"""Source-bound signal drafts and explicit semantic review, independent of export.

Mechanical validation establishes provenance, not the truth of an inference.
Only a named human review may mark an assessment verified. No network calls.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker

try:
    from temporal_evidence import public_day
except ModuleNotFoundError:
    from scripts.temporal_evidence import public_day

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "config/signal-evidence.schema.json").read_text())
ASSESSMENT_SCHEMA = SCHEMA["$defs"]["assessment"]
ASSESSMENT_KEYS = tuple(ASSESSMENT_SCHEMA["properties"])


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def source_content_digest(work):
    return digest({"title": work.get("title") or "", "abstract": work.get("abstract") or ""})


def source_text(card):
    return {key: card.get(key) or "" for key in ("title", "abstract")}


def normalized_url(value):
    if not isinstance(value, str):
        return None
    parsed = urlsplit(value)
    if parsed.scheme not in {"https", "http"} or not parsed.hostname or parsed.username or parsed.password:
        return None
    return parsed._replace(fragment="").geturl().rstrip("/")


def source_public_date(source):
    if source.get("date_supersession"):
        return None, "unknown"
    value = source.get("public_at") or source.get("published_at")
    precision = source.get("public_at_precision") or source.get("date_precision") or ("day" if value and len(value) >= 10 else "month" if value and len(value) == 7 else "year" if value and len(value) == 4 else "unknown")
    return (value, precision) if public_day(value, precision) else (None, "unknown")


def load_signal_specs():
    return json.loads((ROOT / "config/trend-signals.json").read_text())["signals"]


def _map(values, key):
    return values if isinstance(values, dict) else {row[key]: row for row in (values or [])}


def assessment_errors(row, card, signals=None):
    """Validate exact original-text bounds, experiment excerpts and source date."""
    if any(Draft202012Validator(ASSESSMENT_SCHEMA, format_checker=FormatChecker()).iter_errors(row)):
        return ["assessment_schema_invalid"]
    errors = []
    specs = _map(signals if signals is not None else load_signal_specs(), "signal_id")
    spec = specs.get(row["signal_id"])
    if not spec:
        errors.append("unknown_signal")
    elif not (set(spec.get("directions", [])) & set(card.get("directions", [])) or set(spec.get("questions", [])) & set(card.get("questions", []))):
        errors.append("signal_outside_card_facets")
    if row["work_id"] != card.get("work_id") or row["evidence_card_id"] != card.get("evidence_id"):
        errors.append("evidence_card_mismatch")
    if not row["statement"].strip() or len(set(row["source_record_ids"])) != len(row["source_record_ids"]):
        errors.append("empty_statement_or_duplicate_source")
    documents = [doc for doc in card.get("source_documents", []) if normalized_url(doc.get("url")) == normalized_url(row["source_url"])]
    if not normalized_url(row["source_url"]) or not documents or not set(row["source_record_ids"]) <= {doc["source_record_id"] for doc in documents}:
        errors.append("source_not_bound_to_card")
    dated = [doc for doc in documents if doc.get("source_record_id") in row["source_record_ids"]]
    if not dated or not all(row["public_at"] == doc.get("public_at") and row["public_at_precision"] == doc.get("public_at_precision") for doc in dated):
        errors.append("source_public_date_mismatch")
    if (row["public_at_precision"] == "unknown") != (row["public_at"] is None) or (row["public_at"] is not None and public_day(row["public_at"], row["public_at_precision"]) is None):
        errors.append("invalid_public_date")
    quotes = []
    for span in row["source_spans"]:
        text = card.get(span["field"]) or ""
        if span["end"] <= span["start"] or text[span["start"]:span["end"]] != span["quote"]:
            errors.append("source_span_mismatch")
        quotes.append(span["quote"])
    if row["stance"] != "neutral" and not any(span["field"] == "abstract" and len(span["quote"].strip()) >= 20 for span in row["source_spans"]):
        errors.append("directional_assessment_requires_abstract")
    excerpts = "\n".join(quotes)
    experiment = row["experiment"]
    values = [experiment[key] for key in ("setting", "baseline", "metric") if experiment[key] is not None] + experiment["limitations"]
    if any(not value.strip() or value not in excerpts for value in values):
        errors.append("experiment_not_verbatim_source")
    # A draft interpretation can be Chinese, but quantitative values must occur
    # in the cited spans, never elsewhere in the paper/title/packet.
    numbers = lambda text: set(re.findall(r"(?<![\d.])[+-]?\d+(?:\.\d+)?(?![\d.])", text))
    if not numbers(row["statement"]) <= numbers(excerpts):
        errors.append("statement_number_not_in_source")
    # Chinese quantitative claims also need explicit numeric source support.
    for token in re.findall(r"([零一二两三四五六七八九十百千]+)\s*(?:项|篇|个|组|家|次|倍|小时|天|万|亿|秒|分钟|个百分点)", row["statement"]):
        total, current = 0, 0
        for char in token:
            if char in "零一二两三四五六七八九":
                current = {"零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}[char]
            else:
                total += (current or 1) * {"十": 10, "百": 100, "千": 1000}[char]
                current = 0
        if float(total + current) not in {float(value) for value in numbers(excerpts)}:
            errors.append("statement_number_not_in_source")
    return sorted(set(errors))


def record_content_digest(row):
    return digest({key: row.get(key) for key in (*ASSESSMENT_KEYS, "source_content_digest", "source_text_snapshot", "source_text_digest")})


def _bound_archived_text(row, sources):
    """Prove a historical draft against trusted archived version metadata.

    A full-text digest suffices only for a complete snapshot. For truncated
    abstracts an archived full snapshot is needed to verify the exact prefix;
    a caller-provided full digest does not authenticate an arbitrary excerpt.
    """
    if sources is None:
        return False
    for identifier in row["source_record_ids"]:
        source = sources.get(identifier, {})
        if source.get("source_type") != "official_arxiv_version_metadata":
            return False
        archived = source.get("archived_text_snapshot")
        expected = source.get("text_content_digest") or (source_content_digest(archived) if isinstance(archived, dict) else None)
        if expected != row["source_content_digest"]:
            return False
        if isinstance(archived, dict):
            if digest({"title": archived.get("title") or "", "abstract": (archived.get("abstract") or "")[:3500]}) != row["source_text_digest"]:
                return False
        elif row["source_text_digest"] != expected:
            return False
    return bool(row["source_record_ids"])


def make_signal_draft(assessment, card, *, month, model, generated_at, input_digest):
    errors = assessment_errors(assessment, card)
    if errors:
        raise ValueError("signal_assessment_invalid:" + ",".join(errors))
    identity = [month, assessment["signal_id"], assessment["work_id"], normalized_url(assessment["source_url"]), assessment["source_spans"]]
    snapshot = source_text(card)
    row = {**copy.deepcopy(assessment), "record_id": "signal-evidence:" + digest(identity)[:24],
           "review_status": "draft", "generator": "llm", "model": model, "generated_month": month,
           "created_at": generated_at, "updated_at": generated_at, "input_digest": input_digest,
           "source_content_digest": card.get("source_content_digest") or source_content_digest(card),
           "source_text_snapshot": snapshot, "source_text_digest": digest(snapshot), "review_history": []}
    row["content_digest"] = record_content_digest(row)
    return row


def validate_signal_record(row, work, source_records=None, signals=None):
    if any(Draft202012Validator(SCHEMA, format_checker=FormatChecker()).iter_errors(row)):
        return ["signal_record_schema_invalid"]
    errors = []
    if not work or row["work_id"] != work.get("work_id"):
        return ["unknown_work"]
    sources = _map(source_records, "source_record_id") if source_records is not None else None
    if not set(row["source_record_ids"]) <= set(work.get("source_record_ids", [])):
        errors.append("source_not_owned_by_work")
    if sources is not None and any(identifier not in sources or normalized_url(sources[identifier].get("url")) != normalized_url(row["source_url"]) for identifier in row["source_record_ids"]):
        errors.append("source_record_url_mismatch")
    if sources is not None and any(identifier in sources and source_public_date(sources[identifier]) != (row["public_at"], row["public_at_precision"]) for identifier in row["source_record_ids"]):
        errors.append("source_record_public_date_mismatch")
    if sources is not None and any(sources.get(identifier, {}).get("date_supersession") for identifier in row["source_record_ids"]):
        errors.append("source_public_date_superseded")
    snapshot = row["source_text_snapshot"]
    if row["source_text_digest"] != digest(snapshot) or row["content_digest"] != record_content_digest(row):
        errors.append("record_content_changed_requires_review")
    # Verified snapshots remain historical evidence when canonical text changes.
    # Drafts must be regenerated/reviewed instead of being silently made current.
    if row["review_status"] != "verified":
        canonical_matches = row["source_content_digest"] == source_content_digest(work)
        excerpt_matches = row["source_text_digest"] == digest({"title": work.get("title") or "", "abstract": (work.get("abstract") or "")[:3500]})
        if not (canonical_matches and excerpt_matches) and not _bound_archived_text(row, sources):
            errors.append("canonical_source_changed" if not canonical_matches else "source_excerpt_not_bound_to_original")
    documents = [{"source_record_id": identifier, "url": row["source_url"], "public_at": row["public_at"], "public_at_precision": row["public_at_precision"]} for identifier in row["source_record_ids"]]
    card = {**work, **snapshot, "evidence_id": row["evidence_card_id"], "source_documents": documents}
    errors += assessment_errors({key: row[key] for key in ASSESSMENT_KEYS}, card, signals)
    history = row["review_history"]
    if row["review_status"] == "verified" and (not history or history[-1]["decision"] != "verified" or any(not history[-1][key].strip() for key in ("reviewer", "note", "review_id"))):
        errors.append("semantic_review_required")
    return sorted(set(errors))


def review_signal_record(row, *, reviewer, note, reviewed_at, semantic_check_completed=False, decision="verified"):
    if decision not in {"verified", "draft"} or not reviewer.strip() or not note.strip() or (decision == "verified" and not semantic_check_completed):
        raise ValueError("explicit_semantic_review_required")
    result = copy.deepcopy(row)
    result["review_history"].append({"review_id": "review:" + digest([row["record_id"], reviewed_at, reviewer, note])[:20], "reviewer": reviewer,
                                     "reviewed_at": reviewed_at, "decision": decision, "note": note})
    result.update(review_status=decision, updated_at=reviewed_at)
    result["content_digest"] = record_content_digest(result)
    return result


def merge_signal_drafts(existing, drafts, month):
    """Replace this month's untouched automatic drafts, preserve human history."""
    def protected(row):
        return row.get("review_status") == "verified" or row.get("generator") != "llm" or bool(row.get("review_history")) or row.get("content_digest") != record_content_digest(row)
    retained = {row["record_id"]: copy.deepcopy(row) for row in existing if row.get("generated_month") != month or protected(row)}
    for row in drafts:
        if row.get("review_status") != "draft" or row.get("review_history") or row.get("generated_month") != month:
            raise ValueError("automated_merge_accepts_only_current_drafts")
        if row["record_id"] not in retained:
            previous = next((old for old in existing if old["record_id"] == row["record_id"]), None)
            retained[row["record_id"]] = copy.deepcopy(previous if previous and previous.get("content_digest") == row["content_digest"] else row)
    return [retained[key] for key in sorted(retained)]


def load_signal_evidence(path, *, works, source_records=None, signal_specs=None):
    path = Path(path)
    rows, invalid = [], []
    for number, line in enumerate(path.read_text().splitlines() if path.exists() else [], 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError("not_object")
            rows.append(row)
        except ValueError:
            invalid.append({"record": None, "line": number, "errors": ["malformed_jsonl_record"]})
    malformed_count = len(invalid)
    by_work, valid = _map(works, "work_id"), []
    identities = {}
    for row in rows:
        identities[row.get("record_id")] = identities.get(row.get("record_id"), 0) + 1
    for row in rows:
        errors = validate_signal_record(row, by_work.get(row.get("work_id")), source_records, signal_specs)
        if identities[row.get("record_id")] > 1:
            errors.append("duplicate_record_id")
        (invalid if errors else valid).append({"record": row, "errors": errors} if errors else row)
    return {"records": valid, "invalid_records": invalid, "counts": {"total": len(rows) + malformed_count, "verified": sum(row["review_status"] == "verified" for row in valid), "draft": sum(row["review_status"] == "draft" for row in valid), "invalid": len(invalid)}}


def overlay_signal_evidence(works, records):
    """Attach validated persistent records to copies, never mutate authority."""
    grouped = {}
    for row in records:
        grouped.setdefault(row["work_id"], []).append(row)
    result = []
    for work in works:
        row = {**work}
        if row.get("signal_evidence"):
            row["legacy_signal_evidence"] = row["signal_evidence"]
        row["signal_evidence"] = copy.deepcopy(grouped.get(row["work_id"], []))
        result.append(row)
    return result
