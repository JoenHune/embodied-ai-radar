"""Source-comparison holds, separate from publication status or relevance.

A hold is a reviewer's source comparison, not a declaration of misconduct or
independent experimental invalidation. Raw metadata/reading receipts remain
unchanged. The current review clock controls the hold; old paper dates are not
replaced by the time the discrepancy was discovered.
"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator
from catalog_store import fingerprint
from fulltext_reading_reviews import public_audit, timestamp, versioned_read_url
from versioned_text import validate_snapshot

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "config/source-content-conflicts.schema.json").read_text())
PRIVATE = re.compile(r"file://|/Users/|/home/|/private/|\.research/|[A-Za-z]:\\")


def require(value, code):
    if not value:
        raise ValueError("source_content_conflict:" + code)


def conflict_id_for(row):
    identity = {key: row[key] for key in ("work_id", "version")}
    identity["issue_types"] = sorted(row["issue_types"])
    identity["metadata_sources"] = sorted(row["metadata_sources"], key=lambda x: x["snapshot_id"])
    identity["reading_sources"] = sorted(row["reading_sources"], key=lambda x: x["reading_id"])
    return "source-conflict:" + fingerprint(identity)[:24]


def cutoff_time(value):
    text = str(value)
    return timestamp(text + "T23:59:59.999999Z" if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text) else text)


def _safe_text(value):
    require(not PRIVATE.search(value) and all(c.isprintable() or c in "\n\t" for c in value), "private_or_control_text")


def _unique(rows, key):
    result = {row[key]: row for row in rows}
    require(len(result) == len(rows), "duplicate_" + key)
    return result


def _metadata_url_matches(url, work, version):
    from collect_hardware_sources import arxiv_identity
    try:
        parsed = urlsplit(str(url))
        expected = arxiv_identity(work.get("identifiers", {}).get("arxiv") or work["work_id"])
        identity = arxiv_identity(url)
        return bool(parsed.scheme == "https" and parsed.hostname in {"arxiv.org", "www.arxiv.org"}
                    and not parsed.username and not parsed.password and parsed.port in {None, 443}
                    and not parsed.query and not parsed.fragment and not PRIVATE.search(str(url))
                    and all(c.isprintable() and not c.isspace() for c in str(url))
                    and expected and identity == (expected[0], version)
                    and parsed.path.rstrip("/") in {f"/abs/{expected[0]}{version}", f"/html/{expected[0]}{version}"})
    except (ValueError, TypeError):
        return False


def build_source_conflicts(records, catalog, readings, observations, as_of):
    """Validate all lineage, then derive the as-of public comparison notices.

    This verifies metadata/hash references, not the semantics of the review.
    Resolutions require explicitly sourced review records, never only a toggle.
    """
    until = cutoff_time(as_of)
    require(isinstance(records, list), "schema_invalid")
    validator = Draft202012Validator(SCHEMA)
    require(all(not list(validator.iter_errors(row)) for row in records), "schema_invalid")
    works = _unique(catalog.get("works", []), "work_id")
    snapshots = _unique(catalog.get("text-snapshots", []), "snapshot_id")
    sources = _unique(catalog.get("source-records", []), "source_record_id")
    # Audit even future receipts/holds; do not hide malformed history by date.
    receipts = _unique(public_audit(readings, catalog, observations, "9999-12-31")["records"], "reading_id") if records else {}
    _unique(records, "conflict_id")
    output = []
    for row in records:
        require(row["conflict_id"] == conflict_id_for(row), "id_mismatch")
        work = works.get(row["work_id"])
        require(work is not None, "unknown_work")
        detected = timestamp(row["detected_at"])
        for text in [row["summary_zh"], *row["limitations_zh"]]:
            _safe_text(text)
        metadata, reading_views = [], []
        require(len({x["snapshot_id"] for x in row["metadata_sources"]}) == len(row["metadata_sources"]), "duplicate_snapshot")
        require(len({x["reading_id"] for x in row["reading_sources"]}) == len(row["reading_sources"]), "duplicate_reading")
        for proof in row["metadata_sources"]:
            item = snapshots.get(proof["snapshot_id"])
            require(item is not None and item["work_id"] == row["work_id"] and item["version"] == row["version"], "metadata_identity_mismatch")
            require(not validate_snapshot(item, work, sources), "metadata_snapshot_invalid")
            require(_metadata_url_matches(item.get("source_url"), work, row["version"]), "metadata_source_url_invalid")
            require(item["content_digest"] == proof["content_digest"], "metadata_digest_mismatch")
            metadata.append({key: copy.deepcopy(item.get(key)) for key in ("snapshot_id", "source_record_id", "source_url", "available_at", "date_precision", "content_digest")})
        for proof in row["reading_sources"]:
            item = receipts.get(proof["reading_id"])
            require(item is not None and item["work_id"] == row["work_id"] and item["version"] == row["version"], "reading_identity_mismatch")
            require(fingerprint(item) == proof["reading_digest"], "reading_digest_mismatch")
            require(timestamp(item["read_completed_at"]) <= detected, "reading_after_detection")
            reading_views.append({**{key: copy.deepcopy(item[key]) for key in ("reading_id", "raw_sha256", "article_text_sha256", "observed_at", "read_completed_at")},
                                  "source_url": versioned_read_url(item["source_url"], item["version"])})
        resolution = row["resolution"]
        require((row["status"] == "resolved") == (resolution is not None), "resolution_required")
        effective_status = "open"
        if resolution is not None:
            when = timestamp(resolution["reviewed_at"])
            require(when > detected, "resolution_not_later")
            _safe_text(resolution["note_zh"])
            owned = set(work.get("source_record_ids", []))
            for sid in resolution["source_record_ids"]:
                require(sid in sources and sid in owned, "resolution_source_not_owned")
                require(_metadata_url_matches(sources[sid].get("url"), work, row["version"]), "resolution_source_version_mismatch")
            for rid in resolution["reading_ids"]:
                receipt = receipts.get(rid)
                require(receipt is not None and receipt["work_id"] == row["work_id"], "resolution_reading_not_owned")
                require(timestamp(receipt["read_completed_at"]) <= when, "resolution_before_reading")
                require(receipt["version"] == row["version"], "resolution_reading_version_mismatch")
            if when <= until:
                effective_status = "resolved"
        if detected > until:
            continue
        notice = {key: copy.deepcopy(row[key]) for key in ("conflict_id", "work_id", "version", "detected_at", "reviewer_kind", "issue_types", "summary_zh", "limitations_zh")}
        notice.update(status=effective_status, experimental_use="hold" if effective_status == "open" else "released",
                      source_urls=sorted({x["source_url"] for x in metadata + reading_views}),
                      metadata_sources=metadata, reading_sources=reading_views,
                      resolution=copy.deepcopy(resolution) if effective_status == "resolved" else None,
                      assurance="source_comparison_review_not_publication_status_or_independent_validation")
        output.append(notice)
    return sorted(output, key=lambda x: (x["work_id"], x["version"], x["conflict_id"]))


def load_source_conflicts(catalog, data_directory, as_of):
    data = Path(data_directory)
    ledger = data / "editorial/source-content-conflicts.jsonl"
    if not ledger.exists():
        require(not ledger.is_symlink(), "unsafe_ledger")
        return []  # An absent optional ledger means no registered comparisons.
    def read(path):
        require(path.is_file() and not path.is_symlink(), "regular_metadata_file_required")
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    records = read(ledger)
    return build_source_conflicts(records, catalog, read(data / "hardware-review/fulltext-readings.jsonl"),
                                  read(data / "hardware-review/source-observations.jsonl"), as_of)


def conflicts_for_work(conflicts, work_id, version=None, *, active_only=False):
    return [copy.deepcopy(row) for row in conflicts if row["work_id"] == work_id
            and (version is None or row["version"] == version)
            and (not active_only or row["experimental_use"] == "hold")]


def gate_editorial_work(work, conflicts):
    """Keep selection/count/grade metadata; withhold disputed experimental text."""
    holds = conflicts_for_work(conflicts, work["work_id"], work.get("text_version"), active_only=True)
    if not holds or work.get("text_version") is None:
        return work
    result = copy.deepcopy(work)
    result.update(source_conflicts=holds, experimental_text_available=False, text_status="source_content_conflict")
    # Keep the abstract here for stable selection priority. The packet builder
    # clears disputed prose AFTER sampling; it cannot seed an LLM statement.
    return result


def signal_record_is_held(work, record, sources=None):
    """Withhold disputed source proof, without removing topical work counts.

    An unversioned signal cannot escape a known work/version conflict by
    omitting its edition. Explicit unrelated editions remain eligible.
    """
    holds = [row for row in work.get("source_conflicts", []) if row.get("experimental_use") == "hold"]
    if not holds:
        return False
    from collect_hardware_sources import arxiv_identity
    identity = arxiv_identity(record.get("source_url"))
    versions = {identity[1]} if identity and identity[1] else set()
    for sid in record.get("source_record_ids", []):
        source = (sources or {}).get(sid, {})
        value = source.get("version")
        if isinstance(value, str) and re.fullmatch(r"v[1-9]\d*", value):
            versions.add(value)
    if not versions:
        return True
    return any(row["version"] in versions for row in holds)
