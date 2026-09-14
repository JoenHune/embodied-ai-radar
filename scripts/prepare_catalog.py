"""One-time identity migration and provenance reconciliation of public source corpora."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from difflib import SequenceMatcher
from collections import defaultdict
from pathlib import Path

from catalog_rules import normalized_title, attribution_valid, publication_verified
from catalog_store import fingerprint
from radar_common import normalize_doi, extract_arxiv_id, classify_research, TAXONOMY

# These report changes to an existing project or organization, not a new work.
OBSERVATION_UPDATE_TYPES = {"strategic_partnership", "research_explainer", "deployment_update", "technology_deployment_update", "code_release"}


def unique(values):
    return list(dict.fromkeys(values))


SOURCE_TABLES = [
    ("works", None), ("preprints", None), ("publications", None),
    ("official-proceedings", None), ("official-programs", None),
    ("papers", None), ("peer-review", "records"), ("group-updates", "updates"),
]


def audit_source_reconciliation(data: Path, sources: list[dict], mappings: list[dict], work_ids: set[str]) -> dict:
    """Prove coverage by the payload identity of every current source row.

    Counting mapping rows alone can pass while one source row is missing and
    another has several historical revisions. This check is deliberately
    independent of the migration's matching and canonical merge heuristics.
    """
    source_index = {row["source_record_id"]: row for row in sources}
    mapping_index = {row["source_record_id"]: row for row in mappings}
    counts, errors = {}, []
    for table, field in SOURCE_TABLES:
        path = data / f"{table}.json"
        if not path.exists():
            continue
        payload = json.loads(path.read_text())
        rows = payload.get(field, []) if field else payload
        counts[table] = len(rows)
        for number, row in enumerate(rows):
            digest = fingerprint(row)
            source_id = f"source:{table}:{digest[:24]}"
            source, mapping = source_index.get(source_id), mapping_index.get(source_id)
            reason = None
            if not source or source.get("payload_hash") != digest:
                reason = "missing_or_changed_source_payload"
            elif not mapping:
                reason = "missing_row_reconciliation"
            elif mapping.get("work_id") not in work_ids and not (
                mapping.get("status") in {"event_only", "manual_review"} and mapping.get("basis")
            ):
                reason = "unexplained_missing_work"
            if reason:
                errors.append({"table": table, "row": number, "source_record_id": source_id, "reason": reason})
    return {"status": "failed" if errors else "ok", "input_counts": counts,
            "checked_rows": sum(counts.values()), "errors": errors}


def canonical_id(row: dict) -> str:
    identifiers = row.get("identifiers") or {}
    doi = normalize_doi(identifiers.get("doi") or row.get("doi"))
    arxiv = extract_arxiv_id(identifiers.get("arxiv") or row.get("arxiv_id") or row.get("arxiv_url") or row.get("id"))
    if doi and not doi.startswith("10.48550/arxiv."):
        return f"doi:{doi}"
    if arxiv:
        return f"arxiv:{arxiv}"
    if str(row.get("work_id", "")).startswith(("report:", "artifact:")):
        return row["work_id"]
    title = normalized_title(row.get("title", ""))
    authors = row.get("authors") or []
    year = str(row.get("first_public_date") or row.get("first_submitted") or row.get("year") or "")[:4]
    key = "|".join([title, normalized_title(authors[0]) if authors else "", year])
    return "title:" + hashlib.sha256(key.encode()).hexdigest()[:24]


def merge_work(target: dict, incoming: dict) -> None:
    for key in ["manifestation_ids", "source_record_ids", "aliases", "authors", "institutions", "repositories", "directions", "questions"]:
        target[key] = unique([*target.get(key, []), *incoming.get(key, [])])
    for key in ["abstract", "summary_zh", "title_zh", "primary_direction"]:
        if not target.get(key) and incoming.get(key):
            target[key] = incoming[key]
    for key, value in (incoming.get("identifiers") or {}).items():
        if value and not target.setdefault("identifiers", {}).get(key):
            target["identifiers"][key] = value
    if incoming.get("first_public_date") and (not target.get("first_public_date") or incoming["first_public_date"] < target["first_public_date"]):
        if incoming.get("first_public_date_precision") in {"day", "month"}:
            target["first_public_date"] = incoming["first_public_date"]
            target["first_public_date_precision"] = incoming["first_public_date_precision"]


def blank_from_source(row: dict, when: str) -> dict:
    result = classify_research(title=row.get("title") or "Untitled public artifact", abstract=row.get("abstract") or "", source_is_robotics=bool(row.get("venue")))
    primary = TAXONOMY["categories"].get(result.get("primary_topic"), {}).get("code")
    directions = [TAXONOMY["categories"][key]["code"] for key in result.get("topics", [])]
    positive = sorted(value for value in result.get("topic_scores", {}).values() if value > 0)
    uncertain = len(positive) > 1 and positive[-1] - positive[-2] <= 1
    status = "manual_review" if uncertain and result["status"] == "included" else result["status"]
    return {
        "work_id": canonical_id(row), "title": row.get("title") or "Untitled public artifact", "title_zh": None,
        "authors": row.get("authors") or [], "institutions": row.get("institutions") or [],
        "abstract": row.get("abstract") or "", "summary_zh": row.get("contribution_zh") or row.get("summary_zh") or "",
        "first_public_date": row.get("first_submitted") or row.get("publication_date") or row.get("published_at"),
        "first_public_date_precision": row.get("date_precision") or "unknown",
        "identifiers": {"arxiv": extract_arxiv_id(row.get("arxiv_id") or row.get("arxiv_url") or row.get("id")), "doi": normalize_doi(row.get("doi"))},
        "relevance": {"status": status, "score": result["score"], "classifier_version": "3.1", "reasons": result.get("reasons", [])},
        "primary_direction": primary, "directions": directions, "questions": [],
        "facets": {"methods": [], "capabilities": [], "embodiments": [], "modalities": []},
        "evidence_flags": {}, "evidence_grade": "E0", "strict_peer_reviewed": False,
        "curated": bool(row.get("curated")), "repositories": [], "manifestation_ids": [],
        "source_record_ids": [], "aliases": [], "updated_at": when,
        "classification_state": "low_confidence_review" if uncertain else "accepted",
    }


def reconcile(payload: dict, data: Path, when: str) -> dict:
    """Every public input row gets a source record and a work mapping or explanation."""
    mappings = {}
    canonical = {}
    for old in sorted(payload["works"], key=lambda row: (not bool(row.get("identifiers", {}).get("arxiv")), row["work_id"])):
        new_id = canonical_id(old)
        mappings[old["work_id"]] = new_id
        work = copy.deepcopy(old)
        work["work_id"] = new_id
        work["aliases"] = unique([old["work_id"], *old.get("aliases", [])])
        if new_id in canonical:
            merge_work(canonical[new_id], work)
        else:
            canonical[new_id] = work
    # Known decoding damage may lose a character; require matching authors and
    # near-identical complete titles before merging, never a title prefix alone.
    title_index = defaultdict(list)
    author_index = defaultdict(list)
    identity_merges = {}
    for wid, work in sorted(canonical.items(), key=lambda item: (0 if item[0].startswith("doi:") else 1 if item[0].startswith("arxiv:") else 2, item[0])):
        title_key = normalized_title(work["title"])
        authors = {normalized_title(a) for a in work.get("authors", [])}
        candidates = list(title_index[title_key])
        if "�" in work["title"] and authors:
            candidates.extend(author_index[next(iter(sorted(authors)))])
        for candidate in unique(candidates):
            other = canonical[candidate]
            other_authors = {normalized_title(a) for a in other.get("authors", [])}
            if not authors & other_authors:
                continue
            a, b = work.get("identifiers", {}), other.get("identifiers", {})
            if any(a.get(key) and b.get(key) and a[key] != b[key] for key in ["arxiv", "doi"]):
                continue
            exact = normalized_title(other["title"]) == title_key
            damaged = "�" in work["title"] and authors == other_authors and SequenceMatcher(None, title_key, normalized_title(other["title"])).ratio() > .98
            if exact or damaged:
                merge_work(other, work)
                identity_merges[wid] = candidate
                payload["work-relations"].append({"relation": "merged_into", "work_id": candidate, "previous_id": wid, "reason": "title_and_authors" if exact else "encoding_repair_with_identical_authors"})
                break
        if wid not in identity_merges:
            title_index[title_key].append(wid)
            if authors:
                author_index[next(iter(sorted(authors)))].append(wid)
    for old, target in mappings.items():
        mappings[old] = identity_merges.get(target, target)
    for wid in identity_merges:
        del canonical[wid]
    for table in ["manifestations", "work-organization-links", "field-provenance", "evidence-events", "work-aliases"]:
        for row in payload.get(table, []):
            if row.get("work_id"):
                row["work_id"] = mappings.get(row["work_id"], row["work_id"])
    for old_id, new_id in mappings.items():
        payload["work-aliases"].append({"alias": old_id, "work_id": new_id, "kind": "migration_identity", "valid_from": None, "valid_to": None})
        if old_id != new_id:
            payload["work-relations"].append({"relation": "supersedes_identifier", "work_id": new_id, "previous_id": old_id, "reason": "canonical_identifier_priority"})

    by_arxiv, by_doi, by_title, by_url = {}, {}, defaultdict(list), {}

    def index(work):
        ids = work.get("identifiers") or {}
        if ids.get("arxiv"):
            by_arxiv[extract_arxiv_id(ids["arxiv"])] = work["work_id"]
        if ids.get("doi"):
            by_doi[normalize_doi(ids["doi"])] = work["work_id"]
        title_key = normalized_title(work["title"])
        if work["work_id"] not in by_title[title_key]:
            by_title[title_key].append(work["work_id"])

    for work in canonical.values():
        index(work)
    for manifestation in payload["manifestations"]:
        if manifestation.get("url"):
            by_url.setdefault(manifestation["url"].rstrip("/"), manifestation["work_id"])
    source_records = []
    reconciliations = []
    provenance = []
    input_counts = {}
    source_tables = SOURCE_TABLES
    authoritative_urls = set()
    manifestation_keys = {(item["work_id"], item.get("url")) for item in payload["manifestations"]}
    for file_name, field in source_tables:
        path = data / f"{file_name}.json"
        content = json.loads(path.read_text()) if path.exists() else []
        rows = content.get(field, []) if field else content
        input_counts[file_name] = len(rows)
        for number, row in enumerate(rows):
            url = row.get("arxiv_url") if file_name in {"preprints", "papers"} else None
            url = url or row.get("official_url") or row.get("url") or next((v.get("url") for v in row.get("versions", []) if v.get("url")), "")
            arxiv = extract_arxiv_id(row.get("arxiv_id") or row.get("arxiv_url") or (row.get("id") if file_name == "papers" else None))
            doi = normalize_doi(row.get("doi"))
            source_id = f"source:{file_name}:{fingerprint(row)[:24]}"
            source_records.append({"source_record_id": source_id, "source_type": file_name,
                                   "url": url, "source_id": row.get("publication_id") or row.get("program_id") or row.get("preprint_id") or row.get("update_id") or row.get("work_id") or str(number),
                                   "payload_hash": fingerprint(row), "title": row.get("title"),
                                   "published_at": row.get("first_submitted") or row.get("publication_date") or row.get("published_at") or row.get("first_public_date"),
                                   "date_precision": row.get("date_precision") or row.get("first_public_date_precision") or "unknown",
                                   "retrieved_at": row.get("fetched_at") or row.get("first_seen_at") or None,
                                   "recorded_at": when, "raw_ref": f"data/{file_name}.json#/{field + '/' if field else ''}{number}"})
            target = by_arxiv.get(arxiv) if arxiv else None
            basis = "arxiv_id" if target else None
            if not target and doi:
                target = by_doi.get(doi)
                basis = "doi" if target else None
            if not target and row.get("work_id"):
                target = mappings.get(row["work_id"])
                basis = "legacy_alias" if target else None
            if not target and url:
                target = by_url.get(url.rstrip("/"))
                # Shared venue indexes are not a work identity.
                if target and not (re.search(r"/(abs|forum|pdf)/?", url) or url.endswith(".html") or file_name == "group-updates"):
                    target = None
                basis = "official_work_url" if target else None
            if not target:
                candidates = by_title.get(normalized_title(row.get("title") or ""), [])
                source_authors = {normalized_title(a) for a in row.get("authors", [])}
                for candidate in candidates:
                    existing = canonical[candidate]
                    if arxiv and existing.get("identifiers", {}).get("arxiv") not in {None, arxiv}:
                        continue
                    matches = source_authors & {normalized_title(a) for a in existing.get("authors", [])}
                    if matches or file_name == "group-updates":
                        target, basis = candidate, "title_and_authors" if matches else "official_title_match"
                        break
            observation = file_name == "group-updates" and row.get("update_type") in OBSERVATION_UPDATE_TYPES
            organizational_event = file_name == "group-updates" and row.get("update_type") in {"personnel_change", "organization_change", "hiring", "funding", "strategic_update", *OBSERVATION_UPDATE_TYPES}
            if not target and not organizational_event:
                new_work = blank_from_source(row, when)
                target = new_work["work_id"]
                canonical.setdefault(target, new_work)
                index(canonical[target])
                basis = "new_public_record"
            reconciliations.append({"source_record_id": source_id, "work_id": target,
                                    "status": "mapped" if target else "event_only", "basis": basis or "organizational_event"})
            if not target:
                continue
            work = canonical[target]
            work["source_record_ids"] = unique([*work.get("source_record_ids", []), source_id])
            if observation:
                # Keep the source-to-existing-work trail, without inventing a
                # publication version or changing its original publication date.
                continue
            if arxiv:
                aliases = work.setdefault("identifier_aliases", {})
                aliases["arxiv"] = unique([*aliases.get("arxiv", []), arxiv])
                by_arxiv[arxiv] = target
            if doi:
                aliases = work.setdefault("identifier_aliases", {})
                aliases["doi"] = unique([*aliases.get("doi", []), doi])
                by_doi[doi] = target
            values = {"title": row.get("title"), "authors": row.get("authors"), "abstract": row.get("abstract"),
                      "first_public_date": row.get("first_submitted") or row.get("publication_date") or row.get("published_at") or row.get("first_public_date")}
            for key, value in values.items():
                if value == work.get(key) and value:
                    provenance.append({"work_id": target, "field": key, "source_record_id": source_id,
                                       "observed_at": row.get("first_seen_at") or None, "basis": "exact_source_value"})
            if file_name in {"official-proceedings", "peer-review"} and url:
                authoritative_urls.add(url)
            if url and (target, url) not in manifestation_keys:
                kind = "preprint" if file_name in {"preprints", "papers"} else row.get("publication_type") or row.get("update_type") or "project"
                kind = {"model_release": "model", "dataset_release": "dataset", "benchmark_release": "benchmark", "repository": "code", "conference_program": "conference"}.get(kind, kind)
                mid = "manifest:" + hashlib.sha256(f"{target}|{kind}|{url}".encode()).hexdigest()[:24]
                manifestation = {"manifestation_id": mid, "work_id": target, "kind": kind, "url": url,
                                 "published_at": values["first_public_date"], "date_precision": row.get("date_precision", "unknown"),
                                 "venue": row.get("venue"), "year": row.get("event_year") or row.get("year"),
                                 "status": row.get("verification_status") or row.get("status") or "discovered",
                                 "peer_reviewed": False, "source_record_id": source_id}
                manifestation["peer_reviewed"] = publication_verified(manifestation, authoritative_urls)
                payload["manifestations"].append(manifestation)
                manifestation_keys.add((target, url))
                work["manifestation_ids"].append(mid)
                by_url.setdefault(url.rstrip("/"), target)
    # Keep migration-only source records for legacy manifestation provenance;
    # actual field claims above point to exact input records, not the first URL.
    sources = {row["source_record_id"]: row for row in payload["source-records"]}
    sources.update({row["source_record_id"]: row for row in source_records})
    payload["source-records"] = list(sources.values())
    payload["field-provenance"] = provenance
    payload["reconciliation"] = reconciliations
    payload["works"] = list(canonical.values())
    payload["input_counts"] = input_counts
    for link in payload["work-organization-links"]:
        if link.get("evidence_grade") == "G2" and not attribution_valid(link, canonical.get(link["work_id"])):
            link["previous_evidence_grade"] = "G2"
            link["evidence_grade"] = "G3"
            link["review_reason"] = "missing_date_bounded_membership_evidence"
    return payload
