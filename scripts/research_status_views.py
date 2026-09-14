"""Deterministic status/dependency views; editorial text is never rewritten."""
from __future__ import annotations

from research_status import research_status_as_of
from temporal_evidence import public_day

STATUS_EVENTS = {"withdrawn", "retracted", "corrected", "expression_of_concern", "reinstated"}
EDITORIAL_SECTIONS = ("claims", "direction_summaries", "question_summaries", "organization_changes", "counterevidence", "watchlist")


def latest_status_observation(works, source_records, baseline):
    """Current status metadata has its own clock, independent of text coverage."""
    sources = source_records if isinstance(source_records, dict) else {row["source_record_id"]: row for row in source_records}
    dates = [public_day(baseline)]
    for work in works:
        for notice in work.get("research_status_notices", []):
            if notice.get("review_status") != "verified" or notice.get("scope") != "work" or notice.get("event_type") not in STATUS_EVENTS:
                continue
            for sid in notice.get("source_record_ids", []):
                source = sources.get(sid, {})
                source_type = str(source.get("source_type", ""))
                if sid in work.get("source_record_ids", []) and source.get("url") == notice.get("source_url") and source_type.startswith("official_") and source_type.endswith("_status_notice"):
                    dates.append(public_day(source.get("observed_at") or source.get("retrieved_at")))
    return max(day for day in dates if day is not None).isoformat()


def status_work_views(works, cutoff, source_records):
    result = []
    for work in works:
        if not work.get("research_status_notices"):
            continue
        status = research_status_as_of(work, cutoff, source_records)
        if status["notices"] or status["information_gaps"]:
            result.append({"work_id": work["work_id"], "title": work["title"], "as_of": str(cutoff),
                           "relevance_status": work.get("relevance", {}).get("status", "unknown"), **status})
    return sorted(result, key=lambda row: row["work_id"])


def status_changes(views, *, month=None):
    """Not organization attribution: these are direct work-level notices."""
    rows = []
    for work in views:
        for notice in work["notices"]:
            if month is not None and notice.get("date_precision") in {"year", "unknown"}:
                continue
            day = public_day(notice.get("public_at"), notice.get("date_precision"))
            if day and (month is None or day.isoformat()[:7] == month):
                rows.append({**notice, "work_id": work["work_id"], "work_title": work["title"]})
    return sorted(rows, key=lambda row: (row["public_at"], row["notice_id"]), reverse=True)


def editorial_status_dependencies(editorial, current_views, events):
    """Find retained statements affected by notices known at the current cut.

    This is an explicit review queue, not a claim that a correction invalidates
    every result or that a later withdrawal was known in an earlier month.
    """
    affected = {row["work_id"]: row for row in current_views if row["notices"]}
    event_works = {row["event_id"]: row.get("work_id") for row in events}
    result = []
    for section in EDITORIAL_SECTIONS:
        for index, claim in enumerate(editorial.get(section, [])):
            cited = {event_works.get(value, value) for field in ("supporting_ids", "counterevidence_ids") for value in claim.get(field, [])}
            for work_id in sorted(cited & affected.keys()):
                status = affected[work_id]
                result.append({"claim_id": claim.get("claim_id"), "section": section, "index": index,
                               "code": claim.get("code"), "title": claim.get("title"), "work_id": work_id,
                               "work_title": status["title"], "status": status["status"],
                               "validation_eligible": status["validation_eligible"], "as_of": status["as_of"],
                               "notice_ids": [notice["notice_id"] for notice in status["notices"]],
                               "review_state": "requires_status_aware_review_not_silent_text_edit"})
    return result
