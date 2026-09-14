"""Pure arXiv metadata snapshots: never backdate revised text to submission.

Descriptive arXiv metadata (including abstracts) is CC0 under the official API
terms: https://info.arxiv.org/help/api/tou.html. This module stores no PDF/full
paper content. Callers provide already-loaded raw payloads; no network or IO.
"""
from __future__ import annotations

import calendar
import copy
import hashlib
import json
import re
from datetime import datetime, time, timezone
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

ZONE = ZoneInfo("Asia/Shanghai")


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _arxiv(value):
    found = re.search(r"(?<!\d)(\d{4}\.\d{4,5})(v[1-9]\d*)?(?!\d)", str(value or ""))
    return (found.group(1), found.group(2)) if found else (None, None)


def _upper(value, precision=None):
    if not value or precision == "unknown":
        return None
    try:
        if re.fullmatch(r"\d{4}-\d{2}", value) or precision == "month":
            year, month = map(int, value[:7].split("-"))
            return datetime(year, month, calendar.monthrange(year, month)[1], 23, 59, 59, 999999, tzinfo=ZONE)
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return datetime.combine(datetime.strptime(value, "%Y-%m-%d").date(), time.max, ZONE)
        when = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return when if when.tzinfo is not None else None
    except (ValueError, TypeError):
        return None


def _time(value, precision=None):
    upper = _upper(value, precision)
    if upper is None:
        return None, "unknown"
    if len(value) == 10:
        return value, "day"
    if len(value) == 7 or precision == "month":
        return value[:7], "month"
    return upper.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"), "second"


def _lower(value, precision=None):
    upper = _upper(value, precision)
    if upper is None:
        return None
    if len(value) == 7 or precision == "month":
        return upper.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if len(value) == 10:
        return upper.replace(hour=0, minute=0, second=0, microsecond=0)
    return upper


def _version(payload):
    for field in ["version", "arxiv_version_id", "pdf_url", "arxiv_url"]:
        value = payload.get(field)
        if isinstance(value, int) and value > 0:
            return f"v{value}"
        found = re.search(r"(v[1-9]\d*)(?:\.pdf)?$", str(value or ""))
        if found:
            return found.group(1)
    return None


def snapshot_from_payload(work, source, payload, *, basis="source_bound_metadata"):
    """No published-date fallback for a current v2 or unknown revision."""
    version = _version(payload)
    published, pub_precision = _time(payload.get("submitted_at") or payload.get("first_submitted") or payload.get("published"), payload.get("submitted_at_precision"))
    updated, precision = _time(payload.get("updated_at") or payload.get("updated"), payload.get("updated_at_precision"))
    available, temporal_basis = updated, "current_metadata_updated_at"
    if version == "v1" and published is not None and updated == published:
        available, precision, temporal_basis = published, pub_precision, "explicit_v1_published_equals_updated"
    if available is None:
        # An archived observation establishes presence by retrieval, not a
        # fabricated version publication date. Unknown remains unknown.
        available, precision = _time(source.get("retrieved_at") or source.get("recorded_at"))
        temporal_basis = "archived_observation_only" if available else "metadata_date_unknown"
    if published and updated and _upper(updated, precision) < _lower(published, pub_precision):
        raise ValueError("metadata_update_predates_submission")
    title, abstract, authors = payload.get("title"), payload.get("abstract"), payload.get("authors")
    if not isinstance(title, str) or not title.strip() or not isinstance(abstract, str) or not isinstance(authors, list) or any(not isinstance(author, str) for author in authors):
        raise ValueError("metadata_text_fields_missing")
    text = {"title": title, "abstract": abstract, "authors": authors}
    row = {"work_id": work["work_id"], "source_record_id": source["source_record_id"], "version": version,
           **copy.deepcopy(text), "available_at": available, "date_precision": precision,
           "source_url": source.get("url"), "content_digest": digest(text), "basis": basis + ":" + temporal_basis}
    row["snapshot_id"] = "text-snapshot:" + digest(row)[:24]
    return row


def _pointer(raw_ref, payloads):
    if raw_ref in payloads:
        return payloads[raw_ref]
    path, _, fragment = raw_ref.partition("#")
    value = payloads.get(path)
    if value is None:
        return None
    try:
        for token in fragment.lstrip("/").split("/") if fragment else []:
            token = token.replace("~1", "/").replace("~0", "~")
            value = value[int(token)] if isinstance(value, list) else value[token]
        return value
    except (KeyError, IndexError, ValueError, TypeError):
        return None


def build_versioned_text(works, source_records, *, raw_payloads=None, preprints=None, additions=None):
    """Resolve source archives by hash, not mutable array offsets or title guesses.

    raw_payloads: raw_ref -> original row OR filename -> original JSON envelope.
    Embedded SourceRecord.raw_payload is supported. preprints fallback requires
    its COMPLETE payload hash to equal the source record's immutable hash.
    """
    sources = source_records if isinstance(source_records, dict) else {row["source_record_id"]: row for row in source_records}
    originals = works.values() if isinstance(works, dict) else works
    preprint_hashes = {digest(row): row for row in (preprints or [])}
    snapshots, issues = {}, []
    additions_by_work = {}
    for row in additions or []:
        additions_by_work.setdefault(row.get("work_id"), []).append(row)
    for work in originals:
        cached = {row["source_record_id"] for row in additions_by_work.get(work["work_id"], []) if not validate_snapshot(row, work, sources)}
        work_arxiv = _arxiv((work.get("identifiers") or {}).get("arxiv") or work["work_id"])[0]
        for sid in work.get("source_record_ids", []):
            source = sources.get(sid)
            if not source:
                continue
            if sid in cached and not source.get("archived_text_snapshot"):
                continue
            archived = source.get("archived_text_snapshot")
            if isinstance(archived, dict):
                errors = validate_snapshot(archived, work, sources)
                if not errors:
                    snapshots[archived["snapshot_id"]] = copy.deepcopy(archived)
                else:
                    issues.append({"work_id": work["work_id"], "source_record_id": sid, "reason": ",".join(errors)})
                continue
            source_arxiv = _arxiv(source.get("url") or source.get("source_id"))[0]
            if not source_arxiv or (work_arxiv and source_arxiv != work_arxiv):
                continue
            candidate = source.get("raw_payload")
            if candidate is None:
                candidate = _pointer(source.get("raw_ref") or "", raw_payloads or {})
            if not isinstance(candidate, dict) or (source.get("payload_hash") and digest(candidate) != source["payload_hash"]):
                candidate = preprint_hashes.get(source.get("payload_hash"))
            if not isinstance(candidate, dict):
                issues.append({"work_id": work["work_id"], "source_record_id": sid, "reason": "raw_payload_missing_or_hash_changed"})
                continue
            # Without a hash, only an explicitly embedded archived payload is
            # trusted. A raw_ref alone is a location, not an immutable archive.
            if not source.get("payload_hash") and source.get("raw_payload") is not candidate:
                issues.append({"work_id": work["work_id"], "source_record_id": sid, "reason": "unhashed_mutable_raw_reference"})
                continue
            candidate_arxiv = _arxiv(candidate.get("arxiv_id") or candidate.get("arxiv_url") or candidate.get("preprint_id"))[0]
            if candidate_arxiv != source_arxiv:
                issues.append({"work_id": work["work_id"], "source_record_id": sid, "reason": "raw_payload_identity_mismatch"})
                continue
            for text_payload in [candidate, *candidate.get("metadata_history", [])]:
                try:
                    history_arxiv = _arxiv(text_payload.get("arxiv_id") or text_payload.get("arxiv_url") or text_payload.get("preprint_id"))[0]
                    if history_arxiv != source_arxiv:
                        raise ValueError("historical_payload_identity_mismatch")
                    row = snapshot_from_payload(work, source, text_payload)
                    snapshots[row["snapshot_id"]] = row
                except (ValueError, TypeError) as exc:
                    issues.append({"work_id": work["work_id"], "source_record_id": sid, "reason": str(exc)})
        for row in additions_by_work.get(work["work_id"], []):
            errors = validate_snapshot(row, work, sources)
            if errors:
                issues.append({"work_id": work["work_id"], "source_record_id": row.get("source_record_id"), "reason": ",".join(errors)})
            else:
                snapshots[row["snapshot_id"]] = copy.deepcopy(row)
    return {"snapshots": [snapshots[key] for key in sorted(snapshots)], "issues": issues}


def register_versioned_text_additions(payload, additions):
    """Pure-data archive registration; caller controls persistence/ingestion."""
    result = copy.deepcopy(payload)
    works = {row["work_id"]: row for row in result["works"]}
    sources = {row["source_record_id"]: row for row in result["source-records"]}
    for row in additions:
        work = works.get(row.get("work_id"))
        if not work:
            raise ValueError("versioned_text_work_unknown")
        parsed = urlsplit(row.get("source_url") or "")
        arxiv, version = _arxiv(parsed.path)
        canonical = _arxiv((work.get("identifiers") or {}).get("arxiv") or work["work_id"])[0]
        if parsed.scheme != "https" or parsed.hostname != "arxiv.org" or parsed.username or parsed.password or not parsed.path.startswith(("/abs/", "/html/")) or arxiv != canonical or version != row.get("version") or not version:
            raise ValueError("versioned_text_requires_matching_official_version_url")
        if _upper(row.get("verified_at")) is None or not row.get("verification_basis"):
            raise ValueError("versioned_text_requires_documented_source_check")
        own = {**work, "source_record_ids": [*work.get("source_record_ids", []), row.get("source_record_id")]}
        errors = validate_snapshot(row, own)
        if errors:
            raise ValueError(",".join(errors))
        source = {"source_record_id": row["source_record_id"], "source_type": "official_arxiv_version_metadata", "url": row["source_url"],
                  "published_at": row["available_at"], "date_precision": row["date_precision"], "retrieved_at": row["verified_at"],
                  "payload_hash": digest(row), "raw_ref": "data/versioned-text-additions.jsonl#" + row["snapshot_id"],
                  "version": version, "archived_text_snapshot": copy.deepcopy(row), "metadata_license": "CC0-1.0"}
        if row["source_record_id"] in sources and any(sources[row["source_record_id"]].get(key) != value for key, value in source.items()):
            raise ValueError("versioned_text_archive_conflict")
        if row["source_record_id"] not in sources:
            result["source-records"].append(source)
            sources[row["source_record_id"]] = source
        work["source_record_ids"] = sorted(set(work.get("source_record_ids", [])) | {row["source_record_id"]})
        for field in ["title", "abstract", "authors"]:
            proof = {"work_id": work["work_id"], "field": "versioned_text." + version + "." + field, "source_record_id": row["source_record_id"], "observed_at": row["verified_at"], "basis": row["verification_basis"]}
            if proof not in result.setdefault("field-provenance", []):
                result["field-provenance"].append(proof)
    return result


def validate_snapshot(row, work, sources=None):
    required = {"snapshot_id", "work_id", "source_record_id", "version", "title", "abstract", "authors", "available_at", "date_precision", "source_url", "content_digest", "basis"}
    if not required <= set(row) or row.get("work_id") != work.get("work_id"):
        return ["snapshot_fields_or_work_invalid"]
    if row["source_record_id"] not in work.get("source_record_ids", []):
        return ["snapshot_source_not_owned"]
    if not isinstance(row["title"], str) or not row["title"].strip() or not isinstance(row["abstract"], str) or not isinstance(row["authors"], list) or not all(isinstance(item, str) for item in row["authors"]):
        return ["snapshot_text_invalid"]
    if row["content_digest"] != digest({key: row[key] for key in ["title", "abstract", "authors"]}):
        return ["snapshot_content_hash_mismatch"]
    if row["date_precision"] not in {"second", "day", "month", "unknown"} or (row["available_at"] is None) != (row["date_precision"] == "unknown") or (row["available_at"] is not None and _upper(row["available_at"], row["date_precision"]) is None):
        return ["snapshot_date_invalid"]
    if row["version"] is not None and not re.fullmatch(r"v[1-9]\d*", row["version"]):
        return ["snapshot_version_invalid"]
    if sources is not None:
        source = sources.get(row["source_record_id"])
        if not source or source.get("url", "").rstrip("/") != row.get("source_url", "").rstrip("/"):
            return ["snapshot_source_url_mismatch"]
        if source.get("source_type") == "official_arxiv_version_metadata" and (source.get("version") != row["version"] or source.get("published_at") != row["available_at"] or source.get("payload_hash") != digest(row)):
            return ["archived_snapshot_provenance_mismatch"]
        if source.get("text_content_digest") and source["text_content_digest"] != digest({key: row[key] for key in ["title", "abstract"]}):
            return ["archived_text_digest_mismatch"]
    return []


def text_as_of(work, snapshots, cutoff):
    until = _upper(cutoff)
    if until is None:
        raise ValueError("known_cutoff_required")
    empty = {"title": None, "abstract": None, "authors": [], "source_ids": [], "status": "unavailable", "available_at": None, "version": None, "snapshot_ids": []}
    valid = [row for row in snapshots if row.get("work_id") == work["work_id"] and not validate_snapshot(row, work)]
    eligible = [row for row in valid if (when := _upper(row["available_at"], row["date_precision"])) is not None and when <= until]
    if not eligible:
        future = [row["snapshot_id"] for row in valid if _upper(row["available_at"], row["date_precision"]) is not None]
        return {**empty, "status": "retrospective_only" if future else "unavailable", "retrospective_snapshot_ids": future}
    # Fetching an old v1 page after a known v2 release does not make v1 the
    # newest edition. Prefer the newest explicitly identified eligible version;
    # use unversioned observations only when no identified version is available.
    known = [row for row in eligible if row["version"]]
    chosen = max(known or eligible, key=lambda row: (int((row["version"] or "v0")[1:]), _upper(row["available_at"], row["date_precision"])))
    peers = [row for row in eligible if row["version"] == chosen["version"] and _upper(row["available_at"], row["date_precision"]) == _upper(chosen["available_at"], chosen["date_precision"])]
    if len({row["content_digest"] for row in peers}) > 1:
        return {**empty, "status": "conflicting_snapshots", "snapshot_ids": [row["snapshot_id"] for row in peers]}
    return {**{key: copy.deepcopy(chosen[key]) for key in ["title", "abstract", "authors", "available_at", "version"]},
            "date_precision": chosen["date_precision"], "source_ids": sorted({row["source_record_id"] for row in peers}),
            "snapshot_ids": sorted({row["snapshot_id"] for row in peers}), "status": "available" if chosen["version"] else "available_unversioned"}
