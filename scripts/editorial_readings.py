"""Read-only, source-bound AI reading annotations for historical work views.

Two clocks stay separate: public_audit uses the caller's CURRENT data as_of
to hide future readings; annotations_for_work uses the HISTORICAL cutoff
only for the already selected version's public date. A later reading of v1
may inform a retrospective v1 view, but a v3 reading cannot replace it.

The work argument must be the historical view produced by the existing
text-selection pipeline. This helper never selects a newer work version,
changes facts/grades/sampling, loads original HTML, or certifies cognition.
"""
from __future__ import annotations

import copy
import json
import re
from datetime import date, datetime
from pathlib import Path

from catalog_store import fingerprint
from fulltext_reading_reviews import public_audit, timestamp, versioned_read_url
from temporal_evidence import public_by


ANNOTATION_FIELDS = (
    "reading_id", "work_id", "version", "source_url", "raw_sha256",
    "article_text_sha256", "article_normalization", "article_chars",
    "observed_at", "read_completed_at", "reading_status", "reader_kind",
    "source_availability_status", "transport_verification", "assurance",
    "verification_scope", "human_reviewed", "understanding_verified",
    "images_inspected", "supplementary_materials_inspected",
    "publisher_fulltext_or_media_completeness_verified", "tables_exhaustive",
    "checked_table_ids", "checked_table_count", "checked_table_text_sha256",
    "findings_zh", "limitations_zh", "declaration_sha256",
    "reading_packet_sha256", "reading_packet_segment_chars",
)

PDF_ANNOTATION_FIELDS = (
    "reading_id", "work_id", "version", "source_format", "source_url",
    "source_observation_id", "manifestation_id", "edition_label", "pdf_sha256",
    "document_text_sha256", "page_text_sha256", "extractor_version", "page_count",
    "read_pages", "visual_pages_checked", "observed_at", "read_completed_at",
    "reading_status", "reader_kind", "text_scope", "assurance", "verification_scope",
    "human_reviewed", "understanding_verified", "supplementary_materials_inspected",
    "publisher_fulltext_or_media_completeness_verified", "tables_exhaustive",
    "checked_table_count", "findings_zh", "limitations_zh", "declaration_sha256",
    "pdf_source_record_id", "pdf_source_metadata_sha256", "pdf_identity_checked_at",
)


def _reading_order(row):
    return timestamp(row["read_completed_at"]), timestamp(row["observed_at"]), row["reading_id"]


def build_reading_index(catalog, readings, observations, as_of, *, pdf_readings=None, pdf_observations=None):
    """Audit explicit public inputs and return independent lists by work_id.

    Only metadata consistency is audited. Actual source bytes and the content
    behind valid-looking locator hashes are NOT independently reverified.
    """
    work_ids = [row["work_id"] for row in catalog["works"]]
    if len(work_ids) != len(set(work_ids)):
        raise ValueError("editorial_readings_duplicate_canonical_work")
    audited = public_audit(list(readings), catalog, list(observations), as_of)
    indexed = {}
    for row in sorted(audited["records"], key=lambda row: (row["work_id"], *_reading_order(row))):
        indexed.setdefault(row["work_id"], []).append(copy.deepcopy(row))
    if (pdf_readings is None) != (pdf_observations is None):
        raise ValueError("editorial_readings_pdf_metadata_pair_incomplete")
    if pdf_readings is not None:
        if not isinstance(pdf_readings, list) or not isinstance(pdf_observations, list):
            raise ValueError("editorial_readings_pdf_metadata_lists_required")
        if pdf_readings or pdf_observations:
            from pdf_reading_reviews import visible_public_audit
            pdf = visible_public_audit(pdf_readings, catalog, pdf_observations, as_of)
            by_source = {row["source_observation_id"]: row for row in pdf["sources"]}
            for row in pdf["records"]:
                source = by_source[row["source_observation_id"]]
                derived = copy.deepcopy(row)
                derived.update(pdf_source_record_id=source["source_record_id"],
                               pdf_source_metadata_sha256=source["metadata_sha256"],
                               pdf_identity_checked_at=source["identity_check"]["checked_at"])
                indexed.setdefault(row["work_id"], []).append(derived)
            for rows in indexed.values():
                rows.sort(key=_reading_order)
    return indexed


def _read_metadata_jsonl(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("editorial_readings_regular_metadata_file_required")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_reading_index(catalog, directory, as_of):
    """Load HTML metadata plus an optional complete PDF pair; never source bytes.

    HTML files are required. Both PDF files may be absent for legacy fixtures;
    a one-file PDF pair is invalid. Production callers still validate the
    independent eight-ledger source clock before invoking this loader.
    """
    directory = Path(directory)
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("editorial_readings_metadata_directory_required")
    readings = _read_metadata_jsonl(directory / "fulltext-readings.jsonl")
    observations = _read_metadata_jsonl(directory / "source-observations.jsonl")
    pdf_paths = [directory / "pdf-readings.jsonl", directory / "pdf-source-observations.jsonl"]
    present = [path.exists() or path.is_symlink() for path in pdf_paths]
    if any(present) and not all(present):
        raise ValueError("editorial_readings_pdf_metadata_pair_incomplete")
    pdf = [_read_metadata_jsonl(path) for path in pdf_paths] if all(present) else [None, None]
    return build_reading_index(catalog, readings, observations, as_of,
                               pdf_readings=pdf[0], pdf_observations=pdf[1])


def _version_date_is_valid(value, precision):
    """Recognize the existing text snapshot's second/day/month date forms."""
    if not isinstance(value, str) or precision not in {"second", "day", "month"}:
        return False
    try:
        if precision == "day":
            return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value)) and bool(date.fromisoformat(value))
        if precision == "month":
            if not re.fullmatch(r"\d{4}-\d{2}(?:-\d{2})?", value):
                return False
            date.fromisoformat(value if len(value) == 10 else value + "-01")
            return True
        return "T" in value and datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is not None
    except ValueError:
        return False


def annotations_for_work(work, index, cutoff):
    """Return latest HTML and/or PDF for the already selected historical version.

    The historical view gate is intentionally stricter than abstract fallback:
    unavailable/unversioned/ambiguous text cannot be upgraded by a reading.
    Newest is selected within each format, never PDF replacing an HTML record.
    Versionless conference PDFs cannot acquire a fabricated arXiv version here.
    """
    version = work.get("text_version")
    snapshot_ids = work.get("text_snapshot_ids")
    available_at, precision = work.get("text_available_at"), work.get("text_date_precision")
    if (work.get("experimental_text_available") is not True or work.get("text_status") != "available" or
            work.get("research_status_blocked") or work.get("validation_eligible") is False or
            not isinstance(version, str) or not re.fullmatch(r"v[1-9]\d*", version) or
            not isinstance(snapshot_ids, list) or not snapshot_ids or
            any(not isinstance(sid, str) or not sid.strip() for sid in snapshot_ids) or
            len(snapshot_ids) != len(set(snapshot_ids)) or
            not _version_date_is_valid(available_at, precision)):
        return []
    try:
        if not public_by(available_at, cutoff, precision):
            return []
    except (TypeError, ValueError):
        return []
    candidates = [row for row in index.get(work.get("work_id"), [])
                  if row["work_id"] == work.get("work_id") and row["version"] == version]
    result = []
    for pdf in (False, True):
        rows = [row for row in candidates if (row.get("source_format") == "pdf") == pdf]
        if rows:
            result.append(_annotation_for_reading(max(rows, key=_reading_order), work, cutoff, pdf=pdf))
    return result


def _annotation_for_reading(selected, work, cutoff, *, pdf=False):
    version = work["text_version"]
    snapshot_ids = work["text_snapshot_ids"]
    available_at, precision = work["text_available_at"], work["text_date_precision"]
    fields = PDF_ANNOTATION_FIELDS if pdf else ANNOTATION_FIELDS
    annotation = {key: copy.deepcopy(selected[key]) for key in fields if key in selected}
    annotation.update(
        reading_source_url=selected["source_url"] if pdf else versioned_read_url(selected["source_url"], version),
        annotation_kind="ai_pdf_reading_paraphrase" if pdf else "ai_fulltext_reading_paraphrase",
        annotation_scope="retrospective_reading_of_the_selected_historical_version",
        source_attribution="paper_author_reports_as_interpreted_by_AI_not_independent_validation",
        public_metadata_audit_scope="metadata_consistency_only;original_source_not_re_read",
        verbatim_source_text=False,
        independent_validation=False,
        matched_text_snapshot_ids=sorted(snapshot_ids),
        source_version_available_at=available_at,
        source_version_date_precision=precision,
    )
    warnings = []
    if pdf:
        annotation["page_locator_basis"] = "one_based_PDF_file_pages_not_HTML_DOM_or_printed_pages"
        if not public_by(selected["pdf_identity_checked_at"], cutoff, "second"):
            warnings.append("PDF_identity_check_after_historical_cutoff_not_backdated")
    if not pdf and selected["source_availability_status"] == "partial_text":
        warnings.append("partial_source_text_preserved")
    if not pdf and selected["transport_verification"] != "complete":
        warnings.append("transport_completion_not_verified")
    if not pdf and selected["transport_verification"] == "legacy_unrecorded":
        warnings.append("legacy_transport_unrecorded")
    if annotation["reading_source_url"] != selected["source_url"]:
        warnings.append("observed_url_unversioned_reader_link_pinned_without_new_acquisition")
    if not public_by(selected["observed_at"], cutoff, "second"):
        warnings.append("source_observation_after_historical_cutoff_not_backdated")
    if not public_by(selected["read_completed_at"], cutoff, "second"):
        warnings.append("reading_after_historical_cutoff_not_backdated")
    annotation["warnings"] = warnings
    annotation["annotation_digest"] = fingerprint(annotation)
    return annotation
