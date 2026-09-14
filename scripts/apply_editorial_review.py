"""Explicit, source-bound post-generation editing; never a forged Responses result."""
from __future__ import annotations

import argparse
import copy
import json
import re
from datetime import datetime
from pathlib import Path

try:
    from generate_v3_editorial import (EDITORIAL, OUTPUT_SCHEMA, PROSE_SECTIONS, digest, editorial_input_digest,
                                      validate_editorial, read_jsonl, write_json, atomic_text)
except ModuleNotFoundError:
    from scripts.generate_v3_editorial import (EDITORIAL, OUTPUT_SCHEMA, PROSE_SECTIONS, digest, editorial_input_digest,
                                               validate_editorial, read_jsonl, write_json, atomic_text)

REVIEW_FIELDS = {"review_id", "reviewer", "reviewer_kind", "reviewed_at", "parent_artifact_digest", "parent_response_id", "input_digest", "edits"}
PROSE_FIELDS = {"summary", "supporting_ids", "counterevidence_ids"}
LOCAL_FIELDS = {"title_zh", "summary_zh", "keywords_zh"}
LOCAL_IDENTITY_FIELDS = {"work_id", "source_ids", *LOCAL_FIELDS}


def _equal(left, right):
    return json.dumps(left, ensure_ascii=False, sort_keys=True, allow_nan=False) == json.dumps(right, ensure_ascii=False, sort_keys=True, allow_nan=False)


def _time(value):
    if not isinstance(value, str):
        raise ValueError("review_time_must_be_utc")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError("review_time_must_be_utc")
    return parsed


def _content_digest(artifact):
    return digest({key: value for key, value in artifact.items() if key != "post_edit_reviews"})


def _validate_content(artifact, packet):
    content = {key: copy.deepcopy(artifact[key]) for key in OUTPUT_SCHEMA["properties"] if key in artifact}
    for section in PROSE_SECTIONS:
        for row in content.get(section, []):
            row.pop("claim_id", None)
    validate_editorial(content, packet)


def _review_valid(review, artifact, packet):
    if not isinstance(review, dict) or set(review) != REVIEW_FIELDS:
        raise ValueError("invalid_editorial_review_fields")
    if not all(isinstance(review[key], str) and review[key].strip() for key in REVIEW_FIELDS - {"edits"}):
        raise ValueError("missing_editorial_review_identity")
    if review["reviewer_kind"] not in {"ai", "human"}:
        raise ValueError("reviewer_kind_must_be_ai_or_human")
    if review["reviewer_kind"] == "human" and re.search(r"\b(codex|gpt|chatgpt|claude|assistant)\b", review["reviewer"], re.I):
        raise ValueError("ai_reviewer_cannot_be_labeled_human")
    checked = _time(review["reviewed_at"])
    if checked < _time(artifact["generated_at"]):
        raise ValueError("review_predates_generation")
    for key in ["parent_artifact_digest", "input_digest"]:
        if not re.fullmatch(r"[a-f0-9]{64}", review[key]):
            raise ValueError("invalid_review_digest")
    if artifact.get("status") != "complete" or review["parent_response_id"] != artifact.get("response_id"):
        raise ValueError("review_parent_response_mismatch")
    if review["input_digest"] != artifact.get("input_digest") or review["input_digest"] != editorial_input_digest(packet):
        raise ValueError("review_evidence_packet_changed")
    if not isinstance(review["edits"], list) or not review["edits"]:
        raise ValueError("editorial_review_requires_explicit_edits")
    cards = {row["evidence_id"]: row for row in packet["evidence_cards"] if row.get("evidence_month") == packet["month"]}
    for edit in review["edits"]:
        required = {"path", "before", "after", "evidence_ids", "reason"}
        if not isinstance(edit, dict) or not required <= set(edit) or set(edit) - required - {"op"} or edit.get("op", "replace") != "replace":
            raise ValueError("review_only_supports_explicit_replace")
        if not isinstance(edit["reason"], str) or not edit["reason"].strip():
            raise ValueError("review_reason_required")
        ids = edit["evidence_ids"]
        if not isinstance(ids, list) or not ids or any(not isinstance(eid, str) or eid not in cards for eid in ids) or len(ids) != len(set(ids)):
            raise ValueError("review_evidence_id_unknown_or_duplicate")
        if any(not cards[eid].get("source_record_ids") for eid in ids):
            raise ValueError("review_evidence_has_no_source_id")
    return cards


def _path(value):
    if not isinstance(value, str) or not value.startswith("/"):
        raise ValueError("review_requires_json_pointer")
    parts = value[1:].split("/")
    # Allowed property names contain no escaped pointer tokens or dash append.
    if parts[0] in PROSE_SECTIONS and (len(parts) == 1 or len(parts) == 2 and re.fullmatch(r"0|[1-9]\d*", parts[1]) or len(parts) == 3 and re.fullmatch(r"0|[1-9]\d*", parts[1]) and parts[2] in PROSE_FIELDS):
        return parts
    if parts[0] == "localizations" and len(parts) == 3 and re.fullmatch(r"0|[1-9]\d*", parts[1]) and parts[2] in LOCAL_FIELDS:
        return parts
    raise ValueError("review_path_not_editable:" + value)


def _lookup(container, parts):
    for part in parts:
        try:
            container = container[int(part)] if isinstance(container, list) else container[part]
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            raise ValueError("review_path_does_not_exist") from exc
    return container


def _rows_for_edit(artifact, parts):
    if parts[0] == "localizations":
        return []
    value = _lookup(artifact, parts[:1] if len(parts) == 1 else parts[:2])
    return value if isinstance(value, list) else [value]


def apply_editorial_review(artifact, review, packet):
    """Pure, idempotent, exact-precondition replacement with complete validation."""
    cards = _review_valid(review, artifact, packet)
    _validate_content(artifact, packet)
    previous = artifact.get("post_edit_reviews", [])
    if not isinstance(previous, list):
        raise ValueError("invalid_post_edit_review_history")
    if previous and previous[-1].get("result_content_digest") != _content_digest(artifact):
        raise ValueError("reviewed_artifact_content_changed")
    for receipt in previous:
        original_review = {key: receipt[key] for key in REVIEW_FIELDS if key in receipt}
        if set(original_review) != REVIEW_FIELDS or digest(original_review) != receipt.get("review_digest"):
            raise ValueError("review_history_digest_mismatch")
        if receipt.get("scope") != "content_review_not_independent_validation" or receipt.get("independent_validation") is not False or receipt.get("label") != ("AI内容审校" if receipt.get("reviewer_kind") == "ai" else "人工内容审校"):
            raise ValueError("review_history_scope_changed")
        if receipt["review_id"] == review["review_id"]:
            if receipt["review_digest"] != digest(review):
                raise ValueError("editorial_review_id_conflict")
            return copy.deepcopy(artifact)
    if digest(artifact) != review["parent_artifact_digest"]:
        raise ValueError("review_parent_artifact_changed")
    if previous and _time(review["reviewed_at"]) < _time(previous[-1]["reviewed_at"]):
        raise ValueError("review_predates_previous_review")
    result = copy.deepcopy(artifact)
    replacements = set()
    for edit in review["edits"]:
        parts = _path(edit["path"])
        current = _lookup(result, parts)
        if not _equal(current, edit["before"]):
            raise ValueError("review_before_mismatch:" + edit["path"])
        before_rows = copy.deepcopy(_rows_for_edit(result, parts))
        parent = _lookup(result, parts[:-1])
        key = int(parts[-1]) if isinstance(parent, list) else parts[-1]
        parent[key] = copy.deepcopy(edit["after"])
        after_rows = _rows_for_edit(result, parts)
        if any(not isinstance(row, dict) for row in after_rows):
            raise ValueError("invalid_review_claim_row")
        old_by_id = {row.get("claim_id"): row for row in before_rows if row.get("claim_id")}
        for index, row in enumerate(after_rows):
            old = old_by_id.get(row.get("claim_id"))
            if len(parts) >= 2 and before_rows:
                old = before_rows[0]
            if old and not _equal(row.get("numeric_claims"), old.get("numeric_claims")):
                raise ValueError("review_cannot_change_numeric_claims")
            if not old and row.get("numeric_claims") != []:
                raise ValueError("new_review_claim_cannot_add_numeric_facts")
            added = set(row.get("supporting_ids", []) + row.get("counterevidence_ids", [])) - set((old or {}).get("supporting_ids", []) + (old or {}).get("counterevidence_ids", []))
            if not added <= set(edit["evidence_ids"]):
                raise ValueError("new_citation_missing_review_evidence")
            if not set(edit["evidence_ids"]) & set(row.get("supporting_ids", []) + row.get("counterevidence_ids", [])) and (len(parts) > 1 or not old or not _equal(row, old)):
                raise ValueError("review_evidence_unrelated_to_edited_claim")
        if parts[0] == "localizations":
            localization = result["localizations"][int(parts[1])]
            cited_works = {cards[eid]["work_id"] for eid in edit["evidence_ids"]}
            if localization["work_id"] not in cited_works:
                raise ValueError("localization_review_evidence_wrong_work")
        elif len(parts) <= 2:
            replacements.add(tuple(parts))
    for section in PROSE_SECTIONS:
        original_rows = {row.get("claim_id"): row for row in artifact[section] if row.get("claim_id")}
        for index, row in enumerate(result[section]):
            if row.get("claim_id") in original_rows and _equal(row, original_rows[row["claim_id"]]):
                continue
            if not row.get("claim_id") or (section,) in replacements or (section, str(index)) in replacements:
                content = {key: value for key, value in row.items() if key != "claim_id"}
                row["claim_id"] = f"claim:{artifact['month']}:review:" + digest([review["review_id"], section, index, content])[:24]
    _validate_content(result, packet)
    receipt = {**copy.deepcopy(review), "review_digest": digest(review), "result_content_digest": _content_digest(result),
               "scope": "content_review_not_independent_validation", "label": "AI内容审校" if review["reviewer_kind"] == "ai" else "人工内容审校",
               "independent_validation": False, "generation_provenance": "post_edit_not_new_model_response"}
    result["post_edit_reviews"] = [*copy.deepcopy(previous), receipt]
    return result


def _reviewed_localizations(parent, result, rows, review, packet):
    """Preflight every cache edit before any artifact/cache write."""
    by_id = {row["work_id"]: row for row in rows}
    if len(by_id) != len(rows):
        raise ValueError("duplicate_localization_cache_identity")
    before = {row["work_id"]: row for row in parent["localizations"]}
    cards = {card["evidence_id"]: card for card in packet["evidence_cards"]}
    changes = {}
    marker = {"review_id": review["review_id"], "review_digest": digest(review), "reviewer_kind": review["reviewer_kind"],
              "reviewer": review["reviewer"], "reviewed_at": review["reviewed_at"], "parent_response_id": review["parent_response_id"],
              "scope": "content_review_not_independent_validation"}
    for row in result["localizations"]:
        wid = row["work_id"]
        if _equal(row, before[wid]):
            continue
        cached = by_id.get(wid)
        if not cached or cached.get("source_content_digest") != cards[wid].get("source_content_digest") or not cached.get("source_content_digest"):
            raise ValueError("localization_cache_source_changed")
        current = {key: cached.get(key) for key in LOCAL_IDENTITY_FIELDS}
        resumed = marker in cached.get("post_edit_reviews", []) and _equal(current, row)
        if not resumed and not _equal(current, before[wid]):
            raise ValueError("localization_cache_before_mismatch")
        changes[wid] = {**copy.deepcopy(cached), **copy.deepcopy(row),
                        "post_edit_reviews": copy.deepcopy(cached.get("post_edit_reviews", [])) + ([] if resumed else [marker])}
    return [changes.get(row["work_id"], copy.deepcopy(row)) for row in rows]


def _immutable_json(path, value):
    if path.exists():
        if not _equal(json.loads(path.read_text()), value):
            raise ValueError("editorial_archive_conflict")
    else:
        write_json(path, value)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, default=EDITORIAL)
    args = parser.parse_args(argv)
    review, packet = json.loads(args.review.read_text()), json.loads(args.packet.read_text())
    month = packet["month"]
    if not re.fullmatch(r"20\d{2}-(0[1-9]|1[0-2])", month):
        raise ValueError("invalid_review_month")
    target = args.output_directory / "monthly" / f"{month}.json"
    parent = json.loads(target.read_text())
    result = apply_editorial_review(parent, review, packet)
    if _equal(parent, result):
        print(json.dumps({"status": "already_applied", "month": month, "review_id": review["review_id"]}))
        return 0
    path = args.output_directory / "work-localizations.jsonl"
    previous_rows = read_jsonl(path)
    localizations = _reviewed_localizations(parent, result, previous_rows, review, packet)
    # Backups and explicit review records precede all live content changes.
    _immutable_json(args.output_directory / "revisions" / month / f"{review['parent_artifact_digest']}.json", parent)
    _immutable_json(args.output_directory / "reviews" / month / f"{digest(review)}.json", review)
    if not _equal(previous_rows, localizations):
        atomic_text(path, "".join(json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n" for row in localizations))
    write_json(target, result)
    print(json.dumps({"status": "review_applied", "month": month, "review_id": review["review_id"], "reviewer_kind": review["reviewer_kind"], "edits": len(review["edits"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
