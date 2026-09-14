"""Pure, source-bound withdrawal/retraction/correction state at a cutoff.

This module changes neither raw records nor research counts. An unverified or
undated declaration is not a withdrawal fact. A correction is not an implicit
reinstatement. Same-time/overlapping blocking and reinstatement notices fail
closed until a reliably later reinstatement is available.
"""
from __future__ import annotations

import copy
import re
from datetime import date, datetime, time
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

EVENTS = {"withdrawn", "retracted", "corrected", "expression_of_concern", "reinstated"}
BLOCKING = {"withdrawn", "retracted"}
WARNINGS = {"corrected", "expression_of_concern"}
ZONE = ZoneInfo("Asia/Shanghai")


def _date_helpers():
    # temporal_evidence will itself call this module; no module-level cycle.
    try:
        from temporal_evidence import public_day, cutoff_day
    except ModuleNotFoundError:
        from scripts.temporal_evidence import public_day, cutoff_day
    return public_day, cutoff_day


def _url(value):
    if not isinstance(value, str) or any(char.isspace() for char in value):
        return None
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            return None
        return parsed._replace(scheme=parsed.scheme.lower(), netloc=parsed.netloc.lower(), fragment="").geturl().rstrip("/")
    except ValueError:
        return None


def _interval(value, precision):
    public_day, _ = _date_helpers()
    if precision == "unknown" or value is None:
        return None
    if precision not in {"second", "day", "month", "year"} or not isinstance(value, str):
        return None
    try:
        if precision == "second":
            if not re.match(r"^\d{4}-\d{2}-\d{2}T", value):
                return None
            instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return (instant, instant) if instant.tzinfo else None
        pattern = {"day": r"\d{4}-\d{2}-\d{2}", "month": r"\d{4}-\d{2}(?:-\d{2})?", "year": r"\d{4}(?:-\d{2}(?:-\d{2})?)?"}[precision]
        if not re.fullmatch(pattern, value):
            return None
        # Reject malformed more-precise spellings, without borrowing their
        # precision to locate a month/year-only event within its interval.
        if len(value) == 10:
            date.fromisoformat(value)
        elif len(value) == 7:
            date.fromisoformat(value + "-01")
        last = public_day(value, precision)
        if last is None:
            return None
        first = date(last.year, 1, 1) if precision == "year" else date(last.year, last.month, 1) if precision == "month" else last
        return datetime.combine(first, time.min, ZONE), datetime.combine(last, time.max, ZONE)
    except (TypeError, ValueError):
        return None


def _cutoff(value):
    _, cutoff_day = _date_helpers()
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError("research_status_cutoff_requires_timezone")
        return value
    if isinstance(value, str) and "T" in value:
        bounds = _interval(value, "second")
        if bounds is None:
            raise ValueError("research_status_invalid_cutoff")
        return bounds[1]
    return datetime.combine(cutoff_day(value), time.max, ZONE)


def _sources(records):
    if records is None:
        return None, set()
    if isinstance(records, dict):
        return records, set()
    values, duplicates = {}, set()
    for row in records:
        if not isinstance(row, dict) or not row.get("source_record_id"):
            continue
        sid = row["source_record_id"]
        if sid in values:
            duplicates.add(sid)
        values[sid] = row
    return values, duplicates


def _notice_error(notice, work, sources, duplicates):
    if not isinstance(notice, dict) or not all(isinstance(notice.get(key), str) and notice[key].strip() for key in ["notice_id", "summary_zh"]):
        return "notice_identity_or_summary_missing"
    if notice.get("event_type") not in EVENTS:
        return "notice_event_type_unsupported"
    if notice.get("scope") != "work":
        return "notice_scope_unsupported"
    if notice.get("review_status") != "verified":
        return "notice_not_verified"
    identities = {work.get("work_id"), *[value for value in work.get("aliases", []) if isinstance(value, str)]}
    if not work.get("work_id") or (notice.get("work_id") is not None and notice["work_id"] not in identities):
        return "notice_work_mismatch"
    ids = notice.get("source_record_ids")
    if not isinstance(ids, list) or not ids or any(not isinstance(sid, str) or not sid.strip() for sid in ids) or len(ids) != len(set(ids)):
        return "notice_source_ids_invalid"
    if not set(ids) <= set(work.get("source_record_ids", [])):
        return "notice_source_not_owned_by_work"
    url = _url(notice.get("source_url"))
    if not url:
        return "notice_source_url_invalid"
    if sources is None:
        return "notice_source_records_unavailable"
    if set(ids) & duplicates:
        return "notice_source_identity_ambiguous"
    for sid in ids:
        source = sources.get(sid)
        if not isinstance(source, dict) or source.get("source_record_id") != sid:
            return "notice_source_record_unknown_or_mismatched"
        if source.get("work_id") is not None and source["work_id"] not in identities:
            return "notice_source_record_wrong_work"
    matched = [sources[sid] for sid in ids if _url(sources[sid].get("url")) == url]
    if not matched:
        return "notice_source_url_mismatch"
    if not any(re.fullmatch(r"official_[a-z0-9_]+_status_notice", str(source.get("source_type") or "")) for source in matched):
        return "notice_source_not_official_status_notice"
    return None


def research_status_as_of(work, cutoff, source_records=None):
    """Return active/warning/blocking state with all verified available notices.

    Date-only values cover a full Shanghai day; month/year values only become
    usable at the interval's end. Reinstatement must be definitely later than
    the blocking notice to clear it. URL/date/verification hints in current
    metadata are never substituted for the notice's own verified fields.
    """
    until = _cutoff(cutoff)
    sources, duplicates = _sources(source_records)
    gaps, available = [], []
    original = work.get("research_status_notices", [])
    if not isinstance(original, list):
        original = []
        gaps.append({"reason": "research_status_notice_collection_invalid"})
    for index, notice in enumerate(original):
        interval = _interval(notice.get("public_at"), notice.get("date_precision")) if isinstance(notice, dict) else None
        # A later notice must not introduce a new warning into an earlier
        # month's packet, even when its source is not loaded for that view.
        if interval is not None and interval[1] > until:
            continue
        error = _notice_error(notice, work, sources, duplicates)
        identity = {"notice_id": notice.get("notice_id") if isinstance(notice, dict) else None, "notice_index": index}
        if error:
            gaps.append({**identity, "reason": error})
            continue
        if interval is None:
            gaps.append({**identity, "reason": "notice_date_unknown_or_invalid", "event_type": notice["event_type"],
                         "date_precision": notice.get("date_precision"), "source_url": notice["source_url"]})
            continue
        if interval[1] <= until:
            available.append((notice, interval))
    # Display order is deterministic, not a claim that overlapping intervals
    # have a known event order. The ambiguity record below states that limit.
    available.sort(key=lambda item: (item[1][1], item[1][0], item[0]["notice_id"]))
    reinstatements = [item for item in available if item[0]["event_type"] == "reinstated"]
    uncleared = [item for item in available if item[0]["event_type"] in BLOCKING and not any(restore[1][0] > item[1][1] for restore in reinstatements)]
    state_events = [item for item in available if item[0]["event_type"] in BLOCKING | {"reinstated"}]
    frontier = [item for item in state_events if not any(other[1][0] > item[1][1] for other in state_events)]
    frontier_types = {item[0]["event_type"] for item in frontier}
    if uncleared:
        status = "retracted" if any(item[0]["event_type"] == "retracted" for item in uncleared) else "withdrawn"
        if len(frontier_types) > 1 and frontier_types & BLOCKING:
            gaps.append({"reason": "ambiguous_status_notice_order", "ambiguous": True, "validation_blocked": True,
                         "notice_ids": sorted({item[0]["notice_id"] for item in frontier}),
                         "possible_final_events": sorted(frontier_types), "resolution": "requires_definitely_later_verified_reinstatement"})
    else:
        warnings = [item for item in available if item[0]["event_type"] in WARNINGS and not any(restore[1][0] > item[1][1] for restore in reinstatements)]
        latest = [item for item in warnings if not any(other[1][0] > item[1][1] for other in warnings)]
        kinds = {item[0]["event_type"] for item in latest}
        status = "expression_of_concern" if "expression_of_concern" in kinds else "corrected" if kinds else "active"
        if len(kinds) > 1:
            gaps.append({"reason": "ambiguous_warning_notice_order", "ambiguous": True, "validation_blocked": False,
                         "notice_ids": sorted({item[0]["notice_id"] for item in latest})})
    return {"status": status, "validation_eligible": not bool(uncleared),
            "notices": [copy.deepcopy(item[0]) for item in available], "information_gaps": gaps}
