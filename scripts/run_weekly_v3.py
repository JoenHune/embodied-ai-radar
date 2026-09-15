#!/usr/bin/env python3
"""Auditable weekly v3 update. Preview is the default; --publish requires main.

Runtime, collection cutoff and report week are distinct. Dry-run never imports
collectors, creates caches/locks, changes data, contacts the network, or commits.
"""
from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import html
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.parse import quote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SHANGHAI = ZoneInfo("Asia/Shanghai")
STAGED_PATHS = [
    "data/catalog", "data/editorial", "data/snapshots", "data/weekly-v3",
    "data/conferences", "data/preprints.json", "data/preprint-coverage.json",
    "data/publications.json", "data/publication-coverage.json",
    "data/group-source-status.json", "data/group-update-candidates.json",
    "data/group-review-queue.json", "data/group-updates.json",
    "data/research-status-additions.jsonl",
    "data/work-organization-links.json", "docs/.vitepress/data/v3-overview.json",
    "docs/organizations", "docs/pulse/weekly",
]
EXPECTED_SOURCES = ("arxiv", "publications", "arxiv_research_status", "official_groups", "corl")


def read_json(path: Path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def write_json(path: Path, value, *, compact: bool = False) -> None:
    content = json.dumps(value, ensure_ascii=False, separators=(",", ":") if compact else None, indent=None if compact else 2) + "\n"
    if path.exists() and path.read_text() == content:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(path.suffix + ".tmp")
    pending.write_text(content)
    pending.replace(path)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def run(command: list[str], env: dict | None = None) -> None:
    print("Running " + " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def week_context(now: datetime) -> dict:
    local = now.astimezone(SHANGHAI)
    end = local.date() - timedelta(days=local.weekday() + 1)
    start = end - timedelta(days=6)
    iso = end.isocalendar()
    return {"week": f"{iso.year}-W{iso.week:02d}", "from": start.isoformat(), "until": end.isoformat(),
            "from_utc": datetime.combine(start, datetime.min.time(), SHANGHAI).astimezone(timezone.utc).isoformat(),
            "until_exclusive_utc": datetime.combine(end + timedelta(days=1), datetime.min.time(), SHANGHAI).astimezone(timezone.utc).isoformat()}


def collection_months(cutoff: date) -> list[str]:
    previous = cutoff.replace(day=1) - timedelta(days=1)
    return [previous.strftime("%Y-%m"), cutoff.strftime("%Y-%m")]


def merge_records(existing: list[dict], incoming: list[dict], key: str) -> list[dict]:
    """Missing/enrichment-empty fields never erase a prior source observation."""
    merged = {row[key]: dict(row) for row in existing if row.get(key)}
    for row in incoming:
        if not row.get(key):
            raise ValueError(f"Source record missing {key}")
        previous = merged.get(row[key], {})
        merged[row[key]] = {**previous, **{name: value for name, value in row.items() if value not in (None, "", [], {})}}
    return sorted(merged.values(), key=lambda row: str(row[key]))


def _query_window(month: str, cutoff: date) -> dict:
    start = date.fromisoformat(month + "-01")
    end = (start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    return {"from": start.isoformat(), "until": min(end, cutoff).isoformat(), "basis": "arxiv_submittedDate_UTC"}


def _last_observed(rows, cutoff: date) -> str | None:
    dates = [str(row.get("first_submitted") or row.get("publication_date") or row.get("published_at") or "")[:10] for row in rows]
    return max((value for value in dates if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) and value <= cutoff.isoformat()), default=None)


def _aggregate_check(source: str, checks: list[dict], *, observed_records=0, requested_window=None) -> dict:
    complete = bool(checks) and all(row.get("complete") is True for row in checks)
    usable = any(row.get("status") in {"ok", "partial"} or row.get("observed_records", 0) for row in checks)
    return {"source": source, "status": "ok" if complete else "partial" if usable else "failed", "complete": complete,
            "requested_window": requested_window, "checks": checks, "observed_records": observed_records,
            "completed_checks": sum(row.get("complete") is True for row in checks), "expected_checks": len(checks),
            "coverage_basis": "registered_source_query_scope_not_global_research_completeness"}


def collect_arxiv(cutoff: date, now: datetime | None = None) -> dict:
    collector = importlib.import_module("collect_arxiv_v2")
    now = now or datetime.now(timezone.utc)
    base = getattr(collector, "_weekly_raw_root", collector.RAW)
    collector._weekly_raw_root = base
    collector.RAW = base / "weekly" / now.strftime("%Y%m%dT%H%M%S%fZ")
    collector.RAW.mkdir(parents=True, exist_ok=True)
    collector.REGISTRY["window"]["until"] = cutoff.isoformat()
    incoming, checks = {}, []
    for month in collection_months(cutoff):
        for query in collector.REGISTRY["arxiv_sources"]["queries"]:
            # Observe each page's advertised total ourselves: a short/empty
            # feed or a later failed page must not look like a complete query.
            batch, total, offset, error_type = [], None, 0, None
            try:
                while total is None or offset < total:
                    body = collector.fetch(query["id"], query["query"], month, offset, 500)
                    expected, page = collector.parse_feed(body)
                    if total is not None and expected != total:
                        error_type = "ResultTotalChangedDuringPagination"
                    total = expected
                    batch.extend(page)
                    if not page:
                        break
                    offset += len(page)
            except Exception as error:
                error_type = type(error).__name__
            complete = total is not None and len(batch) >= total and error_type is None
            checks.append({"source_id": "arxiv:" + query["id"] + ":" + month, "query_id": query["id"],
                           "requested_window": _query_window(month, cutoff), "status": "ok" if complete else "partial" if batch else "failed",
                           "complete": complete, "expected_records": total, "observed_records": len(batch),
                           "last_observed_data_through": _last_observed(batch, cutoff),
                           "error_type": error_type or (None if complete else "IncompletePagination")})
            for record in batch:
                incoming[record["arxiv_id"]] = collector.merge_record(incoming.get(record["arxiv_id"], {}), record, query["id"])
    collector.classify(list(incoming.values()))
    rows = merge_records(read_json(collector.OUTPUT, []), list(incoming.values()), "arxiv_id")
    write_json(collector.OUTPUT, rows, compact=True)
    write_json(collector.COVERAGE, collector.summarize(rows))
    result = _aggregate_check("arxiv", checks, observed_records=len(incoming), requested_window={"from": collection_months(cutoff)[0] + "-01", "until": cutoff.isoformat()})
    return {**result, "source_data_through": cutoff.isoformat() if result["complete"] else None,
            "last_observed_data_through": _last_observed(list(incoming.values()), cutoff), "stored_records": len(rows)}


def _publication_pages(collector, spec: dict, cutoff: date) -> list[dict]:
    """Collector return success is not proof that all advertised rows arrived."""
    if "dblp_stream" in spec:
        paths = [(collector.RAW / f"dblp-{spec['venue'].lower()}-{year}.json", "hits", {"year": year, "basis": "dblp_venue_year_index"}) for year in spec["years"]]
    else:
        paths = [(collector.RAW / f"crossref-{spec['venue'].lower().replace(' ', '-')}-through-{cutoff.isoformat()}.json", "items", dict(collector.REGISTRY["window"], basis="crossref_publication_date"))]
    checks = []
    for path, key, window in paths:
        raw = read_json(path, {})
        total, fetched = raw.get("expected_total"), len(raw.get(key, []))
        complete = isinstance(total, int) and total >= 0 and fetched >= total and raw.get("complete") is not False
        checks.append({"requested_window": window, "expected_records": total, "observed_records": fetched, "complete": complete,
                       "status": "ok" if complete else "partial" if fetched else "failed",
                       "error_type": None if complete else "IncompleteOrUnverifiedPagination"})
    return checks


def collect_publications(cutoff: date, now: datetime) -> dict:
    collector = importlib.import_module("collect_publications")
    collector.REGISTRY["window"] = {"from": (cutoff - timedelta(days=45)).isoformat(), "until": cutoff.isoformat()}
    # DBLP caches are intentionally fresh per run date, so a previous complete
    # yearly page cannot hide newly indexed papers. Crossref uses a 45-day overlap.
    base = getattr(collector, "_weekly_raw_root", collector.RAW)
    collector._weekly_raw_root = base
    collector.RAW = base / "weekly" / now.strftime("%Y%m%dT%H%M%S%fZ")
    collector.RAW.mkdir(parents=True, exist_ok=True)
    incoming, checks = [], []
    for source in collector.REGISTRY["conference_sources"] + collector.REGISTRY["journal_sources"]:
        try:
            if "dblp_stream" in source:
                spec = {**source, "years": [year for year in source["years"] if cutoff.year - 1 <= year <= cutoff.year]}
                batch = collector.collect_dblp(spec)
            else:
                spec = dict(source)
                batch = collector.collect_crossref(spec)
            incoming.extend(batch)
            pages = _publication_pages(collector, spec, cutoff)
            checked = _aggregate_check(source["venue"], pages, observed_records=len(batch), requested_window={"years": spec["years"]} if "dblp_stream" in spec else dict(collector.REGISTRY["window"]))
            checks.append({**checked, "source_id": "publication:" + source["venue"], "source_data_through": cutoff.isoformat() if checked["complete"] else None,
                           "last_observed_data_through": _last_observed(batch, cutoff)})
        except Exception as error:
            checks.append({"source": source["venue"], "source_id": "publication:" + source["venue"], "status": "failed", "complete": False,
                           "requested_window": {"years": source["years"]} if "dblp_stream" in source else dict(collector.REGISTRY["window"]), "error_type": type(error).__name__})
    result = _aggregate_check("publications", checks, observed_records=len(incoming), requested_window={"from": (cutoff - timedelta(days=45)).isoformat(), "until": cutoff.isoformat()})
    if not incoming and not any(row["status"] == "ok" for row in checks):
        return result
    rows = merge_records(read_json(collector.OUTPUT, []), collector.deduplicate(incoming), "publication_id")
    # Classify against the full source window, not only the discovery overlap.
    collector.REGISTRY = read_json(ROOT / "config/source-registry.json")
    collector.REGISTRY["window"]["until"] = cutoff.isoformat()
    collector.apply_classification(rows)
    write_json(collector.OUTPUT, rows, compact=True)
    write_json(collector.SUMMARY, collector.summarize(rows, "weekly-incremental"))
    return {**result, "source_data_through": cutoff.isoformat() if result["complete"] else None,
            "last_observed_data_through": _last_observed(incoming, cutoff)}


def research_status_baseline(preprints: list[dict], previous_updates: list[dict]) -> list[dict]:
    """Merge pre-collection metadata with watch receipts, including empty comments.

    Unlike general merge_records, an explicit empty comment/hash and a cleared
    pending flag are meaningful. Older receipts cannot downgrade a newer version.
    """
    from research_status_watch import _metadata
    result = {}
    receipt_ids = {_metadata(row).get("arxiv_id") for row in previous_updates}
    for checkpoint, rows in ((False, preprints), (True, previous_updates)):
        for original in rows:
            row = _metadata(original)
            key = row.get("arxiv_id")
            if not key:
                continue
            previous = result.get(key, {})
            merged = {**previous, **{field: value for field, value in row.items() if value is not None}}
            if row.get("comment_sha256") is None and previous:
                merged["status_comment_hint"] = previous.get("status_comment_hint", False)
            rank = lambda value: (int((value.get("latest_version") or "v0")[1:]), str(value.get("updated_at") or ""))
            if previous and rank(merged) < rank(previous):
                # A newer ordinary collection is not proof that its status
                # page was checked: the older watch receipt cannot clear it.
                merged = {**previous, "status_check_pending": True}
            elif not checkpoint or "status_check_pending" not in original:
                merged["status_check_pending"] = previous.get("status_check_pending", False) or row.get("status_check_pending", False)
            result[key] = merged
    for key, row in result.items():
        if key not in receipt_ids:
            row["status_check_pending"] = True
    return [result[key] for key in sorted(result)]


def _status_file(relative: str) -> Path:
    path = ROOT / relative
    if path.is_symlink() or not path.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("Status audit path escapes the workspace")
    return path


def _write_status_text(relative: str, content: str, *, immutable=False) -> None:
    path = _status_file(relative)
    if path.exists():
        if path.read_text() == content:
            return
        if immutable:
            raise ValueError("Status audit run identity conflict")
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(path.suffix + ".tmp")
    pending.write_text(content)
    pending.replace(path)


def _stage_status_candidates(candidates: list[dict], works: list[dict]) -> tuple[list[dict], list[dict]]:
    """Never overwrite the first staging source or a conflicting notice ID."""
    from catalog_store import read_table
    from ingest_research_status import apply_research_status_additions
    from research_status_watch import _notice_version, _date_key
    relative = "data/research-status-additions.jsonl"
    path = _status_file(relative)
    original = path.read_text() if path.exists() else ""
    existing = [json.loads(line) for line in original.splitlines() if line.strip()]
    accepted, reviews = [], []
    authority = None
    for candidate in candidates:
        same_id = [row for row in existing if row.get("notice_id") == candidate.get("notice_id")]
        same_version = [row for row in existing if _notice_version(row) == _notice_version(candidate) and _notice_version(row)[0]]
        conflicts = [row for row in same_id + same_version if row.get("event_type") != candidate.get("event_type") or _date_key(row) != _date_key(candidate)]
        # Source IDs may differ for a later observation, but reusing a notice
        # ID to rewrite its own description/scope is an explicit review item.
        same_id_changed = any(any(row.get(field) != candidate.get(field) for field in ("scope", "review_status", "summary_zh")) for row in same_id)
        if conflicts or same_id_changed or any(_notice_version(row) != _notice_version(candidate) for row in same_id):
            reviews.append({"error_code": "status_staging_identity_state_or_date_conflict", "notice_id": candidate.get("notice_id"),
                            "existing_notice_ids": list(dict.fromkeys(row.get("notice_id") for row in same_id + same_version)), "observed_notice": copy.deepcopy(candidate)})
            continue
        if same_id or same_version:
            # The observed source remains in the separate run observation, not
            # substituted into a manual or already imported logical notice.
            continue
        if authority is None:
            authority = {name: read_table(ROOT / "data/catalog", name) for name in
                         ("work-aliases", "source-records", "manifestations", "evidence-events", "field-provenance")}
            authority["works"] = works
        try:
            authority = apply_research_status_additions(authority, [candidate])
        except (ValueError, TypeError, KeyError):
            reviews.append({"error_code": "status_candidate_preflight_failed", "notice_id": candidate.get("notice_id"), "observed_notice": copy.deepcopy(candidate)})
            continue
        accepted.append(copy.deepcopy(candidate))
        existing.append(candidate)
    if accepted:
        if (path.read_text() if path.exists() else "") != original:
            raise ValueError("Status staging changed during preflight")
        content = original + ("\n" if original and not original.endswith("\n") else "")
        content += "".join(json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n" for row in accepted)
        _write_status_text(relative, content)
    return accepted, reviews


def collect_research_status(cutoff: date, now: datetime, baseline: list[dict], *, metadata_fetcher=None, status_fetcher=None, sleeper=None) -> dict:
    """Persist independent status checks. None of their clocks advances corpus coverage."""
    from catalog_store import read_table
    from research_status_watch import watch_research_status
    context = week_context(now)
    folder = "data/weekly-v3/research-status"
    state = read_json(ROOT / folder / "baseline.json", {})
    works = read_table(ROOT / "data/catalog", "works")
    kwargs = {"metadata_fetcher": metadata_fetcher, "status_fetcher": status_fetcher}
    if sleeper is not None:
        kwargs["sleeper"] = sleeper
    result = watch_research_status(works, baseline, **kwargs)
    accepted, stage_reviews = _stage_status_candidates(result["notice_candidates"], works)
    result["review_queue"].extend(stage_reviews)
    if stage_reviews:
        result["coverage"]["status"] = "partial"
        conflicted = {row.get("observed_notice", {}).get("source_record", {}).get("raw", {}).get("work_identifiers", {}).get("arxiv") for row in stage_reviews}
        for row in result["metadata_updates"]:
            if row.get("arxiv_id") in conflicted:
                row["status_check_pending"] = True
    complete = result["coverage"]["status"] == "complete"
    previous = state.get("source_check", {})
    failures = 0 if complete else int(previous.get("consecutive_failures", 0)) + 1
    last_success = result["checked_at"] if complete else previous.get("last_success")
    checks = [{"source_id": "arxiv-status:batch:" + hashlib.sha256(",".join(row["requested_ids"]).encode()).hexdigest()[:16],
               "status": "ok" if row["status"] == "complete" else row["status"], "complete": row["status"] == "complete",
               "expected_records": len(row["requested_ids"]), "observed_records": len(row["returned_ids"]), "missing_records": len(row["missing_ids"])}
              for row in result["coverage"]["metadata_batches"]]
    pages = result["coverage"]["status_pages"]
    if pages["requested"]:
        checks.append({"source_id": "arxiv-status:version-pages", "status": "ok" if not pages["failed"] and not pages["review_required"] else "partial",
                       "complete": not pages["failed"] and not pages["review_required"] and not stage_reviews,
                       "expected_records": pages["requested"], "observed_records": pages["completed"], "review_required": pages["review_required"] + len(stage_reviews)})
    summary = {"source": "arxiv_research_status", "status": "ok" if complete else "partial" if result["coverage"]["returned_count"] else "failed",
               "complete": complete, "checked_at": result["checked_at"], "source_data_through": None,
               "requested_window": {"basis": "latest_metadata_all_registered_arxiv_ids", "first_submission_month_filter": False},
               "expected_records": result["coverage"]["requested_count"], "observed_records": result["coverage"]["returned_count"],
               "missing_records": result["coverage"]["missing_count"], "current_review_count": len(result["review_queue"]),
               "notice_candidates_staged": len(accepted), "status_pages": pages, "checks": checks,
               "expected_checks": len(checks), "completed_checks": sum(row["complete"] for row in checks),
               "consecutive_failures": failures, "failure_basis": "incomplete_status_coverage_not_necessarily_transport_failure",
               "last_success": last_success, "report_path": f"{folder}/{context['week']}/snapshot.json"}
    run_id = now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_folder = f"{folder}/{context['week']}/{run_id}"
    records = {
        run_folder + "/observations.jsonl": "".join(json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n" for row in result["observations"]),
        run_folder + "/check.json": json.dumps({"week": context["week"], "run_id": run_id, "requested_source_cutoff": cutoff.isoformat(),
            "coverage": result["coverage"], "source_check": summary, "staged_notice_ids": [row["notice_id"] for row in accepted]}, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n",
        run_folder + "/review-queue.json": json.dumps(result["review_queue"], ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n",
    }
    for relative, body in records.items():
        target = _status_file(relative)
        if target.exists() and target.read_text() != body:
            raise ValueError("Status run already exists with different content")
    for relative, body in records.items():
        _write_status_text(relative, body, immutable=True)
    week_path = f"{folder}/{context['week']}/snapshot.json"
    old_week = read_json(ROOT / week_path, {})
    week = {"schema_version": "1", "week": context["week"], "run_ids": list(dict.fromkeys([*old_week.get("run_ids", []), run_id])),
            "latest_run_id": run_id, "latest_source_check": summary, "observation_scope": "run_audit_not_research_revision"}
    baseline_updates = research_status_baseline([], [*state.get("metadata_updates", []), *result["metadata_updates"]])
    for relative, value in [(week_path, week), (folder + "/baseline.json", {"schema_version": "1", "source_check": summary, "metadata_updates": baseline_updates})]:
        _write_status_text(relative, json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n")
    owned_paths = [*records, week_path, folder + "/baseline.json"]
    summary["_status_audit_hashes"] = {relative: hashlib.sha256(_status_file(relative).read_bytes()).hexdigest() for relative in owned_paths}
    return summary


def collect_sources(cutoff: date, now: datetime, *, status_metadata_fetcher=None, status_fetcher=None, status_sleeper=None) -> list[dict]:
    # Capture BEFORE collect_arxiv rewrites preprints; its fresh metadata must
    # never become the comparison baseline for this same status-watch run.
    try:
        prior = read_json(ROOT / "data/weekly-v3/research-status/baseline.json", {})
        status_baseline = research_status_baseline(read_json(ROOT / "data/preprints.json", []), prior.get("metadata_updates", []))
        baseline_error = None
    except Exception as error:
        status_baseline, baseline_error = [], type(error).__name__
    def status_check():
        if baseline_error:
            return {"source": "arxiv_research_status", "status": "failed", "complete": False, "source_data_through": None,
                    "error_type": "PrecollectionBaselineUnavailable", "checked_at": now.isoformat()}
        return collect_research_status(cutoff, now, status_baseline, metadata_fetcher=status_metadata_fetcher, status_fetcher=status_fetcher, sleeper=status_sleeper)
    checks = []
    for name, callback in [("arxiv", lambda: collect_arxiv(cutoff, now)), ("arxiv_research_status", status_check), ("publications", lambda: collect_publications(cutoff, now))]:
        try:
            checks.append({"source": name, **callback(), "checked_at": datetime.now(timezone.utc).isoformat()})
        except Exception as error:
            checks.append({"source": name, "status": "failed", "complete": False, "requested_window": {"until": cutoff.isoformat()}, "error_type": type(error).__name__})
    # Source availability is a recorded observation; a blocked conference does
    # not delete its previously verified snapshot or fabricate a zero count.
    for name, command in [
        ("official_groups", [sys.executable, "scripts/collect_group_sources.py", "--as-of", now.astimezone(SHANGHAI).date().isoformat()]),
        ("corl", [sys.executable, "scripts/collect_corl_openreview.py", "--edition", "corl-2026"]),
    ]:
        try:
            run(command)
            checks.append(read_collector_check(name, now))
        except subprocess.CalledProcessError:
            checks.append({"source": name, "status": "failed", "complete": False, "checked_at": now.isoformat(), "error_type": "CollectorProcessFailed"})
    run([sys.executable, "scripts/resolve_organizations.py"])
    return checks


def read_collector_check(name: str, now: datetime) -> dict:
    """A zero exit code reports process health, not source completeness."""
    def current(value):
        try:
            observed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return observed.tzinfo is not None and observed >= now
        except ValueError:
            return False
    if name == "corl":
        raw = read_json(ROOT / "data/conferences/corl-2026/source-status.json", {})
        observed = str(raw.get("checked_at") or "")
        fresh = current(observed)
        complete = raw.get("complete") is True and fresh
        return {"source": name, "status": "ok" if complete else "partial" if raw.get("records_retained") else "failed",
                "complete": complete, "checked_at": raw.get("checked_at"), "status_record_current_run": fresh,
                "source_status": raw.get("status", "unverified"), "expected_records": raw.get("expected_count"),
                "observed_records": raw.get("fetched_count", 0), "retained_records": raw.get("records_retained", 0),
                "requested_window": {"edition": "corl-2026", "basis": "official_accepted_venue_snapshot"},
                "error_type": None if complete else "IncompleteOfficialConferenceSnapshot"}
    rows = list(read_json(ROOT / "data/group-source-status.json", {}).get("sources", []))
    # Count registered-but-never-checked T0/T1 channels too. Looking only at
    # successful status rows would make newly added or unsupported sources
    # disappear from the denominator and falsely report complete coverage.
    from catalog_store import read_table
    registered = read_table(ROOT / "data/catalog", "organizations")
    present = {(row.get("organization_id"), row.get("kind"), row.get("url")) for row in rows}
    for org in registered:
        if org.get("tier") not in {"T0", "T1"}:
            continue
        for kind, url in (org.get("official_urls") or {}).items():
            if not isinstance(url, str) or urlsplit(url).scheme not in {"http", "https"} or (org["organization_id"], kind, url) in present:
                continue
            rows.append({"source_id": "registered:" + hashlib.sha256(f"{org['organization_id']}|{kind}|{url}".encode()).hexdigest()[:16],
                         "organization_id": org["organization_id"], "kind": kind, "url": url, "status": "unverified", "last_checked": None})
    checks = []
    for row in rows:
        observed = str(row.get("last_checked") or "")
        fresh = current(observed)
        complete = fresh and row.get("status") == "healthy" and not row.get("consecutive_failures") and row.get("parser_status") != "partial"
        checks.append({"source_id": row.get("source_id"), "organization_id": row.get("organization_id"), "url": row.get("url"),
                       "status": "ok" if complete else "partial" if fresh and row.get("status") == "partial" else "failed" if fresh else "not_checked_this_run",
                       "source_status": row.get("status", "unverified"), "complete": complete, "checked_at": row.get("last_checked"),
                       "consecutive_failures": row.get("consecutive_failures", 0), "requested_window": {"basis": "official_page_snapshot"},
                       "parser_status": row.get("parser_status"), "last_success": row.get("last_success")})
    return {**_aggregate_check(name, checks, requested_window={"as_of": now.astimezone(SHANGHAI).date().isoformat(), "basis": "registered_official_pages"}), "checked_at": now.isoformat()}


def collection_coverage(checks: list[dict], cutoff: date, prior_data_through: str | None, previous: dict | None = None) -> dict:
    """Availability != completeness. A partial source never advances the latter.

    available_data_through is the analysis cutoff for retained/new usable data;
    it is NOT a claim that every source was checked through that day. The
    separate registered_scope_complete flag applies only to registered queries,
    venue streams and pages. Earlier completeness is retained only if explicit.
    """
    previous = previous or {}
    checks = [{key: copy.deepcopy(value) for key, value in row.items() if not key.startswith("_status_")} for row in checks]
    old_checks = {row["source"]: row for row in previous.get("sources", [])}
    for row in checks:
        if row["source"] == "arxiv_research_status" and "consecutive_failures" not in row:
            row["consecutive_failures"] = 0 if row.get("complete") is True else int(old_checks.get(row["source"], {}).get("consecutive_failures", 0)) + 1
    by_source = {row["source"]: row for row in checks}
    primary = [by_source.get(name, {"source": name, "status": "not_checked", "complete": False}) for name in ("arxiv", "publications")]
    available = [prior_data_through] if prior_data_through else []
    for row in primary:
        if row.get("complete") is True:
            available.append(cutoff.isoformat())
        elif row.get("last_observed_data_through"):
            available.append(min(row["last_observed_data_through"], cutoff.isoformat()))
    all_expected = EXPECTED_SOURCES
    complete = all(name in by_source and by_source[name].get("complete") is True for name in all_expected)
    corpus_complete = all(row.get("complete") is True for row in primary)
    return {"schema_version": "1", "requested_source_cutoff": cutoff.isoformat(), "available_data_through": max(available) if available else None,
            "registered_scope_complete": complete, "primary_corpora_complete": corpus_complete,
            "complete_through": max(filter(None, [cutoff.isoformat(), previous.get("complete_through")])) if complete else previous.get("complete_through"),
            "primary_corpora_complete_through": max(filter(None, [cutoff.isoformat(), previous.get("primary_corpora_complete_through")])) if corpus_complete else previous.get("primary_corpora_complete_through"),
            "status": "complete" if complete else "partial" if any(r.get("status") in {"ok", "partial"} for r in checks) else "failed",
            "incomplete_sources": [name for name in all_expected if name not in by_source or by_source[name].get("complete") is not True],
            "sources": copy.deepcopy(checks), "scope_note": "完成仅指已登记查询/会议期刊流/官方页面；不代表全互联网覆盖。可用数据截止日不代表所有来源完整或新鲜。"}


VOLATILE_FIELDS = {"generated_at", "run_at", "retrieved_at", "observed_at", "checked_at", "last_checked", "last_success", "updated_at",
                   "ingested_at", "input_digest", "payload_hash", "catalog_hash", "dataset_version", "editorial_hash", "_managed_field_hashes",
                   "source_health", "last_failure_date", "attempts", "failure", "byte_count", "raw_ref"}


def semantic_value(value):
    if isinstance(value, dict):
        return {key: semantic_value(item) for key, item in sorted(value.items()) if key not in VOLATILE_FIELDS and not key.startswith("_")}
    if isinstance(value, list):
        return [semantic_value(item) for item in value]
    return value


def content_hash(value) -> str:
    return hashlib.sha256(json.dumps(semantic_value(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def research_state() -> dict:
    from catalog_store import read_table
    tables = ["works", "manifestations", "organizations", "work-organization-links", "work-aliases", "evidence-events", "editorial-claims", "work-relations", "taxonomy-assignments", "text-snapshots", "report-text-snapshots", "source-records", "field-provenance"]
    catalog = {name: read_table(ROOT / "data/catalog", name) for name in tables}
    # Opaque source payload hashes and source locators are evidence, not fetch
    # clocks. Preserve them even where managed-work metadata uses the same key
    # for volatile bookkeeping. Unknown hash changes fail conservatively into
    # an evidence revision rather than silently discarding the new observation.
    for table in ("source-records", "field-provenance"):
        catalog[table] = [{**row, **{("source_evidence_" + key): row[key] for key in ("payload_hash", "raw_ref", "updated_at") if key in row}}
                          for row in catalog[table]]
    # Repeated observations of the identical field/source binding remain in
    # the authoritative ledger, but capture-clock duplicates are one semantic
    # provenance fact for research revision comparison.
    provenance = {json.dumps(semantic_value(row), ensure_ascii=False, sort_keys=True, separators=(",", ":")): semantic_value(row)
                  for row in catalog["field-provenance"]}
    catalog["field-provenance"] = [provenance[key] for key in sorted(provenance)]
    # source-health and organizations.source_health belong to the operational
    # coverage channel, not the research revision. Their complete records and
    # actual check times are retained on disk/in metadata commits, never reset.
    # For an undated observation, first discovery is the timeline evidence, not
    # a disposable fetch clock. first_seen_at is always retained as well.
    catalog["evidence-events"] = [{**row, "first_observation_at": row.get("first_seen_at") or row.get("observed_at")}
        if not row.get("published_at") or row.get("date_precision") in {"unknown", "month", "year"} else row for row in catalog["evidence-events"]]
    editorial = {}
    for path in sorted((ROOT / "data/editorial").rglob("*")):
        if not path.is_file() or path.name.endswith(".attempt.json") or path.name == "status.json" or path.suffix not in {".json", ".jsonl"}:
            continue
        editorial[str(path.relative_to(ROOT / "data/editorial"))] = read_json(path) if path.suffix == ".json" else [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    manifest = read_json(ROOT / "docs/public/api/v1/catalog-manifest.json", {})
    calendar = {key: manifest.get(key) for key in ["complete_months", "provisional_month", "available_months"]}
    return {"catalog": catalog, "editorial": editorial, "calendar": calendar}


def planned_generated_paths(context: dict) -> list[str]:
    """Exact output manifest prepared BEFORE running collectors/builders.

    No review additions, config, README, arbitrary new files or manual signal
    reviews are cleanup targets. Unknown outputs are left for diagnosis.
    """
    from catalog_store import TABLES, read_table, table_output_paths
    paths = {path for path in STAGED_PATHS if path.endswith(".json")}
    paths.update(str(path.relative_to(ROOT)) for name in TABLES
                 for path in table_output_paths(ROOT / "data/catalog", name))
    paths.update(["data/catalog/manifest.json", "data/catalog/migration-report.json", "data/editorial/status.json", "data/editorial/work-localizations.jsonl"])
    manifest = read_json(ROOT / "docs/public/api/v1/catalog-manifest.json", {})
    months = {value for value in [*manifest.get("available_months", []), *manifest.get("complete_months", []), manifest.get("provisional_month")] if value and re.fullmatch(r"20\d{2}-\d{2}", value)}
    for month in months:
        paths.update([f"data/editorial/monthly/{month}.json", f"data/editorial/monthly/{month}.attempt.json", f"data/editorial/legacy/{month}.json"])
        history_path = f"data/snapshots/monthly/{month}/history.json"
        history = read_json(ROOT / history_path, [])
        paths.add(history_path)
        paths.update(f"data/snapshots/monthly/{month}/r{revision}.json" for revision in range(1, len(history) + 2))
    paths.update("data/editorial/legacy/" + name for name in ["work-notes.jsonl", "context.json", "reconciliation.json", "manifest.json", "content-audit.md"])
    paths.update("data/conferences/corl-2026/" + name for name in ["source-status.json", "records.jsonl", "group-metadata.json", "validation-rejections.json"])
    for org in read_table(ROOT / "data/catalog", "organizations"):
        if re.fullmatch(r"[a-z0-9][a-z0-9-]*", org.get("slug", "")):
            paths.add("docs/organizations/" + org["slug"] + ".md")
    paths.update([f"data/weekly-v3/{context['week']}.json", "data/weekly-v3/source-coverage.json", f"docs/pulse/weekly/{context['week'].lower()}.md", "docs/pulse/weekly/index.md"])
    return sorted(paths)


def checkpoint_generated(paths: list[str], backup: Path) -> dict:
    before = {}
    for relative in paths:
        source = ROOT / relative
        if not source.resolve().is_relative_to(ROOT.resolve()) or source.is_symlink():
            raise ValueError("Generated checkpoint path escapes the workspace")
        if source.is_file():
            target = backup / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            before[relative] = hashlib.sha256(source.read_bytes()).hexdigest()
        else:
            before[relative] = None
    return {"backup": backup, "files": before}


def generated_hashes(checkpoint: dict) -> dict:
    return {relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() if (ROOT / relative).is_file() else None for relative in checkpoint["files"]}


def restore_generated(checkpoint: dict, expected_after: dict) -> list[str]:
    """Restore only this run's exact planned outputs, never a broad glob."""
    current = generated_hashes(checkpoint)
    if current != expected_after:
        raise RuntimeError("Generated files changed after verification; refusing to overwrite concurrent edits")
    restored = []
    for relative, previous_hash in checkpoint["files"].items():
        if current[relative] == previous_hash:
            continue
        target = ROOT / relative
        if target.is_symlink() or not target.resolve().is_relative_to(ROOT.resolve()):
            raise RuntimeError("Generated path changed identity; refusing restoration")
        if previous_hash is None:
            if target.is_file():
                target.unlink()  # exact predeclared newly generated file only
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(checkpoint["backup"] / relative, target)
        restored.append(relative)
    return restored


def _status_git_changes() -> set[str]:
    """NUL paths retain spaces and rename originals; no directory-wide staging."""
    output = subprocess.check_output(["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"], cwd=ROOT, text=True)
    entries, paths, index = output.split("\0"), set(), 0
    while index < len(entries):
        entry = entries[index]
        index += 1
        if not entry:
            continue
        paths.add(entry[3:])
        if "R" in entry[:2] or "C" in entry[:2]:
            if index >= len(entries) or not entries[index]:
                raise ValueError("Incomplete git rename status")
            paths.add(entries[index])
            index += 1
    return paths


def publish_status_audit(context: dict, owned_hashes: dict[str, str], *, publish=False, revision=None, generated_paths=()) -> dict:
    """Commit only this run's explicit status-audit files, never a research revision.

    Called from --publish only after the original clean-main/lock protections.
    Direct publish=False calls retain local audit files without committing or
    pushing; the main dry-run never collects or calls this helper at all.
    """
    pattern = r"data/weekly-v3/research-status/(?:baseline\.json|20\d{2}-W(?:0[1-9]|[1-4]\d|5[0-3])/(?:snapshot\.json|\d{8}T\d{12}Z/(?:observations\.jsonl|check\.json|review-queue\.json)))"
    generated_paths = set(generated_paths)
    if generated_paths and not generated_paths <= set(planned_generated_paths(context)):
        raise ValueError("Metadata audit contains undeclared generated files")
    if any(path not in generated_paths and path != "data/weekly-v3/source-coverage.json" and not re.fullmatch(pattern, path) for path in owned_hashes):
        raise ValueError("Status audit manifest contains an unowned path")
    changes = _status_git_changes()
    foreign = changes - set(owned_hashes)
    result = {"status": "research_noop_with_status_observations", "week": context["week"], "revision": revision,
              "research_changed": False, "committed": False, "pushed": False, "owned_paths": sorted(changes & set(owned_hashes))}
    if foreign:
        return {**result, "status": "unowned_changes_require_review", "unowned_paths": sorted(foreign)}
    for relative, expected in owned_hashes.items():
        path = _status_file(relative)
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            return {**result, "status": "status_audit_changed_during_verification"}
    if not changes:
        return {**result, "status": "unchanged"}
    if not publish:
        return {**result, "retained_locally": True}
    if git("branch", "--show-current") != "main":
        return {**result, "status": "status_audit_requires_main"}
    run(["git", "add", "--", *sorted(changes)])
    if _status_git_changes() - set(owned_hashes):
        return {**result, "status": "unowned_changes_require_review"}
    pending = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode
    if pending not in {0, 1}:
        raise RuntimeError("Cannot verify status-audit staging")
    if pending == 1:
        run(["git", "commit", "-m", f"data: metadata/status audit {context['week']} (research revision unchanged)"])
        run(["git", "push", "origin", "HEAD:main"])
        result.update(committed=True, pushed=True)
    return result


def _verify_catalog_unchanged_before_ingest(checkpoint):
    catalog = {**checkpoint, "files": {path: value for path, value in checkpoint["files"].items() if path.startswith("data/catalog/")}}
    if generated_hashes(catalog) != catalog["files"]:
        raise RuntimeError("Catalog changed during collection; refusing to overwrite concurrent edits")


def _finish_status_audit(checkpoint, expected_generated_hashes, owned_hashes, context, previous, audit, audit_path, *, publish):
    # An unchanged research hash is not permission to roll back real checks,
    # acquired records, provenance or their matching manifest. Retain every
    # verified generated change, and stage only its exact predeclared pathname.
    if generated_hashes(checkpoint) != expected_generated_hashes:
        raise RuntimeError("Generated files changed after verification; refusing metadata publication")
    changed = {path: value for path, value in expected_generated_hashes.items() if value != checkpoint["files"][path]}
    if any(value is None for value in changed.values()):
        raise RuntimeError("Generated file deletion requires review; status audit cannot discard records")
    retained_hashes = {**changed, **owned_hashes}
    result = publish_status_audit(context, retained_hashes, publish=publish, revision=previous.get("revision"), generated_paths=changed)
    audit.update(**result, preserved_generated_paths=sorted(changed))
    write_json(audit_path, audit)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] in {"research_noop_with_status_observations", "unchanged"} else 1


def run_audit_path(context: dict, now: datetime) -> Path:
    return ROOT / "logs/weekly-v3/runs" / f"{now.strftime('%Y%m%dT%H%M%S%fZ')}-{context['week']}.json"


def published_editorial_completion(manifest: dict, worker_status: dict | None = None) -> dict:
    """Count only the final export's digest-validated, current LLM summaries.

    Worker success or previous_complete_preserved can describe old evidence.
    Neither overrides a final monthly data_only/legacy_editorial/missing state.
    """
    months = list(dict.fromkeys(value for value in [*manifest.get("complete_months", []), manifest.get("provisional_month")]
                               if isinstance(value, str) and re.fullmatch(r"20\d{2}-(0[1-9]|1[0-2])", value)))
    statuses = {}
    for month in months:
        snapshot = read_json(ROOT / "docs/public/api/v1/monthly" / f"{month}.json", {})
        statuses[month] = snapshot.get("editorial_status", "missing") if snapshot.get("month") == month else "missing"
    completed = [month for month in months if statuses[month] == "llm_complete"]
    retained = [row.get("month") for row in (worker_status or {}).get("months", []) if row.get("previous_complete_preserved") and row.get("month") in months]
    return {"summary_mode": "llm_complete" if months and len(completed) == len(months) else "llm_partial" if completed else "data_only",
            "basis": "final_public_monthly_editorial_status", "current_month_statuses": statuses,
            "current_completed_months": completed, "historical_retained_months": list(dict.fromkeys(retained))}


def choose_snapshot(previous: dict, context: dict, now: datetime, state: dict, coverage: dict, summary_mode: str) -> tuple[dict, dict]:
    """One ISO-week document; source-health updates need no research revision."""
    research_hash = content_hash({"state": state, "summary_mode": summary_mode})
    coverage_hash = content_hash(coverage)
    same_week = previous.get("week") == context["week"]
    research_changed = not same_week or previous.get("research_content_hash") != research_hash
    coverage_changed = not same_week or previous.get("coverage_hash") != coverage_hash
    previous_revision = int(previous.get("revision", 0)) if same_week else 0
    if not research_changed and not coverage_changed:
        return copy.deepcopy(previous), {"research_changed": False, "coverage_changed": False, "publish_changed": False}
    revision = previous_revision + 1 if research_changed else previous_revision
    snapshot = {"version": "3.2", "week": context["week"], "coverage": context, "run_at": now.isoformat(),
                "requested_source_cutoff": coverage["requested_source_cutoff"], "data_through": coverage["available_data_through"],
                "source_checks": copy.deepcopy(coverage["sources"]), "collection_coverage": coverage, "verified": True,
                "summary_mode": summary_mode, "research_content_hash": research_hash, "coverage_hash": coverage_hash,
                "revision": revision, "revision_basis": "research_content_not_run_metadata", "research_changed": research_changed}
    return snapshot, {"research_changed": research_changed, "coverage_changed": coverage_changed, "publish_changed": True}


def weekly_digest(context: dict, now: datetime, *, write: bool = True, coverage: dict | None = None) -> str:
    from temporal_evidence import public_day

    def safe_text(value):
        text = html.escape(str(value or ""), quote=False).replace("\n", " ").replace("\r", " ")
        return re.sub(r"([\\`*_\[\]{}|])", r"\\\1", text)

    def source_link(event):
        value = str(event.get("url") or "")
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            return "来源链接待核验"
        return f"[{safe_text(event.get('title'))}](<{quote(value, safe=':/?#@!$&\x27*+,;=%-_.~')}>)"

    organizations = read_json(ROOT / "docs/public/api/v1/organizations.json", [])
    events = []
    seen = set()
    for organization in organizations:
        for event in organization.get("updates", []):
            precision = event.get("date_precision")
            published_day = public_day(event.get("published_at"), precision) if precision not in {"month", "year", "unknown"} else None
            published = published_day.isoformat() if published_day else None
            key = (event["event_id"], organization["organization_id"])
            if published and context["from"] <= published <= context["until"] and key not in seen:
                seen.add(key)
                events.append({**event, "organization_name": organization["name"], "local_date": published})
    # Strategic observations do not require a research work or G1/G2 lab
    # attribution. Keep them visibly separate; never let this path upgrade a
    # hiring/demo/personnel clue into a reviewed research publication.
    strategic_types = {"deployment", "demo", "company_demo", "hiring", "hiring_signal", "personnel_change", "organization_change", "funding", "strategic_update"}
    names = {org["organization_id"]: org["name"] for org in organizations}
    for event in read_json(ROOT / "docs/public/api/v1/events.json", []):
        if (event.get("event_type") not in strategic_types and event.get("evidence_layer") != "S") or event.get("organization_id") not in names:
            continue
        key = (event["event_id"], event["organization_id"])
        if key in seen:
            continue
        precision = event.get("date_precision")
        when = public_day(event.get("published_at"), precision) if precision not in {"month", "year", "unknown"} else None
        basis = "公开日期"
        if when is None:
            when = public_day(event.get("observed_at") or event.get("first_seen_at"))
            basis = "首次观测日期（发布日期待核验）"
        if when and context["from"] <= when.isoformat() <= context["until"]:
            seen.add(key)
            events.append({**event, "organization_name": names[event["organization_id"]], "local_date": when.isoformat(), "date_basis": basis})
    organization_count = len({event["organization_name"] for event in events})
    grouped = {}
    for event in events:
        key = (event.get("work_id") or event.get("url"), event["event_type"])
        if key in grouped:
            grouped[key]["organization_names"].add(event["organization_name"])
        else:
            grouped[key] = {**event, "organization_names": {event["organization_name"]}}
    events = [{**event, "organization_name": " × ".join(sorted(event.pop("organization_names")))} for event in grouped.values()]
    events.sort(key=lambda row: row.get("published_at", ""), reverse=True)
    research = [row for row in events if row["event_type"] not in strategic_types and row.get("evidence_layer") != "S"]
    strategic = [row for row in events if row not in research]
    lines = [f"# 具身智能关键研究组周报 · {context['week']}", "", f"覆盖北京时间 {context['from']}—{context['until']}。运行检查时间单独保存在周更审计中。", "", "## 本周判断", "",
             f"- 已登记 {len(research)} 项研究发布与 {len(strategic)} 项战略观察，涉及 {organization_count} 个组织。",
             "- 第一方技术报告与公开评审分别保留；共同署名不能替代独立复现。",
             "- 研究趋势及来源缺口以当月研究账本为准。", "", "## 本周研究变化", ""]
    if not research:
        lines.append("本周无可升级信号。来源读取失败或资料不足不解释为没有研究活动。")
    for event in research[:12]:
        lines.extend([f"### {safe_text(event['organization_name'])} · {safe_text(event['title'])}", "", f"- {event['local_date']} · {safe_text(event['event_type'])} · {safe_text(' / '.join(event.get('direction_codes', [])))}", f"- {safe_text(event.get('summary_zh') or '详细贡献与实验条件请查原始来源。')}", f"- 公开来源：{source_link(event)}", ""])
    lines += ["## 战略观察", ""]
    for event in strategic:
        lines.append(f"- {safe_text(event['organization_name'])} · {source_link(event)} · {event['local_date']} {safe_text(event.get('date_basis', '公开日期'))}：{safe_text(event.get('summary_zh') or '公开战略披露，未作为同行评审成果计数。')}")
    if not strategic:
        lines.append("本周无新增已登记战略观察。")
    if len(research) > 12:
        lines += ["", "## 其他已登记研究变化", ""]
        lines.extend(f"- {safe_text(event['organization_name'])} · {source_link(event)}" for event in research[12:])
    if coverage:
        lines += ["", "## 来源覆盖与缺口", "",
                  f"- 可用数据截止：{safe_text(coverage.get('available_data_through') or '未知')}；这不是全来源已完整更新的声明。",
                  f"- 登记范围完整检查截止：{safe_text(coverage.get('complete_through') or '尚无可证实的完整检查')}。",
                  f"- 本次未完整来源：{safe_text('、'.join(coverage.get('incomplete_sources', [])) or '无（仅限登记范围）')}。"]
        for source in coverage.get("sources", []):
            window = source.get("requested_window") or {}
            lines.append(f"- {safe_text(source['source'])}：{safe_text(source['status'])}；请求范围 {safe_text(json.dumps(window, ensure_ascii=False, sort_keys=True))}；完整子检查 {source.get('completed_checks', 0)}/{source.get('expected_checks', '?')}。")
    content = "\n".join(lines) + "\n"
    if write:
        path = ROOT / "docs/pulse/weekly" / (context["week"].lower() + ".md")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    return content


def snapshot_path(context: dict) -> Path:
    return ROOT / "data/weekly-v3" / (context["week"] + ".json")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publish", action="store_true", help="Execute, verify, commit the explicit data scope and push main")
    parser.add_argument("--dry-run", action="store_true", help="Read-only preview (also the default)")
    parser.add_argument("--fallback", action="store_true", help="Skip if the completed ISO week already has a verified snapshot")
    parser.add_argument("--data-only", action="store_true", help="Do not contact an LLM; retain historical editorial files")
    parser.add_argument("--as-of", type=date.fromisoformat, help="Explicit source collection cutoff; run time remains the actual UTC time")
    parser.add_argument("--check-snapshot", action="store_true", help="Print workflow outputs for the last completed ISO week; never mutate")
    parser.add_argument("--preview-report", action="store_true", help="Render the actual weekly digest to stdout without collecting, writing or publishing")
    configuration = parser.add_mutually_exclusive_group()
    configuration.add_argument("--env-file", type=Path, help="Optional local LLM credentials file outside the repository; never printed")
    configuration.add_argument("--loggerbot-env-file", type=Path, help="Read only CODEX_PROXY model fields from existing external LoggerBot configuration")
    args = parser.parse_args(argv)
    if args.publish and args.dry_run:
        parser.error("--publish and --dry-run are mutually exclusive")
    now = datetime.now(timezone.utc)
    context = week_context(now)
    if args.preview_report:
        print(weekly_digest(context, now, write=False))
        return 0
    cutoff = args.as_of or now.astimezone(SHANGHAI).date() - timedelta(days=1)
    if cutoff > now.astimezone(SHANGHAI).date():
        parser.error("source cutoff cannot be in the future")
    previous = read_json(snapshot_path(context), {})
    ready = bool(previous.get("verified"))
    if args.check_snapshot:
        print(f"ready={'true' if ready else 'false'}\nweek={context['week']}")
        return 0
    branch, changes = git("branch", "--show-current"), git("status", "--porcelain")
    if not args.publish:
        print(json.dumps({"mode": "dry_run", "run_at": now.isoformat(), "coverage": context, "requested_source_cutoff": cutoff.isoformat(), "branch": branch,
                          "clean": not bool(changes), "already_verified": ready, "can_publish": branch == "main" and not changes,
                          "note": "Feature branches are preview-only; publish requires a clean main checkout. No files or network state were changed.",
                          "steps": ["ff-only main update", "incremental arXiv then all-registered-ID status watch; publications/official groups/CoRL", "v3:ingest", "status-only audit commit if research unchanged", "v3:editorial (unless data-only)", "v3:export", "v3:site", "npm test", "ISO-week snapshot", "explicit-path commit", "push main"]}, ensure_ascii=False, indent=2))
        return 0
    if branch != "main" or changes:
        raise SystemExit("Publishing requires a clean main checkout. Run without --publish for a read-only preview.")
    if not args.data_only and (args.loggerbot_env_file or (args.env_file and args.env_file.exists())):
        try:
            from model_runtime import load_model_configuration, ModelConfigurationError
        except ModuleNotFoundError:
            from scripts.model_runtime import load_model_configuration, ModelConfigurationError
        try:
            load_model_configuration(env_file=args.env_file, loggerbot_env_file=args.loggerbot_env_file)
        except ModelConfigurationError as exc:
            raise SystemExit(str(exc)) from None
    lock_path = Path(git("rev-parse", "--git-path", "weekly-v3.lock"))
    if not lock_path.is_absolute():
        lock_path = ROOT / lock_path
    with lock_path.open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit("Another live weekly update holds the repository lock.")
        run(["git", "pull", "--ff-only", "origin", "main"])
        previous = read_json(snapshot_path(context), {})
        if args.fallback and previous.get("verified"):
            print(f"Verified snapshot {context['week']} already exists; fallback skipped.")
            return 0
        audit = {"schema_version": "1", "week": context["week"], "run_at": now.isoformat(), "requested_source_cutoff": cutoff.isoformat(),
                 "status": "started", "mode": "fallback" if args.fallback else "local", "llm_requested": not args.data_only}
        audit_path = run_audit_path(context, now)
        write_json(audit_path, audit)
        with tempfile.TemporaryDirectory(prefix="radar-weekly-generated-") as directory:
            checkpoint = checkpoint_generated(planned_generated_paths(context), Path(directory))
            try:
                source_checks = collect_sources(cutoff, now)
                status_owned_hashes = {path: value for check in source_checks for path, value in check.get("_status_audit_hashes", {}).items()}
                metadata = read_json(ROOT / "data/catalog/manifest.json", {})
                prior_cutoff = metadata.get("data_through") or read_json(ROOT / "config/source-registry.json")["window"]["until"]
                coverage = collection_coverage(source_checks, cutoff, prior_cutoff, previous.get("collection_coverage"))
                effective_cutoff = coverage["available_data_through"] or prior_cutoff
                audit.update(status="collected", source_checks=source_checks, collection_coverage=coverage)
                write_json(audit_path, audit)
                # Public consumers must show this coverage alongside data_through.
                # It is derived run coverage, not a new editable fact source.
                write_json(ROOT / "data/weekly-v3/source-coverage.json", coverage)
                if status_owned_hashes:
                    status_owned_hashes["data/weekly-v3/source-coverage.json"] = hashlib.sha256((ROOT / "data/weekly-v3/source-coverage.json").read_bytes()).hexdigest()
                _verify_catalog_unchanged_before_ingest(checkpoint)
                run(["npm", "run", "v3:ingest", "--", "--as-of", effective_cutoff])
                generated_after_ingest = generated_hashes(checkpoint)
                # Same-week status observations do not call the LLM worker,
                # regenerate the weekly report, or create research revisions.
                # A data-only/partial snapshot can still be upgraded when the
                # caller explicitly requested LLM work.
                if status_owned_hashes and previous.get("week") == context["week"] and (args.data_only or previous.get("summary_mode") == "llm_complete"):
                    state = research_state()
                    unchanged = previous.get("research_content_hash") == content_hash({"state": state, "summary_mode": previous.get("summary_mode")})
                    if unchanged and previous.get("coverage_hash") == content_hash(coverage):
                        return _finish_status_audit(checkpoint, generated_after_ingest, status_owned_hashes, context, previous, audit, audit_path, publish=args.publish)
                run(["npm", "run", "v3:legacy-editorial"])
                if not args.data_only:
                    # Exactly one worker invocation; it owns retries/fallback.
                    run(["npm", "run", "v3:editorial"])
                run(["npm", "run", "v3:export"])
                run(["npm", "run", "v3:site"])
                weekly_digest(context, now, coverage=coverage)
                run(["npm", "test"])
                generated_after_verification = generated_hashes(checkpoint)
                manifest = read_json(ROOT / "docs/public/api/v1/catalog-manifest.json", {})
                editorial_completion = published_editorial_completion(manifest, read_json(ROOT / "data/editorial/status.json", {}))
                summary_mode = editorial_completion["summary_mode"]
                snapshot, changes = choose_snapshot(previous, context, now, research_state(), coverage, summary_mode)
                audit.update(status="verified", **changes, summary_mode=summary_mode, revision=snapshot["revision"],
                             catalog_hash=manifest.get("catalog_hash"), editorial_completion=editorial_completion)
                if not changes["publish_changed"]:
                    return _finish_status_audit(checkpoint, generated_after_verification, status_owned_hashes, context, previous, audit, audit_path, publish=args.publish)
                snapshot["catalog_hash"] = manifest.get("catalog_hash")
                snapshot["editorial_completion"] = editorial_completion
                write_json(snapshot_path(context), snapshot)
                paths = [path for path in STAGED_PATHS if (ROOT / path).exists()]
                run(["git", "add", "--", *paths])
                committed = bool(subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode)
                if committed:
                    description = f"verified research radar {context['week']} revision {snapshot['revision']}" if changes["research_changed"] else f"source coverage {context['week']} (research revision {snapshot['revision']} unchanged)"
                    run(["git", "commit", "-m", "data: " + description])
                    run(["git", "push", "origin", "HEAD:main"])
                audit.update(status="verified_and_pushed" if committed else "verified_no_commit", committed=committed)
                write_json(audit_path, audit)
                print(json.dumps({"status": audit["status"], "week": context["week"], "data_through": effective_cutoff, "source_coverage_status": coverage["status"], "revision": snapshot["revision"]}, ensure_ascii=False))
            except Exception as error:
                # Preserve partially collected data and diagnostics for review;
                # never roll back a failed run or delete unknown user files.
                audit.update(status="failed", error_type=type(error).__name__)
                write_json(audit_path, audit)
                raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
