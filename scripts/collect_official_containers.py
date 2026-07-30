#!/usr/bin/env python3
"""Collect complete official RSS and CoRL proceedings containers.

These static official sources are the strict peer-review evidence layer. DBLP,
Crossref, OpenAlex, and Semantic Scholar remain discovery/enrichment sources.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

from bs4 import BeautifulSoup

from radar_common import ROOT, canonical_work_id, classify_research, clean_text

RAW = ROOT / "data" / "raw" / "official-containers"
OUTPUT = ROOT / "data" / "official-proceedings.json"
COVERAGE = ROOT / "data" / "official-container-coverage.json"
RAW.mkdir(parents=True, exist_ok=True)
USER_AGENT = "embodied-ai-radar/2.0 research-radar@example.com"
SNAPSHOT_DATE = "2026-07-29"

CONTAINERS = [
    {
        "container_id": "rss20",
        "venue": "RSS",
        "event_year": 2024,
        "bibliographic_year": 2024,
        "publication_date": "2024-07-15",
        "url": "https://www.roboticsproceedings.org/rss20/",
        "parser": "rss",
        "expected_count": 134,
    },
    {
        "container_id": "rss21",
        "venue": "RSS",
        "event_year": 2025,
        "bibliographic_year": 2025,
        "publication_date": "2025-06-21",
        "url": "https://www.roboticsproceedings.org/rss21/",
        "parser": "rss",
        "expected_count": 163,
    },
    {
        "container_id": "pmlr-v270",
        "venue": "CoRL",
        "event_year": 2024,
        "bibliographic_year": 2025,
        "publication_date": "2025-01-12",
        "url": "https://proceedings.mlr.press/v270/",
        "parser": "pmlr",
        "expected_count": 264,
    },
    {
        "container_id": "pmlr-v305",
        "venue": "CoRL",
        "event_year": 2025,
        "bibliographic_year": 2025,
        "publication_date": "2025-10-07",
        "url": "https://proceedings.mlr.press/v305/",
        "parser": "pmlr",
        "expected_count": 263,
    },
]


def fetch(container: dict) -> str:
    cache = RAW / f"{container['container_id']}.html"
    if cache.exists() and cache.stat().st_size > 1000:
        return cache.read_text(errors="replace")
    request = urllib.request.Request(container["url"], headers={"User-Agent": USER_AGENT})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                body = response.read().decode("utf-8", errors="replace")
            cache.write_text(body)
            time.sleep(1.1)
            return body
        except (urllib.error.URLError, TimeoutError):
            if attempt == 5:
                raise
            time.sleep(3 * (attempt + 1))
    raise RuntimeError("unreachable")


def parse_authors(text: str) -> list[str]:
    return [
        clean_text(author)
        for author in re.split(r"\s*,\s*", clean_text(text))
        if clean_text(author)
    ]


def base_record(container: dict, title: str, authors: list[str], official_url: str) -> dict:
    work_id = canonical_work_id(
        title=title,
        first_author=(authors or [None])[0],
        year=container["event_year"],
    )
    classification = classify_research(
        title=title,
        source_is_robotics=True,
        extra_text=container["venue"],
    )
    return {
        "publication_id": (
            f"official:{container['container_id']}:"
            f"{hashlib.sha1(official_url.encode()).hexdigest()[:16]}"
        ),
        "work_id": work_id,
        "title": title,
        "authors": authors,
        "abstract": "",
        "venue": container["venue"],
        "event_year": container["event_year"],
        "bibliographic_year": container["bibliographic_year"],
        "publication_date": container["publication_date"],
        "date_precision": "day",
        "publication_type": "conference",
        "official_url": official_url,
        "official_container_url": container["url"],
        "container_id": container["container_id"],
        "verification_status": "peer_reviewed_official_proceedings",
        "doi": None,
        "arxiv_id": None,
        "primary_topic": classification.pop("primary_topic"),
        "topics": classification.pop("topics"),
        "tags": classification.pop("tags"),
        "topic_scores": classification.pop("topic_scores"),
        "relevance": classification,
    }


def parse_rss(container: dict, body: str) -> list[dict]:
    soup = BeautifulSoup(body, "html.parser")
    rows = []
    seen = set()
    for anchor in soup.select("div.content a[href]"):
        href = anchor.get("href", "")
        if not re.fullmatch(r"p\d{3}\.html", href):
            continue
        official_url = urllib.parse.urljoin(container["url"], href)
        if official_url in seen:
            continue
        seen.add(official_url)
        title = clean_text(anchor.get_text(" ", strip=True))
        parent = anchor.find_parent("td")
        author_node = parent.find("i") if parent else None
        authors = parse_authors(author_node.get_text(" ", strip=True) if author_node else "")
        rows.append(base_record(container, title, authors, official_url))
    return rows


def parse_pmlr(container: dict, body: str) -> list[dict]:
    soup = BeautifulSoup(body, "html.parser")
    rows = []
    for paper in soup.select("div.paper"):
        title_node = paper.select_one("p.title")
        authors_node = paper.select_one("span.authors")
        if not title_node:
            continue
        title = clean_text(title_node.get_text(" ", strip=True))
        authors = parse_authors(authors_node.get_text(" ", strip=True) if authors_node else "")
        links = [
            anchor.get("href")
            for anchor in paper.select("p.links a[href]")
            if anchor.get("href")
        ]
        official_url = next(
            (
                link
                for link in links
                if link.startswith("https://proceedings.mlr.press/")
                and link.endswith(".html")
            ),
            container["url"],
        )
        rows.append(base_record(container, title, authors, official_url))
    return rows


def main() -> None:
    records = []
    manifests = []
    for container in CONTAINERS:
        body = fetch(container)
        rows = (
            parse_rss(container, body)
            if container["parser"] == "rss"
            else parse_pmlr(container, body)
        )
        actual = len(rows)
        expected = container["expected_count"]
        complete = actual == expected
        manifests.append(
            {
                **container,
                "observed_count": actual,
                "complete": complete,
                "content_sha256": hashlib.sha256(body.encode()).hexdigest(),
                "fetched_at": SNAPSHOT_DATE,
            }
        )
        print(
            f"{container['container_id']}: {actual}/{expected} "
            f"{'complete' if complete else 'INCOMPLETE'}",
            flush=True,
        )
        if not complete:
            raise SystemExit(
                f"official container count mismatch for {container['container_id']}: "
                f"{actual} != {expected}"
            )
        records.extend(rows)
    OUTPUT.write_text(
        json.dumps(records, ensure_ascii=False, separators=(",", ":")) + "\n"
    )
    coverage = {
        "generated_at": SNAPSHOT_DATE,
        "strict_official_records": len(records),
        "containers_complete": sum(item["complete"] for item in manifests),
        "containers_expected": len(manifests),
        "by_venue": {
            venue: len([record for record in records if record["venue"] == venue])
            for venue in sorted({record["venue"] for record in records})
        },
        "relevance_screen": {
            status: len(
                [record for record in records if record["relevance"]["status"] == status]
            )
            for status in ["included", "candidate", "manual_review", "excluded"]
        },
        "manifests": manifests,
        "method_note": (
            "Every record is present in a complete official proceedings container. "
            "Relevance is a title-level automated screen until abstract enrichment."
        ),
    }
    COVERAGE.write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n")
    print(f"Saved {len(records)} strict official proceedings records.", flush=True)


if __name__ == "__main__":
    main()
