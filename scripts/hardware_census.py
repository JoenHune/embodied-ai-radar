"""Whole-catalog hardware discovery, explicitly separate from usage evidence.

The census has one row per canonical work, including non-included works.
Title/abstract scans are metadata-only. A dictionary hit is an unverified
mention, including hits in references, simulated models, or a later version.
An empty scan is never evidence that a work did not use hardware.

Source scan contract (append-only records supplied by a collector/caller)::

    {work_id, source_url, observed_at, scope: "body", status: "scanned",
     dictionary_hash, content_hash, matches: [detect_mentions(...) records]}

``content_hash`` is the source observation's ``text_sha256``, not raw bytes.
Only scans matching a current full_text_available/partial_text observation
and the current dictionary are usable. Full-text and partial-text scans are
counted separately. This module never fetches sources or edits authority.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

from catalog_store import encode, fingerprint, load_catalog as _load_catalog, write_if_changed
from equipment_radar import CATEGORIES, FORBIDDEN, SOFTWARE, load_equipment_authority, validate_equipment
from source_review_clock import utc_cutoff, visible, usage_visible


OBSERVATION_STATUSES = {"full_text_available", "partial_text", "unavailable", "blocked", "identity_mismatch"}
FAILED_STATUSES = {"unavailable", "blocked", "identity_mismatch"}
AMBIGUOUS_NAMES = {"panda", "stretch", "spot", "digit", "allegro", "pepper", "fetch", "sawyer", "baxter", "tiago", "nao", "solo"}
LIMITS = [
    "The denominator is every canonical work, regardless of relevance status.",
    "Metadata screening covers title/abstract only; it is not full-text reading or hardware-use verification.",
    "Dictionary mentions are discovery candidates, not verified hardware use, ownership, purchases, or market share.",
    "No dictionary hit, an unavailable body, or no verified relationship never means no hardware was used.",
    "Verified relationships come only from the validated four-table authority; they do not certify whole-paper review.",
    "A version change, reference-list mention, or simulated model cannot create a verified usage relationship.",
    "Full-text scanning is current only for matching source text and dictionary hashes; dictionary coverage is not exhaustive.",
    "Full-text availability/scanning refers to extracted body text, not inspected images, supplements, or completed human review.",
    "source_attempt_count counts source-observation records, including offline cached reparses; it is not an HTTP request count.",
    "Motors, actuators, joint modules, electronics components, and simulation/software tools are outside this dictionary scope.",
]


def _check_works(payload):
    works = payload.get("works")
    if not isinstance(works, list):
        raise ValueError("hardware_census_works_required")
    ids = [work.get("work_id") for work in works]
    if any(not isinstance(wid, str) or not wid for wid in ids) or len(set(ids)) != len(ids):
        raise ValueError("hardware_census_duplicate_or_missing_work_id")
    return works


def load_catalog(root):
    """Load the canonical store without any relevance/status filter."""
    payload, manifest = _load_catalog(Path(root))
    _check_works(payload)
    return payload, manifest


def dictionary_hash(dictionary):
    """Content-address the entire dictionary, including aliases and context."""
    return fingerprint(dictionary)


def _alias_pattern(alias):
    # Separators vary between HTML/PDF extraction and official spellings.
    fragments = re.split(r"[\s_\-‐‑–—]+", alias.strip())
    body = r"[\s_\-‐‑–—]+".join(re.escape(part) for part in fragments)
    return r"(?<![A-Za-z0-9_])" + body + r"(?![A-Za-z0-9_]|[\-‐‑–—][0-9])"


def _out_of_scope(label):
    return bool(FORBIDDEN.search(label) or SOFTWARE.search(label))


@lru_cache(maxsize=8)
def _compile_dictionary(serialized):
    dictionary = json.loads(serialized)
    if str(dictionary.get("schema_version")) != "1" or not isinstance(dictionary.get("entries"), list):
        raise ValueError("hardware_dictionary_schema_invalid")
    compiled, seen = [], set()
    for entry in dictionary["entries"]:
        did = entry.get("dictionary_id")
        if not isinstance(did, str) or not did or did in seen:
            raise ValueError("hardware_dictionary_duplicate_or_missing_id")
        seen.add(did)
        if entry.get("category") not in CATEGORIES:
            raise ValueError("hardware_dictionary_category_invalid:" + did)
        if entry.get("identity_level") not in {"model_specified", "family_only", "unspecified"}:
            raise ValueError("hardware_dictionary_identity_level_invalid:" + did)
        if not isinstance(entry.get("name"), str) or not entry["name"].strip():
            raise ValueError("hardware_dictionary_name_required:" + did)
        aliases, contexts = entry.get("aliases", []), entry.get("context_terms", [])
        if not isinstance(aliases, list) or not isinstance(contexts, list) or any(not isinstance(x, str) for x in [*aliases, *contexts]):
            raise ValueError("hardware_dictionary_alias_or_context_invalid:" + did)
        # Reject out-of-scope entries rather than allowing a harmless alias to
        # turn a software package or motor into a hardware discovery record.
        if _out_of_scope(entry["name"]):
            continue
        context_patterns = [re.compile(_alias_pattern(term), re.I) for term in contexts if term.strip()]
        labels = set()
        for alias in [entry["name"], *aliases]:
            normalized = alias.strip().casefold()
            compact = re.sub(r"[\W_]", "", normalized)
            if not normalized or normalized in labels or len(compact) < 2 or compact.isdigit() or _out_of_scope(alias):
                continue
            labels.add(normalized)
            # Unqualified short model strings (G1, M1, A1, etc.) need an
            # explicit manufacturer/device context from the dictionary.
            ambiguous = len(compact) <= 3 or normalized in AMBIGUOUS_NAMES
            if ambiguous and not context_patterns:
                continue
            # Dictionary context terms are requirements for bare single-token
            # aliases, including longer collisions such as ATLAS/A100/D-Claw.
            # Qualified manufacturer/model phrases remain specific identities;
            # their shorter aliases still require local disambiguation.
            needs_context = ambiguous or (bool(context_patterns) and len(normalized.split()) == 1)
            gate = max(re.split(r"[\s_\-‐‑–—]+", normalized), key=len)
            compiled.append((did, re.compile(_alias_pattern(alias), re.I), needs_context, context_patterns, gate))
    return tuple(compiled)


def _detect(text, compiled, section=None):
    found = []
    lowered = text.casefold()
    for did, pattern, needs_context, context_patterns, gate in compiled:
        if gate not in lowered:
            continue
        for match in pattern.finditer(text):
            start, end = match.span()
            if needs_context:
                # Local context avoids a manufacturer elsewhere in a paper
                # certifying every mathematical G1/M1 occurrence in it.
                local = text[max(0, start - 100):min(len(text), end + 100)]
                if not any(context.search(local) for context in context_patterns):
                    continue
            found.append({"dictionary_id": did, "term": match.group(), "start": start, "end": end,
                          "excerpt": text[max(0, start - 110):min(len(text), end + 110)].strip(),
                          **({"section": section} if section is not None else {})})
    # Long model/family-qualified aliases win when aliases overlap. This also
    # prevents one span from being counted as both e.g. RTX 4090 and 4090.
    owners = defaultdict(set)
    for match in found:
        owners[(match["start"], match["end"])].add(match["dictionary_id"])
    accepted = []
    for match in sorted(found, key=lambda row: (-(row["end"] - row["start"]), row["start"], row["dictionary_id"])):
        # An alias claimed equally by multiple identities is unresolved, not
        # an opportunity to select whichever dictionary ID sorts first.
        if len(owners[(match["start"], match["end"])]) > 1:
            continue
        if any(match["start"] < other["end"] and other["start"] < match["end"] for other in accepted):
            continue
        accepted.append(match)
    return sorted(accepted, key=lambda row: (row["start"], row["end"], row["dictionary_id"]))


def detect_mentions(text, dictionary, section=None):
    """Return bounded, deduplicated mentions only; never infer usage."""
    if not isinstance(text, str):
        raise TypeError("hardware_mention_text_must_be_string")
    return _detect(text, _compile_dictionary(encode(dictionary)), section)


def _alias_resolver(payload):
    aliases = defaultdict(set)
    for work in payload["works"]:
        for alias in [work["work_id"], *work.get("aliases", [])]:
            aliases[alias].add(work["work_id"])
    for row in payload.get("work-aliases", []):
        aliases[row["alias"]].add(row["work_id"])

    def resolve(wid):
        owners = aliases.get(wid, set())
        if len(owners) != 1:
            raise ValueError("hardware_census_unknown_or_ambiguous_work:" + str(wid))
        return next(iter(owners))
    return resolve


def _latest_sources(records, resolve, as_of):
    latest, all_by_work = {}, defaultdict(list)
    for record in records:
        wid = resolve(record.get("work_id"))
        if record.get("status") not in OBSERVATION_STATUSES:
            raise ValueError("hardware_census_source_status_invalid")
        if not record.get("source_url") or not record.get("observed_at"):
            raise ValueError("hardware_census_source_provenance_required")
        if not visible(record["observed_at"], as_of):
            continue
        row = {**record, "work_id": wid}
        all_by_work[wid].append(row)
        key = (wid, record["source_url"])
        previous = latest.get(key)
        # The source ledger is append-only and timestamps have second
        # precision. A later same-second correction/reparse supersedes the
        # earlier row, matching the collector's refresh rule. Hash sorting
        # can otherwise restore a superseded full-text status over partial.
        if previous is None or utc_cutoff(row["observed_at"]) >= utc_cutoff(previous["observed_at"]):
            latest[key] = row
    by_work = defaultdict(list)
    for (wid, _), row in sorted(latest.items()):
        by_work[wid].append(row)
    return by_work, all_by_work


def _scan_matches(scan, entry_ids):
    matches = scan.get("matches", [])
    if not isinstance(matches, list):
        raise ValueError("hardware_census_scan_matches_invalid")
    seen, result = set(), []
    for match in matches:
        if (match.get("dictionary_id") not in entry_ids or not isinstance(match.get("start"), int)
                or not isinstance(match.get("end"), int) or match["start"] < 0 or match["end"] <= match["start"]
                or not isinstance(match.get("term"), str) or not match["term"]
                or ("excerpt" in match and not isinstance(match["excerpt"], str))):
            raise ValueError("hardware_census_scan_match_invalid")
        key = (match["dictionary_id"], match["start"], match["end"], match.get("section"))
        if key not in seen:
            seen.add(key)
            result.append({key: match[key] for key in ("dictionary_id", "term", "start", "end", "excerpt", "section") if key in match})
    return result


def _observation_summary(record):
    fields = ("source_url", "effective_url", "observed_at", "status", "raw_sha256", "text_sha256",
              "version", "cache_ref", "body_characters", "error", "failure_reason", "fetched_at", "processing_basis",
              "observation_id", "parent_observation_id", "parser_version", "transport_verification",
              "transport_complete", "transport_returncode", "transport_truncated", "curl_exit_code")
    return {key: record[key] for key in fields if key in record}


def _counts(rows):
    count = lambda predicate: sum(bool(predicate(row)) for row in rows)
    denominator = len(rows)
    result = {
        "denominator": denominator,
        "metadata_screened_work_count": count(lambda row: row["metadata_scan"]["status"] == "scanned"),
        "metadata_nonempty_abstract_work_count": count(lambda row: "abstract" in row["metadata_scan"]["nonempty_fields"]),
        "metadata_mention_work_count": count(lambda row: row["metadata_scan"]["mention_count"]),
        "body_attempted_work_count": count(lambda row: row["source_attempt_count"]),
        "full_text_available_work_count": count(lambda row: row["body_source_state"] == "full_text_available"),
        "partial_text_available_work_count": count(lambda row: row["body_source_state"] == "partial_text"),
        "full_text_not_attempted_work_count": count(lambda row: row["body_source_state"] == "not_attempted"),
        "full_text_failed_work_count": count(lambda row: row["body_source_state"] in FAILED_STATUSES),
        "full_text_screened_current_dictionary_work_count": count(lambda row: row["full_text_screened_current_dictionary"]),
        "full_text_available_pending_scan_work_count": count(lambda row: row["body_source_state"] == "full_text_available" and not row["full_text_screened_current_dictionary"]),
        "full_text_scanned_no_dictionary_mentions_work_count": count(lambda row: row["full_text_screened_current_dictionary"] and row["full_text_mention_count"] == 0),
        "partial_text_screened_current_dictionary_work_count": count(lambda row: row["partial_text_screened_current_dictionary"]),
        "body_mention_work_count": count(lambda row: row["body_mention_count"]),
        "verified_relationship_work_count": count(lambda row: row["verified_usage_seen"]),
        "verified_usage_relationship_count": sum(row["verified_usage_count"] for row in rows),
        "unverified_work_count": count(lambda row: not row["verified_usage_seen"]),
    }
    for status in sorted(FAILED_STATUSES):
        result["source_" + status + "_work_count"] = count(lambda row: row["body_source_state"] == status)
    result["metadata_missing_abstract_work_count"] = denominator - result["metadata_nonempty_abstract_work_count"]
    # Every rate names both its actual operation and the canonical denominator.
    for field in ("metadata_screened", "full_text_screened_current_dictionary", "verified_relationship"):
        result[field + "_fraction_of_denominator"] = round(result[field + "_work_count"] / denominator, 6) if denominator else None
    return result


def build_census(payload, authority, dictionary, source_scans, source_observations, as_of, *, include_excerpts=False):
    """Build derived coverage without mutating catalog, evidence, or inputs."""
    works = _check_works(payload)
    if not isinstance(as_of, str) or not re.match(r"^\d{4}-\d{2}-\d{2}(?:$|T)", as_of):
        raise ValueError("hardware_census_as_of_required")
    cutoff = utc_cutoff(as_of)
    compiled = _compile_dictionary(encode(dictionary))
    dhash = dictionary_hash(dictionary)
    entries = {row["dictionary_id"]: row for row in dictionary["entries"]}
    validated = validate_equipment(payload, authority)
    verified = defaultdict(list)
    for usage in validated["usage-evidence"]:
        if usage["review_status"] == "verified" and usage["role"] != "mentioned" and usage_visible(usage, cutoff):
            verified[usage["work_id"]].append(usage)
    resolve = _alias_resolver(payload)
    observations, attempts = _latest_sources(source_observations or [], resolve, cutoff)
    scans_by_work = defaultdict(list)
    for scan in source_scans or []:
        wid = resolve(scan.get("work_id"))
        if scan.get("scope") != "body" or scan.get("status") not in {"scanned", "failed"}:
            raise ValueError("hardware_census_scan_scope_or_status_invalid")
        if not all(scan.get(key) for key in ("source_url", "observed_at", "dictionary_hash", "content_hash")):
            raise ValueError("hardware_census_scan_hashes_and_provenance_required")
        if visible(scan["observed_at"], cutoff):
            scans_by_work[wid].append({**scan, "work_id": wid})

    rows, candidates = [], []

    def add_candidate(work_id, mention, kind, **provenance):
        entry = entries[mention["dictionary_id"]]
        mention = {key: value for key, value in mention.items() if include_excerpts or key != "excerpt"}
        row = {"work_id": work_id, "candidate_kind": kind, "evidence_status": "unverified_mention",
               "usage_inference": "none", **mention, "name": entry["name"], "category": entry["category"],
               "identity_level": entry["identity_level"], "dictionary_hash": dhash, **provenance}
        row["candidate_id"] = "hardware-mention:" + fingerprint(row)[:24]
        candidates.append(row)

    for work in sorted(works, key=lambda row: row["work_id"]):
        wid = work["work_id"]
        metadata = {field: work.get(field) or "" for field in ("title", "abstract")}
        if any(not isinstance(value, str) for value in metadata.values()):
            raise ValueError("hardware_census_metadata_must_be_text:" + wid)
        mhash = fingerprint(metadata)
        metadata_matches = []
        for section, text in metadata.items():
            for mention in _detect(text, compiled, section):
                metadata_matches.append(mention)
                add_candidate(wid, mention, "metadata_mention", scope="metadata_only", content_hash=mhash)

        current_sources = observations[wid]
        statuses = {record["status"] for record in current_sources}
        source_state = next((status for status in ("full_text_available", "partial_text", "identity_mismatch", "blocked", "unavailable") if status in statuses), "not_attempted")
        full_scanned, partial_scanned, full_hits, body_hits = False, False, 0, 0
        accepted_scans = []
        for observation in current_sources:
            if observation["status"] not in {"full_text_available", "partial_text"} or not observation.get("text_sha256"):
                continue
            matching = [scan for scan in scans_by_work[wid]
                        if scan["source_url"] == observation["source_url"]
                        and scan["dictionary_hash"] == dhash and scan["content_hash"] == observation["text_sha256"]]
            if not matching:
                continue
            # A later explicit scan failure is visible and cannot be replaced
            # silently by an older success for the same source/text/dictionary.
            # Equal instants (including Z versus .000Z spellings) retain the
            # append-only ledger's later event, just like source observations.
            scan = max(enumerate(matching), key=lambda item: (utc_cutoff(item[1]["observed_at"]), item[0]))[1]
            if scan["status"] != "scanned":
                continue
            mentions = _scan_matches(scan, entries)
            complete = observation["status"] == "full_text_available"
            full_scanned |= complete
            partial_scanned |= not complete
            full_hits += len(mentions) if complete else 0
            body_hits += len(mentions)
            accepted_scans.append({key: scan[key] for key in ("source_url", "observed_at", "scope", "status", "dictionary_hash", "content_hash")})
            accepted_scans[-1].update(source_completeness=observation["status"], mention_count=len(mentions))
            for mention in mentions:
                add_candidate(wid, mention, "body_mention", scope="full_text" if complete else "partial_text",
                              source_url=scan["source_url"], effective_url=observation.get("effective_url", scan["source_url"]),
                              source_observed_at=observation["observed_at"], scanned_at=scan["observed_at"],
                              content_hash=scan["content_hash"], source_version=observation.get("version"))

        if full_scanned:
            scan_state = "current_dictionary_scanned"
        elif source_state == "full_text_available":
            scan_state = "pending_current_dictionary_scan"
        elif partial_scanned:
            scan_state = "partial_text_only_scanned"
        elif source_state == "partial_text":
            scan_state = "partial_text_pending_scan"
        elif source_state in FAILED_STATUSES:
            scan_state = "source_failed"
        else:
            scan_state = "not_attempted"
        precise_date = work.get("first_public_date_precision") in {"day", "month"}
        month = str(work.get("first_public_date", ""))[:7] if precise_date else "unknown"
        if not re.fullmatch(r"\d{4}-\d{2}", month):
            month = "unknown"
        rows.append({
            "work_id": wid, "relevance_status": work.get("relevance", {}).get("status", "unknown"),
            "first_public_month": month, "primary_direction": work.get("primary_direction") or "unassigned",
            "directions": sorted(set(work.get("directions") or [])),
            "metadata_scan": {"scope": "metadata_only", "status": "scanned", "fields": ["title", "abstract"],
                              "nonempty_fields": [field for field, text in metadata.items() if text.strip()],
                              "mention_count": len(metadata_matches), "content_hash": mhash, "dictionary_hash": dhash},
            "source_attempt_count": len(attempts[wid]), "body_source_state": source_state,
            "source_status_counts": dict(sorted(Counter(record["status"] for record in attempts[wid]).items())),
            "source_observations": [_observation_summary(record) for record in current_sources],
            "body_scan_status": scan_state, "body_scan_record_count": len(scans_by_work[wid]),
            "body_scans": accepted_scans, "full_text_screened_current_dictionary": full_scanned,
            "partial_text_screened_current_dictionary": partial_scanned,
            "full_text_mention_count": full_hits, "body_mention_count": body_hits,
            "verified_usage_seen": bool(verified[wid]), "verified_usage_count": len(verified[wid]),
            "verified_usage_ids": sorted(row["usage_id"] for row in verified[wid]),
            "hardware_assessment": "verified_relationship_seen" if verified[wid] else "unverified_mentions_seen" if metadata_matches or body_hits else "not_established",
        })

    # Multiple records for one source cannot inflate candidate occurrences.
    candidates = sorted({row["candidate_id"]: row for row in candidates}.values(), key=lambda row: (row["work_id"], row["candidate_kind"], row.get("source_url", ""), row.get("section", ""), row["start"], row["dictionary_id"]))
    included = [row for row in rows if row["relevance_status"] == "included"]

    def groups(field):
        grouped = defaultdict(list)
        for row in rows:
            grouped[row[field]].append(row)
        return [{field: value, "all_works": _counts(group),
                 "included": _counts([row for row in group if row["relevance_status"] == "included"])}
                for value, group in sorted(grouped.items())]

    summary = {
        "schema_version": "1", "as_of": as_of, "dictionary_version": dictionary.get("version"),
        "dictionary_hash": dhash, "authority_hash": fingerprint(authority),
        "work_set_hash": fingerprint(sorted(row["work_id"] for row in rows)),
        "metadata_scope": "metadata_only", "full_text_scope": "source_text_hash_and_dictionary_hash_matched",
        "source_attempt_count_semantics": "source_observation_records_including_cached_reparse_not_http_requests",
        "all_works": _counts(rows), "included": _counts(included),
        "candidate_occurrence_count": len(candidates),
        "candidate_work_count": len({row["work_id"] for row in candidates}),
        "by_month": groups("first_public_month"), "by_direction": groups("primary_direction"),
        "by_relevance": groups("relevance_status"),
        "direction_grouping": "primary_direction_only_each_work_once; multi-label directions remain on rows",
        "limits": list(LIMITS),
    }
    return {"summary": summary, "rows": rows, "candidates": candidates}


def _read_records(path):
    if path is None:
        return []
    path = Path(path)
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    value = json.loads(path.read_text())
    if not isinstance(value, list):
        raise ValueError("hardware_census_record_list_required:" + str(path))
    return value


def export_census(result, output):
    """Write three derived artifacts; callers must choose a separate output."""
    output = Path(output)
    write_if_changed(output / "summary.json", encode(result["summary"]) + "\n")
    for key, name in (("rows", "coverage.jsonl"), ("candidates", "candidates.jsonl")):
        write_if_changed(output / name, "".join(encode(row) + "\n" for row in result[key]))


def main(argv=None):
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=root / "data/catalog")
    parser.add_argument("--authority", type=Path, default=root / "data/equipment")
    parser.add_argument("--dictionary", type=Path, default=root / "config/hardware-dictionary.json")
    parser.add_argument("--source-scans", type=Path)
    parser.add_argument("--source-observations", type=Path)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--output", type=Path, required=True, help="Separate directory for derived summary/coverage/candidates only")
    args = parser.parse_args(argv)
    output = args.output.resolve()
    for protected in (args.catalog.resolve(), args.authority.resolve(), args.dictionary.resolve().parent):
        if output == protected or output in protected.parents or protected in output.parents:
            parser.error("Output must be separate from canonical catalog, authority, and dictionary directories")
    payload, _ = load_catalog(args.catalog)
    result = build_census(payload, load_equipment_authority(args.authority), json.loads(args.dictionary.read_text()),
                          _read_records(args.source_scans), _read_records(args.source_observations), args.as_of)
    export_census(result, output)
    print(encode({"output": str(output), "dictionary_hash": result["summary"]["dictionary_hash"],
                  "all_works": result["summary"]["all_works"], "included": result["summary"]["included"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
