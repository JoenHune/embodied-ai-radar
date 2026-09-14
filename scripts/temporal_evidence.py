"""Pure, conservative evidence views at an Asia/Shanghai calendar cutoff.

No current work-level Boolean is backdated to its preprint date. An undated
peer decision, asset release or experimental claim remains unknown in a
historical view. Date-only source values retain their original calendar day.
"""
from __future__ import annotations

import calendar
import re
from datetime import date, datetime
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

ZONE = ZoneInfo("Asia/Shanghai")
ASSET_FLAGS = {"code": "open_code", "data": "open_data", "dataset": "open_data", "model": "open_model", "benchmark": "benchmark"}
CAPABILITY_FLAGS = {"real_robot", "cross_embodiment", "long_horizon", "deployment", *ASSET_FLAGS.values()}
VERIFIED_ASSET_STATES = {"verified_repository", "verified_asset_release", "official_release", "published", "released"}


def cutoff_day(cutoff: str | date) -> date:
    if isinstance(cutoff, datetime):
        return cutoff.astimezone(ZONE).date() if cutoff.tzinfo else cutoff.date()
    if isinstance(cutoff, date):
        return cutoff
    if re.fullmatch(r"\d{4}-\d{2}", cutoff):
        year, month = map(int, cutoff.split("-"))
        return date(year, month, calendar.monthrange(year, month)[1])
    result = public_day(cutoff)
    if result is None:
        raise ValueError("A known calendar cutoff is required")
    return result


def public_day(value: str | None, precision: str | None = None) -> date | None:
    """Latest possible day of an exact/month-precision public date.

    Month-only evidence is usable at month end, never at a guessed first day.
    A known year is conservatively available only at year end; explicit
    unknown precision is never a dated validation.
    """
    if not isinstance(value, str) or precision in {"unknown", "undated"}:
        return None
    try:
        if precision == "year" or re.fullmatch(r"\d{4}", value):
            return date(int(value[:4]), 12, 31)
        if precision == "month" or re.fullmatch(r"\d{4}-\d{2}", value):
            year, month = map(int, value[:7].split("-"))
            return date(year, month, calendar.monthrange(year, month)[1])
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return date.fromisoformat(value)
        instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
        # A timestamp without an offset has unknown timezone; do not pretend
        # its UTC or local interpretation is known.
        return instant.astimezone(ZONE).date() if instant.tzinfo else None
    except (ValueError, TypeError):
        return None


def public_by(value: str | None, cutoff: str | date, precision: str | None = None) -> bool:
    when = public_day(value, precision)
    return bool(when and when <= cutoff_day(cutoff))


def _source_map(source_records) -> dict:
    if isinstance(source_records, dict):
        return source_records
    return {row["source_record_id"]: row for row in (source_records or [])}


def _linked_source(record: dict, work: dict, sources: dict | None = None) -> bool:
    url = record.get("source_url") or record.get("url") or ""
    parts = urlparse(url)
    identifiers = record.get("source_record_ids") or ([record["source_record_id"]] if record.get("source_record_id") else [])
    if parts.scheme not in {"http", "https"} or not parts.netloc or not identifiers:
        return False
    work_sources = set(work.get("source_record_ids", []))
    if not set(identifiers) <= work_sources:
        return False
    if sources is not None and (not set(identifiers) <= sources.keys() or not any((sources[s].get("url") or "").rstrip("/") == url.rstrip("/") for s in identifiers)):
        return False
    return True


def evidence_as_of(work: dict, manifestations: list[dict], cutoff: str | date, source_records=None) -> dict:
    """Return only date-supported validation state; never mutate inputs.

    Experimental flags use ``evidence_flag_evidence`` records (or a
    ``evidence_flag_provenance`` mapping) with flag/value, review_status,
    source_url/source_record_ids and public_at. Verified asset manifestations
    may independently prove an open asset. Bare legacy flags are reported as
    unverified, not silently used to upgrade evidence maturity.
    """
    until = cutoff_day(cutoff)
    sources = _source_map(source_records) if source_records is not None else None
    available, peer_versions, gaps = [], [], []
    flags = {key: False for key in CAPABILITY_FLAGS | set(work.get("evidence_flags", {}))}
    flag_evidence = {key: [] for key in flags}
    first_day = public_day(work.get("first_public_date"), work.get("first_public_date_precision"))
    work_public = bool(first_day and first_day <= until)
    for version in manifestations:
        if version.get("evidence_layer") == "S":
            continue
        if version.get("work_id") not in {None, work.get("work_id")}:
            continue
        precision = version.get("date_precision")
        released = public_day(version.get("public_at") or version.get("published_at"), precision)
        decision_only = str(version.get("publication_status") or version.get("status") or "").startswith("accepted")
        accepted = public_day(version.get("accepted_at"), version.get("accepted_date_precision", precision if decision_only else None))
        peer = bool(version.get("peer_reviewed") and version.get("kind") in {"conference", "journal"})
        peer_day = accepted if decision_only else min([day for day in [accepted, released] if day], default=None)
        available_day = peer_day if decision_only else released
        if peer and peer_day and peer_day <= until:
            peer_versions.append({**version, "evidence_available_on": peer_day.isoformat()})
            available_day = min([day for day in [available_day, peer_day] if day])
        elif peer and peer_day is None:
            gaps.append({"reason": "peer_review_date_unknown", "manifestation_id": version.get("manifestation_id")})
        if available_day is None:
            if version.get("kind") in ASSET_FLAGS:
                gaps.append({"reason": "asset_release_date_unknown", "manifestation_id": version.get("manifestation_id")})
            continue
        if available_day > until:
            continue
        available.append({**version, "peer_reviewed": peer and bool(peer_day and peer_day <= until), "evidence_available_on": available_day.isoformat()})
        flag = ASSET_FLAGS.get(version.get("kind"))
        if flag and version.get("status") in VERIFIED_ASSET_STATES and version.get("url"):
            flags[flag] = True
            flag_evidence[flag].append(version.get("manifestation_id"))
    records = list(work.get("evidence_flag_evidence", []))
    for flag, entries in (work.get("evidence_flag_provenance") or {}).items():
        for entry in entries if isinstance(entries, list) else [entries]:
            if isinstance(entry, dict):
                records.append({**entry, "flag": flag})
    for record in records:
        if not isinstance(record, dict):
            continue
        flag = record.get("flag")
        if flag not in flags or record.get("value", True) is not True or record.get("review_status") != "verified":
            continue
        if _linked_source(record, work, sources) and public_by(record.get("public_at"), until, record.get("public_at_precision", record.get("date_precision"))):
            flags[flag] = True
            flag_evidence[flag].append(record.get("record_id") or record.get("source_url"))
    replication_ids = []
    for record in work.get("independent_replication_evidence", []):
        if isinstance(record, dict) and record.get("review_status") == "verified" and record.get("cross_platform") is True and record.get("independent_team") is True and _linked_source(record, work, sources) and public_by(record.get("public_at"), until, record.get("public_at_precision", record.get("date_precision"))):
            replication_ids.append(record.get("record_id") or record["source_url"])
    unknown_flags = sorted(key for key, value in work.get("evidence_flags", {}).items() if value and not flags.get(key))
    if unknown_flags:
        gaps.append({"reason": "current_flags_have_no_available_dated_proof", "flags": unknown_flags})
    if work.get("independent_replication_evidence_ids") and not replication_ids:
        gaps.append({"reason": "independent_replication_has_no_available_dated_proof"})
    has_peer = bool(peer_versions)
    company = any(v.get("kind") in {"technical_report", "demo"} for v in available)
    grade = "E4" if has_peer and replication_ids and flags.get("real_robot") else "E3" if has_peer or replication_ids else "E1" if company else "E2" if any(flags.get(key) for key in ["real_robot", "open_code", "open_data", "open_model", "benchmark", "deployment"]) else "E0"
    result = {"as_of": until.isoformat(), "basis": "public_evidence_available_by_calendar_cutoff", "work_public": work_public,
            "evidence_grade": grade, "evidence_flags": flags, "strict_peer_reviewed": has_peer,
            "manifestations": available, "available_manifestation_ids": [v.get("manifestation_id") for v in available if v.get("manifestation_id")],
            "peer_reviewed_manifestations": peer_versions, "flag_evidence_ids": flag_evidence,
            "independent_replication_evidence_ids": replication_ids, "unverified_evidence_flags": unknown_flags, "information_gaps": gaps}
    if work.get("research_status_notices"):
        from research_status import research_status_as_of
        status = research_status_as_of(work, until, sources)
        # A future notice must not alter an earlier evidence packet or pretend
        # that the later withdrawal was already known in that month.
        if status["notices"] or status["information_gaps"]:
            result["research_status"] = status
            result["validation_eligible"] = status["validation_eligible"]
            if not status["validation_eligible"]:
                result["reported_validation_before_status_gate"] = {
                    key: result[key] for key in ("evidence_grade", "evidence_flags", "strict_peer_reviewed",
                                                "peer_reviewed_manifestations", "flag_evidence_ids", "independent_replication_evidence_ids")}
                # A withdrawal invalidates reliance on results, not the fact
                # that a public repository/model/data release exists.
                asset_flags = set(ASSET_FLAGS.values())
                result.update(evidence_grade="E0", strict_peer_reviewed=False,
                              evidence_flags={key: value if key in asset_flags else False for key, value in flags.items()},
                              flag_evidence_ids={key: value if key in asset_flags else [] for key, value in flag_evidence.items()},
                              peer_reviewed_manifestations=[], independent_replication_evidence_ids=[])
                result["information_gaps"].append({"reason": "research_status_blocks_validation", "status": status["status"],
                                                   "notice_ids": [row["notice_id"] for row in status["notices"]]})
    return result
