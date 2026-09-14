"""Apply explicit official month-precision reviews after canonical finalization.

Raw observations are retained. Only listed publication versions/events change;
acceptance dates, other URLs and first-seen timestamps are never rewritten.
Call on every ingest AFTER finalize_facts and BEFORE save/export so incoming
legacy metadata cannot restore unsupported day precision. No network or writes.
"""
from __future__ import annotations

import copy
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

try:
    from catalog_store import fingerprint, read_table
except ModuleNotFoundError:
    from scripts.catalog_store import fingerprint, read_table

MONTH_NAMES = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")


def _url(value):
    parsed = urlsplit(value or "")
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Date review requires a public official URL")
    return parsed._replace(fragment="").geturl().rstrip("/")


def review_source_id(review):
    return "source:date-review:" + fingerprint(review["review_id"])[:24]


def _append_unique(rows, row):
    if fingerprint(row) not in {fingerprint(previous) for previous in rows}:
        rows.append(row)


def _validate(payload, incoming):
    review = copy.deepcopy(incoming)
    required = {"review_id", "work_id", "source_url", "source_record_ids", "publication_month", "source_excerpt", "review_status", "verified_by", "verified_at", "reason", "manifestation_ids", "event_ids", "superseded_date_values"}
    if set(review) != required or review.get("review_status") != "verified" or not all(isinstance(review.get(key), str) and review[key].strip() for key in required - {"source_record_ids", "manifestation_ids", "event_ids", "superseded_date_values"}):
        raise ValueError("Invalid date review fields or status")
    if not re.fullmatch(r"20\d{2}-(0[1-9]|1[0-2])", review["publication_month"]):
        raise ValueError("Date review must establish a complete publication month")
    year, month = map(int, review["publication_month"].split("-"))
    if f"{MONTH_NAMES[month - 1]} {year}" not in review["source_excerpt"]:
        raise ValueError("Inspected source excerpt must state the reviewed month")
    try:
        checked = datetime.fromisoformat(review["verified_at"].replace("Z", "+00:00"))
        if checked.tzinfo is None or checked.strftime("%Y-%m") < review["publication_month"]:
            raise ValueError()
    except ValueError as exc:
        raise ValueError("Date review needs a timezone-aware, nonfuture observation") from exc
    for key in ["source_record_ids", "manifestation_ids", "event_ids", "superseded_date_values"]:
        values = review[key]
        if not isinstance(values, list) or not values or any(not isinstance(item, str) or not item for item in values) or len(values) != len(set(values)):
            raise ValueError("Date review selectors must be nonempty unique lists")
    if any(not re.fullmatch(review["publication_month"] + r"-\d{2}", value) for value in review["superseded_date_values"]):
        raise ValueError("A month-precision correction cannot move a work between months")
    aliases = {row["alias"]: row["work_id"] for row in payload.get("work-aliases", [])}
    review["work_id"] = aliases.get(review["work_id"], review["work_id"])
    works = {row["work_id"]: row for row in payload["works"]}
    sources = {row["source_record_id"]: row for row in payload["source-records"]}
    work = works.get(review["work_id"])
    if not work or not set(review["source_record_ids"]) <= set(work.get("source_record_ids", [])):
        raise ValueError("Date source does not belong to the reviewed work")
    if any(identifier not in sources or _url(sources[identifier].get("url")) != _url(review["source_url"]) for identifier in review["source_record_ids"]):
        raise ValueError("Date source URL mismatch")
    for table, key, selected in [("manifestations", "manifestation_id", "manifestation_ids"), ("evidence-events", "event_id", "event_ids")]:
        rows = [row for row in payload.get(table, []) if row.get(key) in review[selected]]
        if {row[key] for row in rows} != set(review[selected]):
            raise ValueError("Date review references a missing publication target")
        for row in rows:
            if row.get("work_id") != work["work_id"] or _url(row.get("url")) != _url(review["source_url"]):
                raise ValueError("Date review target identity or URL mismatch")
            if (table == "manifestations" and (row.get("kind") != "technical_report" or row.get("peer_reviewed"))) or (table == "evidence-events" and row.get("event_type") != "technical_report"):
                raise ValueError("Date review cannot alter review decisions or unrelated output types")
            # A new, independently changed publication date requires a new review.
            if row.get("published_at") not in {*review["superseded_date_values"], review["publication_month"] + "-01"}:
                raise ValueError("Publication date changed beyond this review's approved scope")
    return review, work, sources


def apply_date_reviews(payload: dict, reviews: list[dict]) -> dict:
    """Mutate only approved fields after validating the complete batch."""
    prepared = [_validate(payload, review) for review in reviews]
    seen_ids = {}
    for review, _, _ in prepared:
        sid = review_source_id(review)
        if sid in seen_ids and seen_ids[sid] != fingerprint(review):
            raise ValueError("Conflicting date review IDs")
        seen_ids[sid] = fingerprint(review)
        existing = next((row for row in payload["source-records"] if row["source_record_id"] == sid), None)
        if existing and existing.get("payload_hash") != fingerprint(review):
            raise ValueError("An archived date review changed; create an explicit new revision")
    for review, work, sources in prepared:
        sid, date = review_source_id(review), review["publication_month"] + "-01"
        # Also supersede freshly re-collected copies of the SAME old date/URL,
        # not different publication dates, URLs or version identifiers.
        replaced_ids = set(review["source_record_ids"])
        replaced_ids.update(identifier for identifier in work.get("source_record_ids", []) if identifier in sources and
                            sources[identifier].get("source_type") != "official_publication_date_review" and
                            sources[identifier].get("url", "").rstrip("/") == review["source_url"].rstrip("/") and
                            sources[identifier].get("published_at") in review["superseded_date_values"])
        archived = {"source_record_id": sid, "source_type": "official_publication_date_review", "url": review["source_url"],
                    "published_at": date, "date_precision": "month", "retrieved_at": review["verified_at"],
                    "source_excerpt": review["source_excerpt"], "review_status": "verified", "reviewed_by": review["verified_by"],
                    "review_id": review["review_id"], "reason": review["reason"], "payload_hash": fingerprint(review),
                    "raw_ref": "data/date-evidence-additions.jsonl#" + review["review_id"],
                    "supersedes_source_record_ids": sorted(review["source_record_ids"]),
                    "superseded_date_values": review["superseded_date_values"]}
        if sid not in sources:
            payload["source-records"].append(archived)
        for identifier in sorted(replaced_ids):
            source = sources[identifier]
            marker = {"source_record_id": sid, "review_id": review["review_id"], "fields": ["published_at", "date_precision"],
                      "reason": "official_source_supports_month_not_day", "reviewed_at": review["verified_at"]}
            if source.get("date_supersession") and source["date_supersession"].get("source_record_id") != sid:
                _append_unique(source.setdefault("date_supersession_history", []), source["date_supersession"])
            source["date_supersession"] = marker
        work["source_record_ids"] = sorted(set(work.get("source_record_ids", [])) | {sid})
        def provenance(field):
            _append_unique(payload.setdefault("field-provenance", []), {"work_id": work["work_id"], "field": field,
                "source_record_id": sid, "observed_at": review["verified_at"], "basis": "official_month_precision_review", "review_id": review["review_id"]})
        def history(row, field, precision_field):
            if row.get(field) != date or row.get(precision_field) != "month":
                _append_unique(row.setdefault("date_history", []), {"field": field, "previous_date": row.get(field),
                    "previous_precision": row.get(precision_field), "date": date, "date_precision": "month", "source_record_id": sid,
                    "review_id": review["review_id"], "reviewed_at": review["verified_at"], "reason": review["reason"]})
                row[field], row[precision_field] = date, "month"
        owner = work.get("first_public_date_source")
        # A separately evidenced earlier version keeps its canonical date.
        if work.get("first_public_date") in {*review["superseded_date_values"], date} and (owner is None or owner in replaced_ids or owner == sid):
            history(work, "first_public_date", "first_public_date_precision")
            work["first_public_date_source"] = sid
            work["date_authority"] = "reviewed_official_month"
            provenance("first_public_date")
            provenance("first_public_date_precision")
            # Keep the incoming-source hashes unchanged: this is a curated edit,
            # not the old automatic value becoming newly writable.
        for row in payload.get("manifestations", []):
            if row.get("manifestation_id") not in review["manifestation_ids"]:
                continue
            previous_precision = row.get("date_precision")
            history(row, "published_at", "date_precision")
            if row.get("public_at") in review["superseded_date_values"]:
                row["date_precision"] = previous_precision
                history(row, "public_at", "date_precision")
            row["date_source_record_id"] = sid
            # Citation ownership now points to the reviewed publication date;
            # the prior source remains in work.sources and history/provenance.
            row.setdefault("original_source_record_id", row.get("source_record_id"))
            row["source_record_id"] = sid
            provenance(f"manifestations.{row['manifestation_id']}.published_at")
        for row in payload.get("evidence-events", []):
            if row.get("event_id") not in review["event_ids"]:
                continue
            previous_precision = row.get("date_precision")
            if row.get("occurred_at") in review["superseded_date_values"]:
                history(row, "occurred_at", "date_precision")
            if row.get("published_at") != date:
                row["date_precision"] = previous_precision
            history(row, "published_at", "date_precision")
            row["date_source_record_id"] = sid
            row["source_record_ids"] = sorted(set(row.get("source_record_ids", [])) | {sid})
            provenance(f"evidence-events.{row['event_id']}.published_at")
            provenance(f"evidence-events.{row['event_id']}.occurred_at")
        for identifier in sorted(replaced_ids):
            provenance(f"source-records.{identifier}.date_supersession")
    return payload


def ingest_date_reviews(payload: dict, data: Path) -> dict:
    return apply_date_reviews(payload, read_table(data, "date-evidence-additions"))
