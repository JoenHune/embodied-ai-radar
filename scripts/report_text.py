"""Pure registration/selection of short, copyright-limited report excerpts.

This is NOT the arXiv metadata protocol. No company report acquires CC0 rights,
peer review, a human semantic review, or an earlier publication event here.
The trust boundary is an independently verified SourceRecord attestation,
already registered by the caller after checking capture/archive artifacts.
An addition cannot supply its own attestation or claim an earlier capture.

Offsets are Python Unicode character offsets into the entity-decoded source
representation identified by content_sha256. Only short excerpts are public;
the complete representation stays in the separate archive verifier's memory.
"""
from __future__ import annotations

import calendar
import copy
import hashlib
import json
import re
from datetime import datetime, time
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from jsonschema import Draft202012Validator, FormatChecker

ZONE = ZoneInfo("Asia/Shanghai")
SCHEMA = json.loads((Path(__file__).resolve().parents[1] / "config/report-text.schema.json").read_text())
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())
BINDINGS = ("report_url", "source_url", "report_published_at", "report_date_precision", "captured_at",
            "available_at", "date_precision", "content_sha256", "excerpt_digest", "verified_by", "verified_at")
ARCHIVE_FIELDS = {"commit", "path", "blob_sha1", "archive_status_sha256", "archive_source_record_id",
                  "archive_content_sha256", "archive_captured_at", "deployment_url", "run_id", "head_sha",
                  "deploy_completed_at", "deployment_proof_sha256", "selector", "attribute",
                  "entity_unescape_passes", "extracted_text_sha256"}


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def sha256_text(value):
    return hashlib.sha256(value.encode()).hexdigest()


def snapshot_id_for(row):
    return "report-text:" + digest({k: v for k, v in row.items() if k != "snapshot_id"})[:24]


def _map(rows, key):
    return rows if isinstance(rows, dict) else {row[key]: row for row in rows}


def _identities(work):
    return {work["work_id"], *[alias for alias in work.get("aliases", []) if isinstance(alias, str)]}


def canonical_work_for_snapshot(snapshot, works):
    """Preserve snapshot IDs/content when a later identity review merges works."""
    matches = [work for work in (works.values() if isinstance(works, dict) else works)
               if snapshot.get("work_id") in _identities(work)]
    return matches[0] if len(matches) == 1 else None


def _url(value):
    try:
        parts = urlsplit(value)
        if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username or parts.password or any(c.isspace() for c in value):
            return None
        return parts._replace(fragment="").geturl().rstrip("/")
    except (TypeError, ValueError):
        return None


def _bounds(value, precision=None):
    if precision == "unknown":
        return (None, None) if value is None else None
    if not isinstance(value, str):
        return None
    try:
        if precision == "year" or (precision is None and re.fullmatch(r"\d{4}", value)):
            if not re.fullmatch(r"\d{4}(?:-01-01)?", value):
                return None
            year = int(value[:4])
            return datetime(year, 1, 1, tzinfo=ZONE), datetime(year, 12, 31, 23, 59, 59, 999999, tzinfo=ZONE)
        if precision == "month" or (precision is None and re.fullmatch(r"\d{4}-\d{2}", value)):
            if not re.fullmatch(r"\d{4}-\d{2}(?:-01)?", value):
                return None
            year, month = map(int, value[:7].split("-"))
            return datetime(year, month, 1, tzinfo=ZONE), datetime(year, month, calendar.monthrange(year, month)[1], 23, 59, 59, 999999, tzinfo=ZONE)
        if precision == "day" or (precision is None and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value)):
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                return None
            day = datetime.strptime(value, "%Y-%m-%d").date()
            return datetime.combine(day, time.min, ZONE), datetime.combine(day, time.max, ZONE)
        if precision not in {None, "second"} or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T.+(?:Z|[+-]\d{2}:\d{2})", value):
            return None
        when = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return (when, when) if when.tzinfo else None
    except (ValueError, TypeError):
        return None


def _instant(value):
    bounds = _bounds(value, "second")
    return bounds[0] if bounds else None


def excerpt_word_count(text):
    """Conservative lexical budget: numbers count, hyphens split words."""
    return len(re.findall(r"[A-Za-z0-9]+(?:['’][A-Za-z]+)?", text))


def _quota_errors(snapshots):
    by_report = {}
    for row in snapshots:
        if not isinstance(row, dict) or not isinstance(row.get("excerpts"), list):
            continue
        by_report.setdefault(_url(row.get("report_url")), set()).update(ex["text"] for ex in row["excerpts"] if isinstance(ex, dict) and isinstance(ex.get("text"), str))
    errors = []
    for report, texts in by_report.items():
        if sum(excerpt_word_count(text) for text in texts) > 25:
            errors.append({"report_url": report, "reason": "report_excerpt_word_budget_exceeded"})
        if sum(len(re.findall(r"[\u3400-\u9fff]", text)) for text in texts) > 160 or sum(len(text) for text in texts) > 800:
            errors.append({"report_url": report, "reason": "report_excerpt_character_budget_exceeded"})
    return errors


def _number_supported(observation, excerpts):
    # Token boundaries forbid 9 in 59, 5 in .5, or 50 in 1,050. No scaling,
    # percentage conversion, derived arithmetic, or paraphrased numeric facts.
    pattern = re.compile(r"(?<![\w.,+-])[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?!\w|\.\d|,\d)")
    for eid in observation["excerpt_ids"]:
        text = excerpts[eid]["text"]
        for match in pattern.finditer(text):
            if match.group() != observation["value"]:
                continue
            suffix = text[match.end():]
            percent = bool(re.match(r"\s*%", suffix))
            points = bool(re.match(r"\s*(?:percentage points?|pp)\b", suffix, re.I))
            if observation["unit"] == "percentage" and percent:
                return True
            if observation["unit"] == "percentage_points" and points:
                return True
            if observation["unit"] in {"count", "ratio"} and not percent and not points:
                return True
    return False


def _local_errors(row, work=None):
    errors = ["schema:" + "/".join(map(str, error.path)) + ":" + error.message for error in VALIDATOR.iter_errors(row)]
    if errors:
        return errors
    if not _url(row["report_url"]) or not _url(row["source_url"]):
        errors.append("invalid_public_url")
    if row["snapshot_id"] != snapshot_id_for(row):
        errors.append("snapshot_hash_mismatch")
    if row["excerpt_digest"] != digest(row["excerpts"]):
        errors.append("excerpt_digest_mismatch")
    if work is not None:
        if row["work_id"] not in _identities(work):
            errors.append("snapshot_work_mismatch")
        if row["source_record_id"] not in work.get("source_record_ids", []):
            errors.append("snapshot_source_not_owned")
    capture, verified = _instant(row["captured_at"]), _instant(row["verified_at"])
    published = _bounds(row["report_published_at"], row["report_date_precision"])
    available = _bounds(row["available_at"], row["date_precision"])
    if capture is None or verified is None or capture > verified or published is None or available is None:
        errors.append("invalid_temporal_fields")
    else:
        if available[0] and available[0] > capture:
            errors.append("availability_after_capture")
        if published[0] and published[0] > capture:
            errors.append("publication_after_capture")
        if published[0] and available[1] and available[1] < published[0]:
            errors.append("availability_predates_report")
    excerpts = {ex["excerpt_id"]: ex for ex in row["excerpts"]}
    if len(excerpts) != len(row["excerpts"]):
        errors.append("duplicate_excerpt_id")
    for ex in excerpts.values():
        if not ex["text"].strip() or ex["end"] - ex["start"] != len(ex["text"]):
            errors.append("excerpt_offset_length_mismatch")
    ordered = sorted(excerpts.values(), key=lambda ex: (ex["start"], ex["end"]))
    if any(left["end"] > right["start"] for left, right in zip(ordered, ordered[1:])):
        errors.append("overlapping_excerpts")
    if len({ob["id"] for ob in row["observations"]}) != len(row["observations"]):
        errors.append("duplicate_observation_id")
    for ob in row["observations"]:
        if not set(ob["excerpt_ids"]) <= excerpts.keys():
            errors.append("observation_excerpt_unknown")
        elif not _number_supported(ob, excerpts):
            errors.append("observation_number_or_unit_not_in_excerpt")
    errors.extend(error["reason"] for error in _quota_errors([row]))
    return errors


def _attestation_errors(row, work, manifestations, sources):
    errors = []
    manifestation = manifestations.get(row["manifestation_id"])
    if not manifestation or manifestation.get("work_id") not in _identities(work):
        return ["report_manifestation_not_owned"]
    if manifestation.get("kind") != "technical_report" or _url(manifestation.get("url")) != _url(row["report_url"]):
        errors.append("report_manifestation_kind_or_url_mismatch")
    if _bounds(manifestation.get("published_at") or manifestation.get("public_at"), manifestation.get("date_precision", "unknown")) != _bounds(row["report_published_at"], row["report_date_precision"]):
        errors.append("report_manifestation_publication_date_mismatch")
    source = sources.get(row["source_record_id"])
    if not source or _url(source.get("url")) != _url(row["source_url"]):
        return errors + ["report_source_unknown_or_url_mismatch"]
    if source.get("source_type") not in {"official_report_text_archive", "official_report_text_capture"}:
        errors.append("report_source_not_attested_capture")
    attestations = [a for a in source.get("report_text_attestations", []) if isinstance(a, dict) and a.get("attestation_id") == row["attestation_id"]]
    if len(attestations) != 1:
        return errors + ["report_attestation_missing_or_ambiguous"]
    attestation = attestations[0]
    if attestation.get("status") != "verified" or attestation.get("verification_scope") != "source_content":
        errors.append("report_attestation_not_source_verified")
    if any(attestation.get(key) != row[key] for key in BINDINGS):
        errors.append("report_attestation_binding_mismatch")
    if source.get("retrieved_at") != row["captured_at"] or source.get("content_sha256") != row["content_sha256"]:
        errors.append("report_source_capture_or_content_mismatch")
    proof = attestation.get("proof")
    if not isinstance(proof, dict):
        return errors + ["report_attestation_proof_missing"]
    # A numeric token alone does not authenticate its label, experimental
    # budget, unit, or semantic context. Bind the complete reviewed extraction
    # to the independently registered attestation, for BOTH capture modes.
    if proof.get("observations_digest") != digest(row["observations"]):
        errors.append("report_observations_attestation_mismatch")
    if attestation.get("basis") == "fresh_capture":
        if row["available_at"] != row["captured_at"] or row["date_precision"] != "second":
            errors.append("fresh_capture_cannot_be_backdated")
        required = {"raw_sha256", "extracted_text_sha256", "selector", "attribute", "entity_unescape_passes"}
        if not required <= proof.keys() or proof.get("raw_sha256") != source.get("raw_sha256"):
            errors.append("fresh_capture_proof_mismatch")
    elif attestation.get("basis") == "git_archive":
        if not ARCHIVE_FIELDS <= proof.keys():
            return errors + ["archive_proof_fields_missing"]
        if source.get("source_type") != "official_report_text_archive":
            errors.append("archive_source_type_mismatch")
        if not re.fullmatch(r"[0-9a-f]{40}", str(proof["commit"])) or proof["head_sha"] != proof["commit"] or not re.fullmatch(r"[0-9a-f]{40}", str(proof["blob_sha1"])):
            errors.append("archive_git_identity_invalid")
        for key in ["archive_status_sha256", "archive_content_sha256", "deployment_proof_sha256"]:
            if not re.fullmatch(r"[0-9a-f]{64}", str(proof[key])):
                errors.append("archive_hash_invalid:" + key)
        if not _url(proof["deployment_url"]) or not str(proof["run_id"]).isdigit() or not proof["archive_source_record_id"] or not proof["path"]:
            errors.append("archive_deployment_identity_invalid")
        # Historical availability is the verified external deployment bound;
        # a collector's self-reported last_checked date never establishes it.
        if row["date_precision"] != "second" or row["available_at"] != proof["deploy_completed_at"] or _instant(proof["deploy_completed_at"]) is None:
            errors.append("archive_availability_not_deployment_bound")
        if proof["archive_content_sha256"] != source.get("raw_sha256") or _instant(proof["archive_captured_at"]) is None:
            errors.append("archive_raw_capture_mismatch")
    else:
        errors.append("unknown_attestation_basis")
    if source.get("hash_scope") != "http_response_body_bytes" or not re.fullmatch(r"[0-9a-f]{64}", str(source.get("raw_sha256"))) or not isinstance(source.get("byte_count"), int) or source["byte_count"] <= 0:
        errors.append("source_raw_hash_scope_or_size_invalid")
    if proof.get("extracted_text_sha256") != row["content_sha256"] or not isinstance(proof.get("entity_unescape_passes"), int) or isinstance(proof.get("entity_unescape_passes"), bool) or not 0 <= proof["entity_unescape_passes"] <= 3 or not isinstance(proof.get("selector"), str) or not proof["selector"] or not isinstance(proof.get("attribute"), str):
        errors.append("source_extraction_proof_invalid")
    # This dedicated source type is an attestation, never a second copy of
    # quoted/full text. The independent extractor retains its raw text locally.
    forbidden = {"full_text", "extracted_text", "raw_html", "html", "body", "body_excerpt", "source_excerpt", "raw_payload", "excerpts", "text"}
    def contains_body(value):
        if isinstance(value, dict):
            return any((key in forbidden and bool(item)) or contains_body(item) for key, item in value.items())
        if isinstance(value, list):
            return any(contains_body(item) for item in value)
        return False
    if contains_body(source):
        errors.append("report_attestation_must_not_duplicate_source_text")
    return errors


def audit_report_text(snapshots, works, manifestations, sources):
    """Validate every row against independently registered source attestations."""
    snapshots = list(snapshots)
    works = list(works.values()) if isinstance(works, dict) else list(works)
    manifestations, sources = _map(manifestations, "manifestation_id"), _map(sources, "source_record_id")
    seen, errors, resolved = set(), [], {}
    for row in snapshots:
        if not isinstance(row, dict):
            errors.append({"snapshot_id": None, "reason": "schema:snapshot_must_be_object"})
            continue
        sid = row.get("snapshot_id")
        if sid in seen:
            errors.append({"snapshot_id": sid, "reason": "duplicate_snapshot_id"})
        seen.add(sid)
        work = canonical_work_for_snapshot(row, works)
        failures = _local_errors(row, work)
        if work is None:
            failures.append("snapshot_work_unknown_or_ambiguous")
        elif not failures:
            failures.extend(_attestation_errors(row, work, manifestations, sources))
            if not failures:
                resolved[sid] = work["work_id"]
        errors.extend({"snapshot_id": sid, "reason": reason} for reason in failures)
    errors.extend(_quota_errors(snapshots))
    return {"status": "failed" if errors else "passed", "checked_snapshots": len(snapshots), "unique_snapshots": len(seen),
            "canonical_work_ids": resolved, "errors": errors}


def register_report_text_additions(payload, additions):
    """Append only, all-or-nothing. The caller registers verified sources first.

    No work, manifestation, source, evidence event, or classification is changed.
    A conflicting existing ID is rejected, with the original payload untouched.
    """
    combined = {row["snapshot_id"]: copy.deepcopy(row) for row in payload.get("report-text-snapshots", [])}
    if len(combined) != len(payload.get("report-text-snapshots", [])):
        raise ValueError("duplicate_existing_report_snapshot_id")
    for row in additions:
        if not isinstance(row, dict):
            raise ValueError("report_text_validation_failed:snapshot_must_be_object")
        sid = row.get("snapshot_id")
        if sid in combined and combined[sid] != row:
            raise ValueError("immutable_report_snapshot_conflict:" + str(sid))
        combined[sid] = copy.deepcopy(row)
    rows = list(combined.values())
    report = audit_report_text(rows, payload.get("works", []), payload.get("manifestations", []), payload.get("source-records", []))
    if report["errors"]:
        raise ValueError("report_text_validation_failed:" + json.dumps(report["errors"], ensure_ascii=False))
    out = copy.deepcopy(payload)
    out["report-text-snapshots"] = sorted(rows, key=lambda row: row["snapshot_id"])
    return out


def report_text_as_of(work, snapshots, cutoff):
    """Select audited snapshots at an exact instant or Shanghai calendar cutoff.

    Caller must use the registered/audited authority table. Each source/report
    stream keeps its newest eligible capture; later revisits do not erase old
    snapshots. Conflicting same-time content is exposed, never chosen silently.
    """
    bounds = _bounds(cutoff)
    if not bounds or bounds[1] is None:
        raise ValueError("known_report_text_cutoff_required")
    until = bounds[1]
    empty = {"status": "unavailable", "snapshots": [], "snapshot_ids": [], "available_at": None,
             "date_precision": "unknown", "canonical_work_id": work["work_id"]}
    candidates = [row for row in snapshots if row.get("work_id") in _identities(work) and not _local_errors(row, work)]
    eligible = [row for row in candidates if (when := _bounds(row["available_at"], row["date_precision"])[1]) is not None and when <= until]
    if not eligible:
        future = sorted(row["snapshot_id"] for row in candidates if row["available_at"] is not None)
        return {**empty, "status": "retrospective_only" if future else "unavailable", "retrospective_snapshot_ids": future}
    streams = {}
    for row in eligible:
        key = (row["manifestation_id"], _url(row["source_url"]))
        streams.setdefault(key, []).append(row)
    chosen, conflicts = [], []
    for rows in streams.values():
        latest = max(_bounds(row["available_at"], row["date_precision"])[1] for row in rows)
        peers = [row for row in rows if _bounds(row["available_at"], row["date_precision"])[1] == latest]
        if len({(row["content_sha256"], row["excerpt_digest"], digest(row["observations"])) for row in peers}) > 1:
            conflicts.extend(row["snapshot_id"] for row in peers)
        else:
            # Identical content recaptured later is not a second observation.
            # Keep the first documented check: a later snapshot's hash sorting
            # earlier must not replace localization/metric source identities.
            chosen.append(min(peers, key=lambda row: (_instant(row["captured_at"]), _instant(row["verified_at"]), row["snapshot_id"])))
    if conflicts:
        return {**empty, "status": "conflicting_snapshots", "snapshot_ids": sorted(conflicts)}
    chosen.sort(key=lambda row: row["snapshot_id"])
    latest = max(chosen, key=lambda row: _bounds(row["available_at"], row["date_precision"])[1])
    return {**empty, "status": "available", "snapshots": copy.deepcopy(chosen), "snapshot_ids": [row["snapshot_id"] for row in chosen],
            "available_at": latest["available_at"], "date_precision": latest["date_precision"]}
