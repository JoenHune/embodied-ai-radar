"""Append an audited monthly arXiv cohort; offline and read-only unless --apply.

This is not a collector or a canonical-catalog importer. An analysis cutoff is
not evidence of successful API collection. Existing records are never enriched,
normalized, reordered, or overwritten. Multi-file replacement is per-file atomic,
not a database transaction; finish other writers before using --apply.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SOURCES = ("arxiv", "publications", "arxiv_research_status", "official_groups", "corl")


def encode(value, *, compact=False):
    return (json.dumps(value, ensure_ascii=False, allow_nan=False,
                       separators=(",", ":") if compact else None,
                       indent=None if compact else 2) + "\n").encode()


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def day(value, label):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError(f"{label}: expected YYYY-MM-DD")
    return date.fromisoformat(value)


def instant(value, label):
    if not isinstance(value, str) or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})", value):
        raise ValueError(f"{label}: timezone-aware seconds required")
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def url(value, label):
    if not isinstance(value, str) or urlsplit(value).scheme not in {"http", "https"} or not urlsplit(value).hostname:
        raise ValueError(f"{label}: HTTP(S) URL required")


def validate_record(row, cutoff):
    if not isinstance(row, dict):
        raise ValueError("record must be an object")
    ident = row.get("arxiv_id")
    if not isinstance(ident, str) or not re.fullmatch(r"\d{4}\.\d{4,5}", ident):
        raise ValueError("invalid arxiv_id")
    if row.get("work_id") != "arxiv:" + ident or row.get("preprint_id", "arxiv:" + ident) != "arxiv:" + ident:
        raise ValueError(f"{ident}: work_id/preprint_id mismatch")
    submitted = day(row.get("first_submitted"), f"{ident}.first_submitted")
    if submitted > cutoff or submitted.strftime("%Y-%m") != cutoff.strftime("%Y-%m"):
        raise ValueError(f"{ident}: first submission outside requested month/cutoff")
    if any(not isinstance(row.get(key), str) or not row[key].strip() for key in ("title", "abstract")):
        raise ValueError(f"{ident}: nonempty title and abstract required")
    authors = row.get("authors")
    if not isinstance(authors, list) or not authors or any(not isinstance(a, str) or not a.strip() for a in authors):
        raise ValueError(f"{ident}: nonempty author list required")
    if row.get("authors_complete") is False or (len(authors) >= 25 and row.get("authors_complete") is not True):
        raise ValueError(f"{ident}: author list not verified complete")
    version = row.get("version")
    if not isinstance(version, str) or not re.fullmatch(r"v[1-9]\d*", version):
        raise ValueError(f"{ident}: explicit arXiv version required")
    if row.get("arxiv_version_id", ident + version) != ident + version:
        raise ValueError(f"{ident}: arxiv_version_id mismatch")
    times = {}
    for key in ("submitted_at", "updated_at"):
        precision = row.get(key + "_precision")
        if precision == "day":
            times[key] = day(row.get(key), f"{ident}.{key}")
        elif precision == "second":
            times[key] = instant(row.get(key), f"{ident}.{key}")
        else:
            raise ValueError(f"{ident}.{key}: explicit day/second precision required")
    if "time_of_day_not_exposed" in str(row.get("metadata_temporal_basis", "")) and any(isinstance(v, datetime) for v in times.values()):
        raise ValueError(f"{ident}: seconds claimed for explicitly day-only source")
    days = {key: value.date() if isinstance(value, datetime) else value for key, value in times.items()}
    if days["submitted_at"] != submitted or days["updated_at"] < submitted or days["updated_at"] > cutoff:
        raise ValueError(f"{ident}: inconsistent/future version dates")
    if row.get("updated") is not None and day(row["updated"], f"{ident}.updated") != days["updated_at"]:
        raise ValueError(f"{ident}: updated date differs from version timestamp")
    if all(isinstance(v, datetime) for v in times.values()) and times["updated_at"] < times["submitted_at"]:
        raise ValueError(f"{ident}: reversed version timestamps")
    if version == "v1" and (days["submitted_at"] != days["updated_at"] or
                            (all(isinstance(v, datetime) for v in times.values()) and times["submitted_at"] != times["updated_at"])):
        raise ValueError(f"{ident}: v1 publication/update timestamps disagree")
    observations = row.get("source_observations")
    if not isinstance(observations, list) or not observations:
        raise ValueError(f"{ident}: source observations required")
    observed = []
    for proof in observations:
        if not isinstance(proof, dict):
            raise ValueError(f"{ident}: source observation must be an object")
        url(proof.get("source_url"), f"{ident}.source_url")
        digest = proof.get("raw_sha256", proof.get("sha256"))
        if not isinstance(digest, str) or not re.fullmatch(r"[a-fA-F0-9]{64}", digest):
            raise ValueError(f"{ident}: source SHA-256 required")
        observed.append(instant(proof.get("fetched_at", proof.get("observed_at")), f"{ident}.source observation"))
    for value in times.values():
        if (isinstance(value, datetime) and value > max(observed)) or (not isinstance(value, datetime) and value > max(observed).date()):
            raise ValueError(f"{ident}: version timestamp postdates source observation")
    if not isinstance(row.get("relevance"), dict) or row["relevance"].get("status") not in {"included", "candidate", "manual_review", "excluded"}:
        raise ValueError(f"{ident}: relevance state required; importer does not classify")
    # No transformations: raw text, observation arrays, unknown fields and all
    # relevance states travel byte-for-value into the appended JSON object.
    fingerprint(row)


def merge_records(existing, incoming, cutoff):
    if not isinstance(existing, list) or not isinstance(incoming, list) or not incoming:
        raise ValueError("existing/input must be arrays; empty input cannot establish collection success")
    old = {}
    for row in existing:
        if not isinstance(row, dict) or not row.get("arxiv_id") or row["arxiv_id"] in old:
            raise ValueError("existing corpus contains missing/duplicate arxiv_id")
        old[row["arxiv_id"]] = row
    unique = {}
    for row in incoming:
        validate_record(row, cutoff)
        ident = row["arxiv_id"]
        prior = unique.get(ident, old.get(ident))
        if prior is not None and fingerprint(prior) != fingerprint(row):
            raise ValueError(f"payload conflict for arxiv:{ident}; no existing record overwritten")
        unique[ident] = row
    added = [copy.deepcopy(row) for ident, row in unique.items() if ident not in old]
    return copy.deepcopy(existing) + added, list(unique.values()), [r["arxiv_id"] for r in added]


def compact_html_coverage(coverage):
    core = coverage.get("core_cs_ro", {})
    core_keys = ("advertised_month_list_total", "listed_unique_ids", "listing_pagination_complete",
                 "metadata_complete_for_observed_month_list", "verified_cs_ro_records",
                 "outside_first_submission_window", "unresolved_metadata_count", "scope_limit")
    source = core.get("month_list_source", {})
    core_result = {key: core[key] for key in core_keys if key in core}
    core_result["source"] = {key: source[key] for key in ("url", "sha256", "finished_at", "raw_file") if key in source}
    supplementary = copy.deepcopy(coverage.get("supplementary", {}))
    complete = (core.get("listing_pagination_complete") is True and
                core.get("metadata_complete_for_observed_month_list") is True and
                core.get("advertised_month_list_total") is not None and
                core.get("advertised_month_list_total") == core.get("listed_unique_ids"))
    for key in ("robot_crosslist", "embodied_crosslist"):
        check = supplementary.get(key, {})
        complete = complete and check.get("status") == "ok" and check.get("complete_pagination") is True and (
            check.get("search_advertised_total_before_category_filter") is not None and
            check.get("search_advertised_total_before_category_filter") == check.get("search_unique_ids_before_category_filter"))
    return {"complete_for_observed_html_scope": bool(complete), "core_cs_ro": core_result,
            "supplementary": supplementary, "api_equivalence_verified": False}


def update_source_coverage(previous, arxiv, cutoff):
    result = copy.deepcopy(previous)
    rows, found = [], False
    for old in result.get("sources", []):
        if old.get("source") == "arxiv":
            rows.append(copy.deepcopy(arxiv))
            found = True
        else:
            retained = copy.deepcopy(old)
            # Keep the actual prior status, error, count and check time. This
            # separate field prevents presenting retained health as a new test.
            retained["check_status_this_run"] = "not_checked_this_run"
            retained["rechecked_this_run"] = False
            rows.append(retained)
    if not found:
        rows.append(copy.deepcopy(arxiv))
    present = {r.get("source") for r in rows}
    for name in EXPECTED_SOURCES:
        if name not in present:
            rows.append({"source": name, "status": "not_checked_this_run", "complete": False,
                         "check_status_this_run": "not_checked_this_run", "rechecked_this_run": False,
                         "expected_records": None, "observed_records": None})
    available = [v for v in (result.get("available_data_through"), arxiv["last_observed_data_through"]) if v]
    result.update(schema_version=result.get("schema_version", "1"), requested_source_cutoff=cutoff.isoformat(),
                  analysis_cutoff=cutoff.isoformat(), cutoff_basis="analysis_window_not_collection_completeness",
                  available_data_through=max(available) if available else None,
                  last_observed_arxiv_v1_date=arxiv["last_observed_data_through"],
                  registered_scope_complete=False, primary_corpora_complete=False, status="partial",
                  sources=rows, incomplete_sources=[r["source"] for r in rows],
                  scope_note="HTML fallback coverage, failed API collection and analysis cutoff are separate; other sources were not rechecked.")
    result.setdefault("complete_through", None)
    result.setdefault("primary_corpora_complete_through", None)
    return result


def prepare(root, input_path, coverage_path, cutoff, *, now=None):
    """Return an in-memory plan. No mkdir, caches, network, or writes here."""
    now = now or datetime.now(timezone.utc)
    if not isinstance(cutoff, date) or cutoff > now.astimezone(timezone.utc).date():
        raise ValueError("cutoff cannot be in the future")
    snapshots = {}

    def read(path, default=None):
        path = Path(path)
        raw = path.read_bytes() if path.exists() else None
        snapshots[path] = raw
        if raw is None and default is None:
            raise ValueError(f"required input missing: {path}")
        return json.loads(raw) if raw is not None else copy.deepcopy(default)

    incoming, coverage = read(input_path), read(coverage_path)
    existing_path = root / "data/preprints.json"
    registry_path = root / "config/source-registry.json"
    weekly_path = root / "data/weekly-v3/source-coverage.json"
    audit_path = root / "data/collection-runs" / cutoff.isoformat() / "arxiv.json"
    existing, registry, previous, prior_audit = read(existing_path, []), read(registry_path), read(weekly_path, {}), read(audit_path, {})
    merged, unique, added = merge_records(existing, incoming, cutoff)
    month = cutoff.strftime("%Y-%m")
    window = coverage.get("requested_window", {})
    if coverage.get("month") != month or day(window.get("from"), "coverage.from") != cutoff.replace(day=1) or not cutoff.replace(day=1) <= day(window.get("until"), "coverage.until") <= cutoff:
        raise ValueError("coverage month/window disagrees with requested cutoff")
    if coverage.get("records") != len(unique):
        raise ValueError("coverage count differs from unique input records")
    latest = max(row["first_submitted"] for row in unique)
    if coverage.get("first_submission_day_max") not in (None, latest):
        raise ValueError("coverage latest v1 date differs from input")
    if coverage.get("cohort_status") == "provisional" and any(row.get("period") != "provisional" or row.get("cohort_status") != "provisional" for row in unique):
        raise ValueError("provisional cohort records must remain provisional")
    if day(registry["window"]["until"], "registry.window.until") > cutoff:
        raise ValueError("analysis cutoff regression is not permitted")
    api = {}
    if coverage.get("api_collection_manifest"):
        ref = Path(coverage["api_collection_manifest"])
        api_path = (coverage_path.parent / ref).resolve()
        if ref.is_absolute() or not api_path.is_relative_to(coverage_path.parent.resolve()):
            raise ValueError("API manifest reference must stay within coverage directory")
        api = read(api_path, {})
    statuses = [x.get("original_api_query_status") for x in coverage.get("supplementary", {}).values()]
    api_status = api.get("status") or ("failed" if statuses and all(s == "failed" for s in statuses) else "unknown")
    api_result = {"status": api_status, "complete": api_status == "ok" and api.get("complete_within_registered_query_scope") is True,
                  "expected_records": api.get("corpus_count"), "observed_records": api.get("network_observed_records"),
                  "checks": [{k: row[k] for k in ("query_id", "status", "complete", "advertised_total", "observed_records", "error_type") if k in row} for row in api.get("queries", [])]}
    html = compact_html_coverage(coverage)
    signature = fingerprint({"cohort": unique, "coverage": coverage, "cutoff": cutoff.isoformat(), "api": api_result})
    stamp = now.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    audit = {"schema_version": "1", "run_id": "monthly-arxiv:" + cutoff.isoformat(), "signature": signature,
             "imported_at": stamp, "analysis_cutoff": cutoff.isoformat(),
             "cutoff_basis": "analysis_window_not_API_collection_completeness", "month": month,
             "cohort_status": coverage.get("cohort_status", "unknown"), "cohort_records": len(unique),
             "last_observed_arxiv_v1_date": latest, "source_data_through": None,
             "registered_api_scope_complete": False, "html_fallback": html, "api_collection": api_result,
             "input": {"path": str(input_path), "sha256": hashlib.sha256(snapshots[input_path]).hexdigest()},
             "coverage_input": {"path": str(coverage_path), "sha256": hashlib.sha256(snapshots[coverage_path]).hexdigest()},
             "source_archives_policy": "External raw archives remain in place; record observation URLs/SHA-256 and raw references are preserved.",
             "limitations": coverage.get("coverage_gaps", [])}
    # A replay does not replace the original ingestion receipt or timestamps.
    if prior_audit.get("signature") == signature:
        audit = prior_audit
    arxiv = {"source": "arxiv", "status": "partial", "complete": False,
             "check_status_this_run": "imported_official_html_fallback", "rechecked_this_run": False,
             "imported_at": audit["imported_at"], "checked_at": coverage.get("collection_finished_at"),
             "analysis_cutoff": cutoff.isoformat(), "requested_window": copy.deepcopy(window),
             "source_data_through": None, "last_observed_data_through": latest,
             "observed_records": len(unique), "expected_records": None,
             "html_fallback": html, "api_collection": api_result,
             "collection_run": str(audit_path.relative_to(root))}
    registry = copy.deepcopy(registry)
    registry["window"]["until"] = cutoff.isoformat()
    registry["updated"] = cutoff.isoformat()
    registry["window"]["until_basis"] = "analysis_cutoff_not_collection_completeness"
    registry["analysis_cutoff"] = cutoff.isoformat()
    weekly = update_source_coverage(previous, arxiv, cutoff)
    updates = {}
    if added:
        updates[existing_path] = encode(merged, compact=True)
    # Commit the append before advancing the analysis window or its receipt.
    # An interrupted metadata commit can then be finished by an identical replay.
    updates.update({registry_path: encode(registry), weekly_path: encode(weekly), audit_path: encode(audit)})
    updates = {path: raw for path, raw in updates.items() if raw != snapshots[path]}
    report = {"applied": False, "analysis_cutoff": cutoff.isoformat(), "input_records": len(unique),
              "existing_records": len(existing), "added_records": len(added), "identical_existing_records": len(unique) - len(added),
              "last_observed_arxiv_v1_date": latest, "html_fallback_complete": html["complete_for_observed_html_scope"],
              "api_status": api_status, "registered_api_scope_complete": False,
              "planned_paths": [str(path.relative_to(root)) for path in updates]}
    return {"snapshots": snapshots, "updates": updates, "report": report}


def apply_plan(plan):
    # All conflicts are checked before creating output directories or replacing
    # any file. Recheck each destination too; the caller must serialize writers.
    for path, before in plan["snapshots"].items():
        if (path.read_bytes() if path.exists() else None) != before:
            raise RuntimeError(f"concurrent input/output change: {path}")
    pending = []
    try:
        for path, raw in plan["updates"].items():
            path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".monthly-arxiv-", delete=False) as handle:
                temporary = Path(handle.name)
                pending.append((path, temporary))
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temporary, (path.stat().st_mode & 0o777) if path.exists() else 0o644)
        for path, temporary in pending:
            if (path.read_bytes() if path.exists() else None) != plan["snapshots"][path]:
                raise RuntimeError(f"concurrent destination change: {path}")
            os.replace(temporary, path)
    finally:
        for _, temporary in pending:
            temporary.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--coverage", required=True, type=Path)
    parser.add_argument("--cutoff", required=True)
    parser.add_argument("--apply", action="store_true", help="write the validated four-file append-only plan")
    args = parser.parse_args(argv)
    plan = prepare(ROOT, args.input.resolve(), args.coverage.resolve(), day(args.cutoff, "cutoff"))
    if args.apply:
        apply_plan(plan)
        plan["report"]["applied"] = True
    print(json.dumps(plan["report"], ensure_ascii=False))


if __name__ == "__main__":
    main()
