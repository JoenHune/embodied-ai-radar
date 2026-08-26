#!/usr/bin/env python3
"""Monitor official research-group sources and emit attribution candidates.

The collector is intentionally conservative.  It extracts links from official
pages, but only sources explicitly marked as publications/projects can emit G1
candidates.  Home/people/hiring pages emit G3 observations and therefore never
enter public research claims without review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
ORGS = ROOT / "config" / "organizations.json"
STATE = ROOT / "data" / "group-source-status.json"
CANDIDATES = ROOT / "data" / "group-update-candidates.json"
RAW = ROOT / "data" / "raw" / "organizations"
WORKS = ROOT / "data" / "works.json"
USER_AGENT = "embodied-ai-radar-group-monitor/1.0 research-radar@example.com"

RESEARCH_HINT = re.compile(
    r"arxiv|publication|paper|project|research|model|dataset|benchmark|github|huggingface|technical[- ]report|robot",
    re.I,
)
DATE_HINT = re.compile(r"\b(20\d{2})[-/.](0?[1-9]|1[0-2])(?:[-/.]([0-2]?\d|3[01]))?\b")
SOURCE_META = {
    "publications": ("official_group_publications", "G1", "preprint"),
    "projects": ("official_group_projects", "G1", "project"),
    "research": ("official_group_research", "G1", "project"),
    "models": ("official_group_models", "G1", "model_release"),
    "datasets": ("official_group_datasets", "G1", "dataset_release"),
    "code": ("official_group_code", "G1", "code_release"),
    "github": ("official_github", "G1", "code_release"),
    "people": ("official_people", "G3", "personnel_change"),
    "hiring": ("official_hiring", "G3", "hiring_signal"),
    "home": ("official_home", "G3", "project"),
    "blog": ("official_blog", "G3", "project"),
}


def source_meta(kind: str):
    if kind in SOURCE_META:
        return SOURCE_META[kind]
    if kind.startswith("source_"):
        return ("official_other", "G3", "project")
    return None


class LinkParser(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self.in_anchor = False
        self.href = ""
        self.text_parts: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        self.in_anchor = True
        self.href = dict(attrs).get("href") or ""
        self.text_parts = []

    def handle_data(self, data):
        if self.in_anchor:
            self.text_parts.append(data)

    def handle_endtag(self, tag):
        if tag.lower() != "a" or not self.in_anchor:
            return
        url = urljoin(self.base_url, self.href)
        title = re.sub(r"\s+", " ", " ".join(self.text_parts)).strip()
        if url.startswith(("http://", "https://")) and title:
            self.links.append((title, url))
        self.in_anchor = False


def canonical_url(value: str) -> str:
    parts = urlsplit(value)
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), "", ""))


def source_id(org_id: str, kind: str, url: str) -> str:
    digest = hashlib.sha1(f"{org_id}|{kind}|{canonical_url(url)}".encode()).hexdigest()[:12]
    return f"source:{digest}"


def fetch(url: str, timeout: int) -> tuple[bytes, str]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read(), response.headers.get("Content-Type", "")
        except (urllib.error.URLError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("unreachable")


def extract_date(title: str, url: str) -> tuple[str | None, str]:
    match = DATE_HINT.search(f"{title} {url}")
    if not match:
        return None, "unknown"
    year, month, day = match.groups()
    if day:
        return f"{int(year):04d}-{int(month):02d}-{int(day):02d}", "day"
    return f"{int(year):04d}-{int(month):02d}-01", "month"


def likely_research_link(title: str, url: str) -> bool:
    if not RESEARCH_HINT.search(f"{title} {url}"):
        return False
    if url.lower().startswith(("mailto:", "javascript:")):
        return False
    return True


def normalize_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def extract_arxiv_id(value: str) -> str | None:
    match = re.search(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})", value, re.I)
    return match.group(1) if match else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bootstrap", action="store_true", help="record current links without emitting candidates")
    parser.add_argument("--backfill-known-works", action="store_true", help="emit only official links that match an existing canonical work")
    parser.add_argument("--reemit-known", action="store_true", help="re-evaluate known links during a controlled backfill")
    parser.add_argument("--kinds", help="comma-separated official URL kinds to monitor")
    parser.add_argument("--dry-run", action="store_true", help="fetch and report without writing state")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--max-sources", type=int)
    parser.add_argument("--as-of", default=date.today().isoformat())
    args = parser.parse_args()

    registry = json.loads(ORGS.read_text())
    works = json.loads(WORKS.read_text()) if args.backfill_known_works else []
    by_arxiv = {row.get("arxiv_id"): row for row in works if row.get("arxiv_id")}
    by_title = {normalize_title(row.get("title", "")): row for row in works if row.get("title")}
    selected_kinds = set(args.kinds.split(",")) if args.kinds else None
    previous = json.loads(STATE.read_text()) if STATE.exists() else {"sources": []}
    prior_by_id = {row["source_id"]: row for row in previous.get("sources", [])}
    sources = []
    for org in registry["organizations"]:
        if not org.get("tracking_unit"):
            continue
        for kind, url in (org.get("official_urls") or {}).items():
            if not url or not source_meta(kind) or (selected_kinds and kind not in selected_kinds):
                continue
            sources.append((org, kind, url))
    if args.max_sources:
        sources = sources[: args.max_sources]

    now = datetime.now(timezone.utc).isoformat()
    status_rows = []
    candidate_rows = []
    for index, (org, kind, url) in enumerate(sources, 1):
        sid = source_id(org["organization_id"], kind, url)
        prior = prior_by_id.get(sid, {})
        source_type, grade, update_type = source_meta(kind)
        row = {
            "source_id": sid,
            "organization_id": org["organization_id"],
            "kind": kind,
            "url": url,
            "source_type": source_type,
            "attribution_grade": grade,
            "last_checked": now,
            "last_success": prior.get("last_success"),
            "consecutive_failures": prior.get("consecutive_failures", 0),
            "content_hash": prior.get("content_hash"),
            "known_links": prior.get("known_links", []),
            "status": prior.get("status", "unverified"),
            "error": None,
            "last_failure_date": prior.get("last_failure_date"),
        }
        try:
            raw_dir = RAW / org["organization_id"].removeprefix("org:")
            raw_dir.mkdir(parents=True, exist_ok=True)
            raw_path = raw_dir / f"{sid.removeprefix('source:')}-{args.as_of}.html"
            if raw_path.exists():
                body, content_type = raw_path.read_bytes(), "text/html"
            else:
                body, content_type = fetch(url, args.timeout)
            digest = hashlib.sha256(body).hexdigest()
            text = body.decode("utf-8", errors="replace")
            parsed_links = []
            if "html" in content_type.lower() or "<html" in text[:1000].lower():
                link_parser = LinkParser(url)
                link_parser.feed(text)
                parsed_links = [
                    {"title": title, "url": canonical_url(link)}
                    for title, link in link_parser.links
                    if likely_research_link(title, link)
                ]
            unique = {item["url"]: item for item in parsed_links}
            old_links = set(row["known_links"])
            new_links = list(unique.values()) if args.reemit_known else [item for key, item in unique.items() if key not in old_links]
            if not args.bootstrap:
                for item in new_links:
                    matched_work = None
                    if args.backfill_known_works:
                        arxiv_id = extract_arxiv_id(item["url"])
                        matched_work = by_arxiv.get(arxiv_id) if arxiv_id else None
                        if not matched_work:
                            matched_work = by_title.get(normalize_title(item["title"]))
                        if not matched_work:
                            continue
                    published_at, precision = extract_date(item["title"], item["url"])
                    if matched_work:
                        published_at = matched_work.get("first_public_date")
                        precision = matched_work.get("first_public_date_precision") or precision
                    candidate_rows.append(
                        {
                            "organization_id": org["organization_id"],
                            "title": (matched_work or {}).get("title") or item["title"],
                            "url": item["url"],
                            "published_at": published_at,
                            "date_precision": precision,
                            "update_type": update_type,
                            "evidence_grade": grade,
                            "source_type": source_type,
                            "direction_codes": [],
                            "question_codes": [],
                            "summary_zh": "官方来源页面新发现的链接，等待结构化归类。",
                            "first_seen_at": args.as_of,
                            "work_id": (matched_work or {}).get("work_id"),
                        }
                    )
            raw_path.write_bytes(body)
            row.update(
                {
                    "last_success": now,
                    "consecutive_failures": 0,
                    "content_hash": digest,
                    "known_links": sorted(unique),
                    "status": "healthy",
                    "last_failure_date": None,
                }
            )
            print(f"group source {index}/{len(sources)} ok: {org['display_name']} {kind} (+{len(new_links)})")
        except Exception as exc:
            already_failed_this_snapshot = str(prior.get("last_checked") or "").startswith(args.as_of)
            failures = 1 if already_failed_this_snapshot else row["consecutive_failures"] + 1
            row.update(
                {
                    "consecutive_failures": failures,
                    "status": "stale" if failures >= 2 else "partial",
                    "error": f"{type(exc).__name__}: {exc}",
                    "last_failure_date": args.as_of,
                }
            )
            print(f"group source {index}/{len(sources)} failed: {org['display_name']} {kind}: {exc}")
        status_rows.append(row)

    if args.dry_run:
        print(json.dumps({"sources": len(status_rows), "candidates": len(candidate_rows)}, ensure_ascii=False))
        return
    STATE.write_text(json.dumps({"version": "1.0", "generated_at": args.as_of, "sources": status_rows}, ensure_ascii=False, indent=2) + "\n")
    existing = json.loads(CANDIDATES.read_text()) if CANDIDATES.exists() else {"candidates": []}
    merged = {f"{item['organization_id']}|{canonical_url(item['url'])}": item for item in existing.get("candidates", [])}
    for item in candidate_rows:
        merged[f"{item['organization_id']}|{canonical_url(item['url'])}"] = item
    CANDIDATES.write_text(json.dumps({"version": "1.0", "generated_at": args.as_of, "candidates": sorted(merged.values(), key=lambda item: (item["organization_id"], item["url"]))}, ensure_ascii=False, indent=2) + "\n")
    print(f"Saved {len(status_rows)} source states and {len(candidate_rows)} new candidates")


if __name__ == "__main__":
    main()
