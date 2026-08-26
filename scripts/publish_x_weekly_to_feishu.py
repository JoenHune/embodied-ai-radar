#!/usr/bin/env python3
"""Publish the X discussion weekly report to Feishu with ISO-week idempotency."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from publish_group_weekly_to_feishu import (
    append_index,
    create_document,
    markdown_blocks,
    read,
    replace_document_blocks,
    tenant_token,
)


ROOT = Path(__file__).resolve().parents[1]
WEEKLY = ROOT / "data" / "x-weekly-discussions.json"
DELIVERIES = ROOT / "data" / "feishu-x-weekly-deliveries.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--week")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    weekly = read(WEEKLY, {})
    week_id = args.week or weekly.get("latest_week")
    if not week_id:
        raise SystemExit("X weekly radar has no completed week")
    week = next((row for row in weekly.get("weeks", []) if row.get("week_id") == week_id), None)
    if not week:
        raise SystemExit(f"X weekly data missing: {week_id}")
    page = ROOT / "docs" / "social" / "weekly" / f"{week_id.lower()}.md"
    if not page.exists():
        raise SystemExit(f"X weekly page missing: {page}")
    title = f"具身智能 X 讨论周报 · {week_id}"
    blocks = markdown_blocks(page.read_text())
    deliveries = read(DELIVERIES, {"version": "1.0", "deliveries": []})
    existing = next((item for item in deliveries["deliveries"] if item["week"] == week_id), None)
    summary = f"{week.get('post_count', 0)} 项 Post，{week.get('ranked_topic_count', 0)} 个热点讨论簇"
    if args.dry_run:
        print(json.dumps({"week": week_id, "title": title, "page": str(page), "blocks": len(blocks), "mode": "update" if existing else "create", "status": week.get("status")}, ensure_ascii=False, indent=2))
        return

    required = ["FEISHU_APP_ID", "FEISHU_APP_SECRET", "FEISHU_FOLDER_TOKEN", "FEISHU_X_INDEX_DOC_TOKEN"]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise SystemExit(f"missing Feishu environment variables: {', '.join(missing)}")
    token = tenant_token(os.environ["FEISHU_APP_ID"], os.environ["FEISHU_APP_SECRET"])
    if existing:
        document_id, doc_url = existing["document_id"], existing["doc_url"]
    else:
        document_id, doc_url = create_document(token, os.environ["FEISHU_FOLDER_TOKEN"], title)
    replace_document_blocks(token, document_id, blocks)
    if not existing:
        append_index(token, os.environ["FEISHU_X_INDEX_DOC_TOKEN"], week_id, title, doc_url, summary)
        existing = {"week": week_id, "document_id": document_id, "doc_url": doc_url}
        deliveries["deliveries"].append(existing)
    existing.update({"status": "published", "updated_at": weekly.get("generated_at"), "title": title})
    DELIVERIES.write_text(json.dumps(deliveries, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(existing, ensure_ascii=False))


if __name__ == "__main__":
    main()
