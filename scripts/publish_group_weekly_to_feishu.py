#!/usr/bin/env python3
"""Publish the generated research-group weekly digest to Feishu.

Dry-run is the default-safe validation path.  Live publishing uses a dedicated
Feishu application identity from environment variables; it never reads or
stores a personal OAuth/refresh token.  ISO week is the idempotency key.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlencode, urlsplit


ROOT = Path(__file__).resolve().parents[1]
RADAR = ROOT / "data" / "research-group-radar.json"
DELIVERIES = ROOT / "data" / "feishu-weekly-deliveries.json"
API = "https://open.feishu.cn/open-apis"
INLINE_LINK = re.compile(r"\[((?:\\.|[^\]])+)\]\((?:<(https?://[^>]+)>|(https?://[^)\s]+))\)")


def read(path: Path, fallback):
    return json.loads(path.read_text()) if path.exists() else fallback


def api_request(method: str, endpoint: str, *, token: str | None = None, body=None, attempts: int = 3):
    data = json.dumps(body or {}, ensure_ascii=False).encode() if body is not None else None
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(f"{API}{endpoint}", data=data, headers=headers, method=method)
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = json.loads(response.read().decode())
            if payload.get("code", 0) != 0:
                raise RuntimeError(f"Feishu code={payload.get('code')} msg={payload.get('msg')}")
            return payload
        except (urllib.error.URLError, RuntimeError) as exc:
            if attempt == attempts - 1:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def tenant_token(app_id: str, app_secret: str) -> str:
    payload = api_request("POST", "/auth/v3/tenant_access_token/internal", body={"app_id": app_id, "app_secret": app_secret})
    token = payload.get("tenant_access_token")
    if not token:
        raise RuntimeError("Feishu tenant_access_token missing")
    return token


def plain_inline(text: str, *, trim: bool = True) -> str:
    text = INLINE_LINK.sub(lambda match: f"{match[1]}（{match[2] or match[3]}）", text)
    value = html.unescape(re.sub(r"\\([\\`*_\[\]{}|])", r"\1", text).replace("**", "").replace("`", ""))
    return value.strip() if trim else value


def inline_elements(text: str) -> list[dict]:
    elements, cursor = [], 0
    for match in INLINE_LINK.finditer(text):
        if match.start() > cursor:
            elements.append({"text_run": {"content": plain_inline(text[cursor:match.start()], trim=False)}})
        url = html.unescape(match[2] or match[3])
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Invalid public link in weekly report")
        elements.append({"text_run": {"content": plain_inline(match[1]), "text_element_style": {"link": {"url": url}}}})
        cursor = match.end()
    if cursor < len(text) or not elements:
        elements.append({"text_run": {"content": plain_inline(text[cursor:], trim=False)}})
    return [element for element in elements if element["text_run"]["content"]]


def index_summary(markdown: str) -> str:
    judgments, groups, in_findings = [], [], False
    period = next((line for line in markdown.splitlines() if line.startswith("覆盖北京时间")), "")
    period = period.split("；生成于")[0]
    for line in markdown.splitlines():
        if line.startswith("## "):
            in_findings = line == "## 本周判断"
        elif in_findings and line.startswith("- ") and len(judgments) < 3:
            judgments.append(plain_inline(line[2:]))
        elif line.startswith("### "):
            name = plain_inline(line[4:].split(" · ", 1)[0])
            if name not in groups:
                groups.append(name)
    pieces = [period, *judgments]
    if groups:
        pieces.append("重点研究组：" + "、".join(groups[:12]))
    return "；".join(piece for piece in pieces if piece) or "本周结构化更新见正文"


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
            blocks.append({"block_type": 3, "heading1": {"elements": inline_elements(line[2:])}})
        elif line.startswith("## "):
            blocks.append({"block_type": 4, "heading2": {"elements": inline_elements(line[3:])}})
        elif line.startswith("### "):
            blocks.append({"block_type": 5, "heading3": {"elements": inline_elements(line[4:])}})
        elif line.startswith("- "):
            blocks.append({"block_type": 12, "bullet": {"elements": inline_elements(line[2:])}})
        elif re.match(r"^\d+\.\s", line):
            blocks.append({"block_type": 13, "ordered": {"elements": inline_elements(re.sub(r'^\d+\.\s+', '', line))}})
        elif line.startswith("|"):
            # Feishu tables need hierarchical descendants.  The weekly digest
            # stays robust by rendering each row as readable plain text.
            cells = [plain_inline(cell) for cell in line.strip("|").split("|")]
            if all(re.fullmatch(r":?-+:?", cell) for cell in cells if cell):
                continue
            blocks.append({"block_type": 2, "text": {"elements": [{"text_run": {"content": " ｜ ".join(cells)}}]}})
        else:
            blocks.append({"block_type": 2, "text": {"elements": inline_elements(line)}})
    return blocks


def create_document(token: str, folder_token: str, title: str) -> tuple[str, str | None]:
    # Creation has no documented idempotency key here. Never blindly retry an
    # ambiguous create response and risk a second document for the same week.
    payload = api_request("POST", "/docx/v1/documents", token=token, body={"folder_token": folder_token, "title": title}, attempts=1)
    document = payload.get("data", {}).get("document", {})
    document_id = document.get("document_id")
    if not document_id:
        raise RuntimeError("Feishu document_id missing")
    # Resolve the actual tenant URL separately, AFTER persisting the ID. A
    # failed metadata lookup must not lose a successfully created document.
    return document_id, document.get("url")


def document_url(token: str, document_id: str) -> str:
    payload = api_request("POST", "/drive/v1/metas/batch_query", token=token,
                          body={"request_docs": [{"doc_token": document_id, "doc_type": "docx"}], "with_url": True})
    row = next((item for item in payload.get("data", {}).get("metas", []) if item.get("doc_token") == document_id), {})
    url = row.get("url") or ""
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise RuntimeError("document_url_unavailable")
    return url


def replace_document_blocks(token: str, document_id: str, blocks: list[dict], *, expected_title: str | None = None) -> None:
    doc = quote(document_id, safe="")
    if expected_title is not None:
        metadata = api_request("GET", f"/docx/v1/documents/{doc}", token=token).get("data", {}).get("document", {})
        if metadata.get("document_id") != document_id or metadata.get("title") != expected_title:
            raise RuntimeError("weekly_document_identity_mismatch")
    for attempt in range(3):
        try:
            root = api_request("GET", f"/docx/v1/documents/{doc}/blocks/{doc}", token=token).get("data", {}).get("block", {})
            if root.get("block_id") != document_id or root.get("block_type") != 1 or not isinstance(root.get("children", []), list):
                raise RuntimeError("document_root_unverified")
            child_count = len(root.get("children", []))
            if child_count:
                api_request("DELETE", f"/docx/v1/documents/{doc}/blocks/{doc}/children/batch_delete", token=token,
                            body={"start_index": 0, "end_index": child_count}, attempts=1)
            for start in range(0, len(blocks), 50):
                api_request("POST", f"/docx/v1/documents/{doc}/blocks/{doc}/children", token=token,
                            body={"children": blocks[start:start + 50], "index": -1}, attempts=1)
            return
        except Exception:
            if attempt == 2:
                raise
            # Re-read and replace the complete managed body; never blindly
            # repeat a positional append after an ambiguous response.
            time.sleep(2 ** attempt)


def append_index(token: str, index_document_id: str, week: str, title: str, doc_url: str, summary: str) -> str | None:
    content = f"{week} · [{title}](<{doc_url}>) · {summary}"
    block = {"block_type": 12, "bullet": {"elements": inline_elements(content)}}
    response = api_request(
        "POST",
        f"/docx/v1/documents/{quote(index_document_id, safe='')}/blocks/{quote(index_document_id, safe='')}/children",
        token=token,
        body={"children": [block], "index": -1},
        attempts=1,
    )
    children = response.get("data", {}).get("children", [])
    return children[0].get("block_id") if children else None


def upsert_index(token: str, index_document_id: str, week: str, title: str, doc_url: str, summary: str, *, allow_create: bool = True) -> str:
    prefix = f"{week} · {title}"
    matches, page_token, seen = [], None, set()
    while True:
        query = {"page_size": 500, **({"page_token": page_token} if page_token else {})}
        payload = api_request("GET", f"/docx/v1/documents/{quote(index_document_id, safe='')}/blocks?{urlencode(query)}", token=token).get("data", {})
        for block in payload.get("items", []):
            text = "".join(element.get("text_run", {}).get("content", "") for value in block.values() if isinstance(value, dict) for element in value.get("elements", []))
            if text.startswith(prefix) and text[len(prefix):].startswith(" · "):
                matches.append(block["block_id"])
        if not payload.get("has_more"):
            break
        page_token = payload.get("page_token")
        if not page_token or page_token in seen:
            raise RuntimeError("index_pagination_incomplete")
        seen.add(page_token)
    if len(matches) > 1:
        raise RuntimeError("duplicate_index_entries_require_review")
    if matches:
        elements = inline_elements(f"{week} · [{title}](<{doc_url}>) · {summary}")
        api_request("PATCH", f"/docx/v1/documents/{quote(index_document_id, safe='')}/blocks/{quote(matches[0], safe='')}", token=token,
                    body={"update_text_elements": {"elements": elements}})
        return matches[0]
    if not allow_create:
        raise RuntimeError("index_append_uncertain_requires_reconciliation")
    block_id = append_index(token, index_document_id, week, title, doc_url, summary)
    if not block_id:
        raise RuntimeError("index_append_uncertain_requires_reconciliation")
    return block_id


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--week")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    radar = read(RADAR, {})
    week = args.week or radar.get("latest_completed_week", {}).get("id")
    if not week:
        raise SystemExit("weekly radar has no completed week")
    page = ROOT / "docs" / "pulse" / "weekly" / f"{week.lower()}.md"
    if not page.exists():
        page = ROOT / "docs" / "groups" / "weekly" / f"{week.lower()}.md"
    if not page.exists():
        raise SystemExit(f"weekly page missing: {page}")
    markdown = page.read_text()
    title = f"具身智能关键研究组周报 · {week}"
    blocks = markdown_blocks(markdown)
    deliveries = read(DELIVERIES, {"version": "1.0", "deliveries": []})
    existing = next((item for item in deliveries["deliveries"] if item["week"] == week), None)
    summary = index_summary(markdown)
    content_hash = hashlib.sha256(json.dumps({"title": title, "blocks": blocks, "index_summary": summary}, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    if args.dry_run:
        print(json.dumps({"week": week, "title": title, "page": str(page), "blocks": len(blocks), "index_summary": summary, "content_hash": content_hash, "mode": "update" if existing else "create"}, ensure_ascii=False, indent=2))
        return
    if existing and existing.get("status") == "published" and existing.get("content_hash") == content_hash:
        print(json.dumps({"week": week, "status": "already_published_unchanged", "document_id": existing.get("document_id")}, ensure_ascii=False))
        return

    required = ["FEISHU_APP_ID", "FEISHU_APP_SECRET", "FEISHU_FOLDER_TOKEN", "FEISHU_INDEX_DOC_TOKEN"]
    if existing is None:
        existing = {"week": week, "status": "queued", "delivery_stage": "pending"}
        deliveries["deliveries"].append(existing)
    # Legacy successful deliveries already appended the index.
    if existing.get("status") == "published":
        existing.setdefault("index_status", "published")

    def persist(**changes):
        existing.update(changes, updated_at=datetime.now(timezone.utc).isoformat(), title=title)
        DELIVERIES.parent.mkdir(parents=True, exist_ok=True)
        pending = DELIVERIES.with_suffix(".json.tmp")
        pending.write_text(json.dumps(deliveries, ensure_ascii=False, indent=2) + "\n")
        pending.replace(DELIVERIES)

    missing = [name for name in required if not os.getenv(name)]
    if missing:
        persist(status="queued", retry_reason="missing_credentials", missing_configuration=missing)
        raise SystemExit("Feishu configuration missing; delivery queued without contacting Feishu.")
    try:
        if existing.get("delivery_stage") == "creating" and not existing.get("document_id"):
            raise RuntimeError("creation_uncertain_requires_reconciliation")
        index_uncertain = existing.get("index_status") == "appending"
        token = tenant_token(os.environ["FEISHU_APP_ID"], os.environ["FEISHU_APP_SECRET"])
        if not existing.get("document_id"):
            persist(status="pending", delivery_stage="creating")
            document_id, doc_url = create_document(token, os.environ["FEISHU_FOLDER_TOKEN"], title)
            # Save before any content writes; a failed body upload resumes the
            # same remote document on the next attempt.
            persist(document_id=document_id, doc_url=doc_url, delivery_stage="document_created")
        document_id, doc_url = existing["document_id"], existing.get("doc_url")
        if not doc_url:
            doc_url = document_url(token, document_id)
            persist(doc_url=doc_url)
        replace_document_blocks(token, document_id, blocks, expected_title=title)
        persist(status="pending", delivery_stage="content_written")
        persist(index_status="appending")
        index_block_id = upsert_index(token, os.environ["FEISHU_INDEX_DOC_TOKEN"], week, title, doc_url, summary, allow_create=not index_uncertain)
        persist(index_status="published", index_block_id=index_block_id)
        persist(status="published", delivery_stage="complete", retry_reason=None, content_hash=content_hash)
    except Exception as error:
        # Exception messages may contain remote identifiers; keep only a safe
        # category in logs and the durable retry queue.
        reason = str(error) if str(error) in {"creation_uncertain_requires_reconciliation", "index_append_uncertain_requires_reconciliation"} else type(error).__name__
        persist(status="queued", retry_reason=reason)
        raise SystemExit(f"Feishu delivery queued ({reason}); website publication remains unchanged.")
    print(json.dumps(existing, ensure_ascii=False))


if __name__ == "__main__":
    main()
