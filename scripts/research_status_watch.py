"""Bounded, injectable checks of updates to already registered arXiv works.

No first-submission-month or relevance filter: old, candidate and excluded works
remain in scope if they have an explicit registered arXiv identity. Preprints
are comparison baselines, not a source of unrelated IDs to discover. No files
are read/written, no authoritative notice/source is changed, and observations
are returned separately for an append-only caller-owned check history.

The default API uses only id_list, without search_query (which would intersect
and hide some requested IDs). Public requests are serial, <=200 IDs per batch,
with a three-second gap between requests. API contract:
https://info.arxiv.org/help/api/user-manual.html#query-interface
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timezone

try:
    from collect_research_status import extract_arxiv_status, fetch_html
except ModuleNotFoundError:
    from scripts.collect_research_status import extract_arxiv_status, fetch_html

ATOM = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
STATUS_HINT = re.compile(r"\b(?:withdraw(?:n|al)?|retract(?:ed|ion)?|reinstate(?:d|ment)?|expression of concern)\b", re.I)


def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _arxiv(value):
    if not isinstance(value, str):
        return None
    value = re.sub(r"^(?:arxiv:|https?://(?:export\.)?arxiv\.org/(?:abs|pdf)/)", "", value.strip(), flags=re.I)
    value = re.sub(r"(?:v\d+)?(?:\.pdf)?$", "", value)
    return value if re.fullmatch(r"(?:\d{4}\.\d{4,5}|[A-Za-z.-]+/\d{7})", value) else None


def _version(row):
    for key in ("latest_version", "version", "arxiv_version_id", "pdf_url", "id"):
        value = row.get(key)
        if isinstance(value, int) and not isinstance(value, bool) and value > 0:
            return f"v{value}"
        if isinstance(value, str):
            match = re.search(r"(?:^|v)([1-9]\d*)(?:\.pdf)?$", value)
            if match:
                return "v" + match.group(1)
    return None


def _metadata(row):
    base = next((base for key in ("arxiv_id", "preprint_id", "work_id", "id") if (base := _arxiv(row.get(key)))), None)
    comment = row.get("comment", row.get("comments"))
    return {"arxiv_id": base, "latest_version": _version(row), "updated_at": row.get("updated_at") or row.get("updated"),
            "comment_sha256": _digest(re.sub(r"\s+", " ", comment).strip()) if isinstance(comment, str) else row.get("comment_sha256"),
            "status_comment_hint": bool(STATUS_HINT.search(comment)) if isinstance(comment, str) else bool(row.get("status_comment_hint")),
            "status_check_pending": bool(row.get("status_check_pending"))}


def parse_latest_metadata(body):
    """Parse only identity/version/update/comment; never infer research status."""
    root = ET.fromstring(body)
    if root.tag != "{http://www.w3.org/2005/Atom}feed":
        raise ValueError("not_an_atom_feed")
    rows = []
    for entry in root.findall("a:entry", ATOM):
        raw_id = entry.findtext("a:id", default="", namespaces=ATOM)
        if not _arxiv(raw_id):
            raise ValueError("arxiv_error_or_invalid_entry")
        links = {node.attrib.get("title", ""): node.attrib.get("href", "") for node in entry.findall("a:link", ATOM)}
        rows.append({"id": raw_id, "arxiv_id": _arxiv(raw_id), "pdf_url": links.get("pdf"),
                     "updated_at": entry.findtext("a:updated", default="", namespaces=ATOM),
                     "comment": entry.findtext("x:comment", default="", namespaces=ATOM)})
    return rows


def fetch_latest_metadata(ids):
    if not ids or len(ids) > 200 or len(set(ids)) != len(ids) or any(_arxiv(value) != value for value in ids):
        raise ValueError("invalid_known_arxiv_id_batch")
    query = urllib.parse.urlencode({"id_list": ",".join(ids), "start": 0, "max_results": len(ids)})
    request = urllib.request.Request("https://export.arxiv.org/api/query?" + query,
                                     headers={"User-Agent": "EmbodiedResearchRadar/3 known-work-status-watch", "Accept": "application/atom+xml"})
    with urllib.request.urlopen(request, timeout=60) as response:
        body = response.read(4_000_001)
    if len(body) > 4_000_000:
        raise ValueError("metadata_response_too_large")
    return parse_latest_metadata(body)


def _fetch_status(url, work_id, _attempted_at):
    html = fetch_html(url)
    return extract_arxiv_status(html, url, work_id, _now())


def _notice_version(notice):
    parsed = urllib.parse.urlsplit(notice.get("source_url", ""))
    match = re.fullmatch(r"/abs/(.+)v([1-9]\d*)", parsed.path)
    return (match.group(1), "v" + match.group(2)) if parsed.scheme == "https" and parsed.netloc == "arxiv.org" and match else (None, None)


def _date_key(notice):
    date, precision = notice.get("public_at"), notice.get("date_precision")
    if precision == "second" and isinstance(date, str):
        try:
            parsed = datetime.fromisoformat(date.replace("Z", "+00:00"))
            if parsed.tzinfo:
                return precision, parsed.astimezone(timezone.utc).isoformat()
        except ValueError:
            pass
    return precision, date


def watch_research_status(works, preprints, *, verified_notices=None, metadata_fetcher=None, status_fetcher=None,
                          sleeper=time.sleep, observed_at=None, batch_size=200):
    """Return coverage, candidates, review items, observations and new baselines.

    metadata_fetcher(ids) -> metadata row list or Atom XML. status_fetcher(url,
    arxiv_work_alias, attempted_at) -> collector notice/None/review result.
    An explicit observed_at makes fixture runs deterministic; production leaves
    it unset. A changed metadata baseline never constitutes a status decision.
    metadata_updates must be persisted separately by the caller, after retaining
    observations/review obligations. status_check_pending preserves retry intent
    after failures and until a candidate notice is acknowledged in the input.
    This function does not edit preprints.
    """
    if isinstance(batch_size, bool) or not isinstance(batch_size, int) or not 1 <= batch_size <= 200:
        raise ValueError("status_watch_batch_size_must_be_1_to_200")
    if observed_at is not None:
        stamp = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
        if stamp.tzinfo is None or stamp.utcoffset().total_seconds() != 0:
            raise ValueError("status_watch_observation_must_be_utc")
    timestamp = lambda: observed_at or _now()
    metadata_fetcher, status_fetcher = metadata_fetcher or fetch_latest_metadata, status_fetcher or _fetch_status
    owners, owner_aliases, work_bases, notices = defaultdict(set), defaultdict(set), defaultdict(set), list(verified_notices or [])
    for work in works:
        wid = work.get("work_id")
        ids = [wid, (work.get("identifiers") or {}).get("arxiv"), *work.get("aliases", [])]
        for value in ids:
            base = _arxiv(value)
            if base:
                owners[base].add(wid)
                owner_aliases[base].update(value for value in [wid, "arxiv:" + base, *work.get("aliases", [])] if isinstance(value, str))
                work_bases[wid].add(base)
        notices.extend(work.get("research_status_notices", []))
    requested = sorted(owners)
    baselines = {}
    for raw in preprints:
        row = _metadata(raw)
        base = row["arxiv_id"]
        if base in owners:
            key = lambda value: (int((value.get("latest_version") or "v0")[1:]), value.get("updated_at") or "")
            if base not in baselines or key(row) > key(baselines[base]):
                baselines[base] = row
    known, invalid_known = defaultdict(list), []
    for notice in notices:
        if not isinstance(notice, dict) or notice.get("review_status") != "verified" or notice.get("scope") != "work" or notice.get("event_type") not in {"withdrawn", "retracted", "corrected", "expression_of_concern", "reinstated"}:
            continue
        base, _ = _notice_version(notice)
        candidates = {base} if base in owners else work_bases.get(notice.get("work_id"), set())
        for key in candidates:
            if notice.get("work_id") not in owner_aliases[key]:
                invalid_known.append({"error_code": "known_notice_work_identity_mismatch", "arxiv_id": key, "notice_id": notice.get("notice_id")})
                continue
            if not any(_digest(old) == _digest(notice) for old in known[key]):
                known[key].append(notice)
    reviews, observations, additions, updates, batches = invalid_known[:], [], [], [], []
    returned, unexpected, duplicate_ids, request_count = set(), set(), set(), 0
    status_requested = status_completed = status_failed = status_reviewed = 0

    def call(fetcher, *args):
        nonlocal request_count
        if request_count:
            sleeper(3.0)
        request_count += 1
        return fetcher(*args)

    def observe(kind, base, outcome, **extra):
        row = {"kind": kind, "arxiv_id": base, "observed_at": timestamp(), "outcome": outcome, **extra}
        row["observation_id"] = "research-status-observation:" + _digest(row)[:24]
        observations.append(row)

    for start in range(0, len(requested), batch_size):
        ids = requested[start:start + batch_size]
        by_id, failure = {}, None
        try:
            raw_rows = call(metadata_fetcher, ids[:])
            rows = parse_latest_metadata(raw_rows) if isinstance(raw_rows, (str, bytes)) else raw_rows
            if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
                raise ValueError("invalid_metadata_rows")
            for raw in rows:
                row = _metadata(raw)
                base = row["arxiv_id"]
                if base not in ids:
                    unexpected.add(base or "unparseable")
                    reviews.append({"error_code": "unexpected_metadata_identity", "arxiv_id": base})
                    continue
                returned.add(base)
                if base in by_id:
                    duplicate_ids.add(base)
                    reviews.append({"error_code": "duplicate_metadata_identity", "arxiv_id": base})
                by_id[base] = row
        except Exception:
            failure = "metadata_fetch_failed"
            reviews.append({"error_code": failure, "requested_ids": ids[:]})
        missing = [base for base in ids if base not in by_id]
        batches.append({"requested_ids": ids[:], "returned_ids": sorted(by_id), "missing_ids": missing,
                        "status": "failed" if failure else "partial" if missing or set(ids) & duplicate_ids else "complete",
                        **({"error_code": failure} if failure else {})})
        for base in ids:
            row = by_id.get(base)
            if failure or row is None:
                observe("metadata", base, failure or "missing_from_response")
                if not failure:
                    reviews.append({"error_code": "metadata_id_missing", "arxiv_id": base})
                continue
            if base in duplicate_ids or len(owners[base]) != 1:
                observe("metadata", base, "identity_requires_review")
                if len(owners[base]) != 1:
                    reviews.append({"error_code": "ambiguous_registered_work", "arxiv_id": base, "work_ids": sorted(owners[base])})
                continue
            previous, version = baselines.get(base), row["latest_version"]
            if not version:
                observe("metadata", base, "version_missing")
                reviews.append({"error_code": "latest_version_missing", "arxiv_id": base})
                continue
            if previous and previous["latest_version"] and int(version[1:]) < int(previous["latest_version"][1:]):
                observe("metadata", base, "version_regressed", metadata=row)
                reviews.append({"error_code": "latest_version_regressed", "arxiv_id": base})
                continue
            reasons = ["no_baseline"] if not previous else [key + "_changed" for key in ("latest_version", "updated_at", "comment_sha256") if row[key] != previous[key]]
            if previous and previous["status_check_pending"]:
                reasons.append("previous_status_check_pending")
            if not row["updated_at"]:
                reasons.append("updated_at_missing")
                reviews.append({"error_code": "metadata_updated_at_missing", "arxiv_id": base})
            if row["status_comment_hint"]:
                reasons.append("status_comment_hint")
            if known[base]:
                reasons.append("known_status_notice")
            observe("metadata", base, "status_check_needed" if reasons else "unchanged", metadata=copy.deepcopy(row), reasons=reasons[:])
            update = {**row, "observed_at": timestamp(), "status_check_pending": bool(reasons)}
            updates.append(update)
            if not reasons:
                continue
            url, alias = f"https://arxiv.org/abs/{base}{version}", "arxiv:" + base
            status_requested += 1
            try:
                result = call(status_fetcher, url, alias, timestamp())
            except Exception:
                status_failed += 1
                reviews.append({"error_code": "status_page_fetch_failed", "arxiv_id": base, "source_url": url})
                observe("version_status", base, "fetch_failed", version=version, source_url=url)
                continue
            status_completed += 1
            if result is None:
                outcome = "no_explicit_status_prior_notice_retained" if known[base] else "no_explicit_status"
                update["status_check_pending"] = bool(known[base])
                if known[base]:
                    status_reviewed += 1
                    reviews.append({"error_code": "no_explicit_status_for_previously_noticed_work", "arxiv_id": base, "source_url": url,
                                    "retained_notice_ids": [notice["notice_id"] for notice in known[base]]})
                observe("version_status", base, outcome, version=version, source_url=url,
                        retained_notice_ids=[notice["notice_id"] for notice in known[base]])
                continue
            if not isinstance(result, dict) or result.get("status") == "review_required":
                status_reviewed += 1
                reviews.append({"error_code": "status_page_requires_review", "arxiv_id": base, "source_url": url,
                                "extractor_result": copy.deepcopy(result) if isinstance(result, dict) else None})
                observe("version_status", base, "review_required", version=version, source_url=url)
                continue
            result_base, result_version = _notice_version(result)
            source = result.get("source_record")
            source_ids = result.get("source_record_ids")
            source_valid = isinstance(source, dict) and source.get("url") == url and isinstance(source_ids, list) and bool(source.get("source_record_id")) and source["source_record_id"] in source_ids and source.get("published_at") == result.get("public_at") and bool(result.get("public_at")) and result.get("date_precision") == "second" and isinstance(result.get("notice_id"), str)
            if (result_base, result_version) != (base, version) or result.get("work_id") != alias or result.get("review_status") != "verified" or result.get("scope") != "work" or result.get("event_type") not in {"withdrawn", "reinstated"} or not source_valid:
                status_reviewed += 1
                reviews.append({"error_code": "status_notice_identity_or_scope_mismatch", "arxiv_id": base, "source_url": url})
                observe("version_status", base, "review_required", version=version, source_url=url)
                continue
            same_version = [notice for notice in known[base] if _notice_version(notice) == (base, version)]
            matching = [notice for notice in same_version if notice.get("event_type") == result["event_type"]]
            conflict = bool(same_version) and (len(matching) != len(same_version) or any(_date_key(notice) != _date_key(result) for notice in matching))
            observed_source = copy.deepcopy(result.get("source_record"))
            if conflict:
                status_reviewed += 1
                reviews.append({"error_code": "known_notice_state_or_date_conflict", "arxiv_id": base, "source_url": url,
                                "existing_notice_ids": [notice["notice_id"] for notice in same_version], "observed_notice": copy.deepcopy(result)})
                outcome, canonical_notice = "notice_conflict_requires_review", None
            elif matching:
                outcome, canonical_notice = "known_notice_observed", matching[0]["notice_id"]
                update["status_check_pending"] = False
            else:
                additions.append(copy.deepcopy(result))
                known[base].append(copy.deepcopy(result))
                outcome, canonical_notice = "new_notice_candidate", result["notice_id"]
            observe("version_status", base, outcome, version=version, source_url=url, notice_id=canonical_notice,
                    observed_notice_id=result.get("notice_id"), observed_source_record=observed_source)
    missing = sorted(set(requested) - returned)
    metadata_complete = not missing and not unexpected and not duplicate_ids and not any(row["status"] != "complete" for row in batches) and not any(row["error_code"].startswith(("metadata_", "latest_version_", "ambiguous_registered_")) for row in reviews)
    state = "not_run" if not requested else "complete" if metadata_complete and not reviews and not status_failed else "partial" if returned else "failed"
    return {"schema_version": "1", "checked_at": timestamp(),
            "coverage": {"status": state, "metadata_complete": metadata_complete, "requested_count": len(requested), "returned_count": len(returned),
                         "missing_count": len(missing), "requested_ids": requested, "returned_ids": sorted(returned), "missing_ids": missing,
                         "unexpected_ids": sorted(unexpected), "duplicate_ids": sorted(duplicate_ids), "metadata_batches": batches,
                         "status_pages": {"requested": status_requested, "completed": status_completed, "failed": status_failed, "review_required": status_reviewed},
                         "request_count": request_count},
            "notice_candidates": additions, "review_queue": reviews, "observations": observations, "metadata_updates": updates}
