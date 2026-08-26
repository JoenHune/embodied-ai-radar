#!/usr/bin/env python3
"""Publish the generated research-group weekly digest to Feishu.

Dry-run is the default-safe validation path.  Live publishing uses a dedicated
Feishu application identity from environment variables; it never reads or
stores a personal OAuth/refresh token.  ISO week is the idempotency key.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RADAR = ROOT / "data" / "research-group-radar.json"
DELIVERIES = ROOT / "data" / "feishu-weekly-deliveries.json"
API = "https://open.feishu.cn/open-apis"


def read(path: Path, fallback):
    return json.loads(path.read_text()) if path.exists() else fallback


def api_request(method: str, endpoint: str, *, token: str | None = None, body=None):
    data = json.dumps(body or {}, ensure_ascii=False).encode() if body is not None else None
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(f"{API}{endpoint}", data=data, headers=headers, method=method)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = json.loads(response.read().decode())
            if payload.get("code", 0) != 0:
                raise RuntimeError(f"Feishu code={payload.get('code')} msg={payload.get('msg')}")
            return payload
        except (urllib.error.URLError, RuntimeError) as exc:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def tenant_token(app_id: str, app_secret: str) -> str:
    payload = api_request("POST", "/auth/v3/tenant_access_token/internal", body={"app_id": app_id, "app_secret": app_secret})
    token = payload.get("tenant_access_token")
    if not token:
        raise RuntimeError("Feishu tenant_access_token missing")
    return token


def plain_inline(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\1（\2）", text)
    return re.sub(r"[*_`]", "", text).strip()


def markdown_blocks(markdown: str) -> list[dict]:
    blocks = []
    first_h1 = True
    for raw in markdown.splitlines():
        line = raw.strip()
        if not line or line == "---" or line.startswith("<!--"):
            continue
        if line.startswith("# "):
            if first_h1:
                first_h1 = False
                continue
            blocks.append({"block_type": 3, "heading1": {"elements": [{"text_run": {"content": plain_inline(line[2:])}}]}})
        elif line.startswith("## "):
            blocks.append({"block_type": 4, "heading2": {"elements": [{"text_run": {"content": plain_inline(line[3:])}}]}})
        elif line.startswith("### "):
            blocks.append({"block_type": 5, "heading3": {"elements": [{"text_run": {"content": plain_inline(line[4:])}}]}})
        elif line.startswith("- "):
            blocks.append({"block_type": 12, "bullet": {"elements": [{"text_run": {"content": plain_inline(line[2:])}}]}})
        elif re.match(r"^\d+\.\s", line):
            blocks.append({"block_type": 13, "ordered": {"elements": [{"text_run": {"content": plain_inline(re.sub(r'^\d+\.\s+', '', line))}}]}})
        elif line.startswith("|"):
            # Feishu tables need hierarchical descendants.  The weekly digest
            # stays robust by rendering each row as readable plain text.
            cells = [plain_inline(cell) for cell in line.strip("|").split("|")]
            if all(re.fullmatch(r":?-+:?", cell) for cell in cells if cell):
                continue
            blocks.append({"block_type": 2, "text": {"elements": [{"text_run": {"content": " ｜ ".join(cells)}}]}})
        else:
            blocks.append({"block_type": 2, "text": {"elements": [{"text_run": {"content": plain_inline(line)}}]}})
    return blocks


def create_document(token: str, folder_token: str, title: str) -> tuple[str, str]:
    payload = api_request("POST", "/docx/v1/documents", token=token, body={"folder_token": folder_token, "title": title})
    document = payload.get("data", {}).get("document", {})
    document_id = document.get("document_id")
    if not document_id:
        raise RuntimeError("Feishu document_id missing")
    return document_id, f"https://alphaist.feishu.cn/docx/{document_id}"


def replace_document_blocks(token: str, document_id: str, blocks: list[dict]) -> None:
    payload = api_request("GET", f"/docx/v1/documents/{document_id}/blocks?page_size=500", token=token)
    items = payload.get("data", {}).get("items", [])
    child_count = max(0, len(items) - 1)
    if child_count:
        api_request(
            "DELETE",
            f"/docx/v1/documents/{document_id}/blocks/{document_id}/children/batch_delete",
            token=token,
            body={"start_index": 0, "end_index": child_count},
        )
    for start in range(0, len(blocks), 50):
        api_request(
            "POST",
            f"/docx/v1/documents/{document_id}/blocks/{document_id}/children",
            token=token,
            body={"children": blocks[start:start + 50], "index": -1},
        )


def append_index(token: str, index_document_id: str, week: str, title: str, doc_url: str, summary: str) -> None:
    content = f"{week} · {title} · {summary} · {doc_url}"
    block = {"block_type": 12, "bullet": {"elements": [{"text_run": {"content": content}}]}}
    api_request(
        "POST",
        f"/docx/v1/documents/{index_document_id}/blocks/{index_document_id}/children",
        token=token,
        body={"children": [block], "index": -1},
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--week")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    radar = read(RADAR, {})
    week = args.week or radar.get("latest_completed_week", {}).get("id")
    if not week:
        raise SystemExit("weekly radar has no completed week")
    page = ROOT / "docs" / "groups" / "weekly" / f"{week.lower()}.md"
    if not page.exists():
        raise SystemExit(f"weekly page missing: {page}")
    markdown = page.read_text()
    title = f"具身智能关键研究组周报 · {week}"
    blocks = markdown_blocks(markdown)
    deliveries = read(DELIVERIES, {"version": "1.0", "deliveries": []})
    existing = next((item for item in deliveries["deliveries"] if item["week"] == week), None)
    summary = f"{radar.get('tracking_group_count', 0)} 个研究组，本周结构化更新见正文"
    if args.dry_run:
        print(json.dumps({"week": week, "title": title, "page": str(page), "blocks": len(blocks), "mode": "update" if existing else "create"}, ensure_ascii=False, indent=2))
        return

    required = ["FEISHU_APP_ID", "FEISHU_APP_SECRET", "FEISHU_FOLDER_TOKEN", "FEISHU_INDEX_DOC_TOKEN"]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise SystemExit(f"missing Feishu environment variables: {', '.join(missing)}")
    token = tenant_token(os.environ["FEISHU_APP_ID"], os.environ["FEISHU_APP_SECRET"])
    if existing:
        document_id = existing["document_id"]
        doc_url = existing["doc_url"]
    else:
        document_id, doc_url = create_document(token, os.environ["FEISHU_FOLDER_TOKEN"], title)
    replace_document_blocks(token, document_id, blocks)
    if not existing:
        append_index(token, os.environ["FEISHU_INDEX_DOC_TOKEN"], week, title, doc_url, summary)
        existing = {"week": week, "document_id": document_id, "doc_url": doc_url}
        deliveries["deliveries"].append(existing)
    existing.update({"status": "published", "updated_at": radar.get("generated_at"), "title": title})
    DELIVERIES.write_text(json.dumps(deliveries, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(existing, ensure_ascii=False))


if __name__ == "__main__":
    main()
