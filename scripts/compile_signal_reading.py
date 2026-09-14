"""Compile explicitly authored source-reading inputs into draft evidence only.

This is not a Responses API run or a human approval. Exact archived excerpts
are resolved from the ordinary month evidence packet. Exported drafts retain
an explicitly AI-labelled draft review so a later LLM run cannot erase them.
"""
from __future__ import annotations

import argparse
import copy
import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.generate_v3_editorial import (
    API, CATALOG, EDITORIAL, atomic_text, build_evidence_packet,
    editorial_input_digest, load_catalog, read_jsonl,
)
from scripts.signal_evidence import (
    digest, make_signal_draft, review_signal_record,
    validate_signal_record,
)


def compile_reading(reading: dict, packet: dict, catalog: dict) -> list[dict]:
    if (reading.get("origin") != "codex_session_source_reading"
            or reading.get("model") is not None
            or reading.get("reviewer") != "Codex AI source check; not a human review"
            or reading.get("month") != packet.get("month")):
        raise ValueError("reading_origin_or_month_invalid")
    try:
        reviewed_at = datetime.fromisoformat(reading["reviewed_at"].replace("Z", "+00:00"))
        if reviewed_at.tzinfo is None or reviewed_at.utcoffset().total_seconds() != 0 or reviewed_at > datetime.now(timezone.utc):
            raise ValueError("invalid")
    except (KeyError, TypeError, ValueError, AttributeError):
        raise ValueError("reading_review_date_invalid") from None
    if not isinstance(reading.get("assessments"), list) or not reading["assessments"]:
        raise ValueError("reading_assessments_required")
    cards = {row["evidence_id"]: row for row in packet["evidence_cards"]}
    works = {row["work_id"]: row for row in catalog["works"]}
    compiled = []
    for item in reading["assessments"]:
        card = cards.get(item.get("work_id"))
        if not card or card.get("experimental_text_available") is False:
            raise ValueError("reading_source_text_unavailable")
        document = next((row for row in card["source_documents"] if row["url"] == item.get("source_url")), None)
        if not document or not item.get("quotes") or not item.get("note", "").strip():
            raise ValueError("reading_source_or_review_note_missing")
        spans = []
        for quote in item["quotes"]:
            if not isinstance(quote, str) or not quote.strip():
                raise ValueError("reading_quote_missing")
            start = card["abstract"].find(quote)
            if start < 0:
                raise ValueError("reading_quote_not_in_archived_abstract")
            spans.append({"field": "abstract", "start": start, "end": start + len(quote), "quote": quote})
        assessment = {key: item[key] for key in ("signal_id", "work_id", "stance", "statement", "experiment", "source_url")}
        assessment.update(evidence_card_id=card["evidence_id"], research_scope="in_scope", source_spans=spans,
                          source_record_ids=[document["source_record_id"]], public_at=document["public_at"],
                          public_at_precision=document["public_at_precision"])
        draft = make_signal_draft(assessment, card, month=reading["month"], model=None,
                                  generated_at=reading["reviewed_at"], input_digest=editorial_input_digest(packet))
        draft = review_signal_record(draft, reviewer=reading["reviewer"], note=item["note"],
                                     reviewed_at=reading["reviewed_at"], decision="draft")
        errors = validate_signal_record(draft, works[item["work_id"]], catalog["source-records"])
        if errors:
            raise ValueError("reading_record_invalid:" + ",".join(errors))
        compiled.append(draft)
    if len({row["record_id"] for row in compiled}) != len(compiled):
        raise ValueError("reading_duplicate_record")
    return compiled


def merge_reading(existing: list[dict], incoming: list[dict], *, allow_revision: bool = False) -> list[dict]:
    """Exact reruns are no-ops; changed or reviewed existing IDs need a revision."""
    result = {row["record_id"]: row for row in existing}
    if len(result) != len(existing):
        raise ValueError("reading_existing_duplicate_record")
    for row in incoming:
        previous = result.get(row["record_id"])
        # Unrelated monthly sampling/coverage can change the packet digest.
        # Keep the original creation provenance if this exact reading itself
        # did not change; never overwrite an older digest with a newer packet.
        content = lambda value: {key: item for key, item in value.items() if key != "input_digest"}
        if previous and digest(content(previous)) != digest(content(row)):
            old_review = (previous.get("review_history") or [{}])[-1]
            new_review = (row.get("review_history") or [{}])[-1]
            old_note, new_note = old_review.get("note", ""), new_review.get("note", "")
            notes_match = old_note == new_note or (bool(new_note) and old_note.startswith(new_note + " Previous draft: "))
            same_reading = (previous.get("content_digest") == row.get("content_digest")
                            and previous.get("review_status") == row.get("review_status")
                            and notes_match
                            and all(old_review.get(key) == new_review.get(key) for key in ("reviewer", "decision")))
            if same_reading:
                continue
            if (not allow_revision or previous.get("review_status") != "draft"
                    or old_review.get("reviewer") != "Codex AI source check; not a human review"):
                raise ValueError("reading_existing_record_changed_requires_revision")
            if row["updated_at"] <= previous["updated_at"]:
                raise ValueError("reading_revision_requires_later_timestamp")
            revised = copy.deepcopy(row)
            history = copy.deepcopy(new_review)
            history["note"] += " Previous draft: " + json.dumps({key: previous[key] for key in ("stance", "statement", "content_digest")}, ensure_ascii=False)
            history["review_id"] = "review:" + digest([row["record_id"], history["reviewed_at"], history["reviewer"], history["note"]])[:20]
            revised["created_at"] = previous["created_at"]
            revised["review_history"] = [*copy.deepcopy(previous["review_history"]), history]
            result[row["record_id"]] = revised
            continue
        result[row["record_id"]] = previous or row
    return [result[key] for key in sorted(result)]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--write", action="store_true", help="Persist drafts; never approve research evidence.")
    parser.add_argument("--revise", action="store_true", help="Explicitly revise this AI's drafts, preserving prior interpretation in review history.")
    args = parser.parse_args(argv)
    reading = json.loads(args.input.read_text())
    month = reading["month"]
    # Validate scope before resolving a month-controlled filesystem path.
    import re
    if not isinstance(month, str) or not re.fullmatch(r"20\d{2}-(0[1-9]|1[0-2])", month):
        raise ValueError("reading_month_invalid")
    catalog = load_catalog(CATALOG)
    snapshot = json.loads((API / "monthly" / f"{month}.json").read_text())
    from editorial_readings import load_reading_index
    manifest = json.loads((API / "catalog-manifest.json").read_text())
    reading_index = load_reading_index(catalog, CATALOG.parent / "hardware-review", manifest["data_through"])
    packet = build_evidence_packet(snapshot, catalog, reading_index=reading_index)
    incoming = compile_reading(reading, packet, catalog)
    path = EDITORIAL / "signal-evidence.jsonl"
    rows = merge_reading(read_jsonl(path), incoming, allow_revision=args.revise)
    if args.write:
        atomic_text(path, "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows))
    print(json.dumps({"month": month, "draft_count": len(incoming), "verified_count": 0,
                      "written": args.write, "input_digest": editorial_input_digest(packet)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
