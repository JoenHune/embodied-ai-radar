#!/usr/bin/env python3
"""Collect official accepted/program records whose proceedings are not yet final.

These records expand discovery and July coverage but are explicitly excluded
from strict peer-reviewed-proceedings counts.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

from radar_common import (
    ROOT,
    canonical_work_id,
    classify_research,
    clean_text,
    normalize_title,
)

RAW = ROOT / "data" / "raw" / "official-programs"
OUTPUT = ROOT / "data" / "official-programs.json"
COVERAGE = ROOT / "data" / "official-program-coverage.json"
RAW.mkdir(parents=True, exist_ok=True)
SNAPSHOT_DATE = json.loads(
    (ROOT / "config" / "source-registry.json").read_text()
)["window"]["until"]
USER_AGENT = "embodied-ai-radar/2.0 research-radar@example.com"
FETCH_AUDIT: list[dict] = []


def fetch(url: str, cache_name: str) -> str:
    stem, dot, suffix = cache_name.rpartition(".")
    dated_name = (
        f"{stem}-through-{SNAPSHOT_DATE}.{suffix}"
        if dot
        else f"{cache_name}-through-{SNAPSHOT_DATE}"
    )
    cache = RAW / dated_name
    if cache.exists() and cache.stat().st_size > 100:
        FETCH_AUDIT.append({"cache_name": cache_name, "status": "current_snapshot_cache"})
        return cache.read_text(errors="replace")
    prior_cache = RAW / cache_name
    # PaperCept's multi-megabyte content pages can be too slow for a full
    # repeated transfer. Revalidate the live URL, then parse the previously
    # checksummed body and disclose that provenance in coverage metadata.
    if prior_cache.exists() and prior_cache.stat().st_size > 1_000_000:
        head = subprocess.run(
            [
                "curl", "--fail", "--location", "--silent", "--show-error",
                "--head", "--max-time", "30", "--user-agent", USER_AGENT, url,
            ],
            capture_output=True,
        )
        if head.returncode == 0:
            FETCH_AUDIT.append(
                {"cache_name": cache_name, "status": "live_url_revalidated_prior_body"}
            )
            return prior_cache.read_text(errors="replace")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                body = response.read().decode("utf-8", errors="replace")
            cache.write_text(body)
            FETCH_AUDIT.append({"cache_name": cache_name, "status": "fresh_body"})
            time.sleep(1.1)
            return body
        except Exception:
            # The system Python on some macOS hosts only offers an older TLS
            # stack. curl uses the current system transport and keeps the
            # source refresh reproducible without weakening TLS.
            try:
                result = subprocess.run(
                    [
                        "curl", "--fail", "--location", "--silent",
                        "--show-error", "--max-time", "120",
                        "--user-agent", USER_AGENT, url,
                    ],
                    check=True,
                    capture_output=True,
                )
                body = result.stdout.decode("utf-8", errors="replace")
                cache.write_text(body)
                FETCH_AUDIT.append({"cache_name": cache_name, "status": "fresh_body"})
                return body
            except subprocess.CalledProcessError:
                if prior_cache.exists() and prior_cache.stat().st_size > 100:
                    FETCH_AUDIT.append(
                        {"cache_name": cache_name, "status": "live_fetch_failed_prior_body"}
                    )
                    return prior_cache.read_text(errors="replace")
                if attempt == 4:
                    raise
                time.sleep(3 * (attempt + 1))
    raise RuntimeError("unreachable")


def classify_record(record: dict) -> dict:
    result = classify_research(
        title=record["title"],
        abstract=record.get("abstract") or "",
        extra_text=" ".join(record.get("keywords") or []),
        source_is_robotics=True,
    )
    record["primary_topic"] = result.pop("primary_topic")
    record["topics"] = result.pop("topics")
    record["tags"] = result.pop("tags")
    record["topic_scores"] = result.pop("topic_scores")
    record["relevance"] = result
    return record


def collect_icra_2026() -> list[dict]:
    base = "https://ras.papercept.net/conferences/conferences/ICRA26/program/"
    records = {}
    source_pages = []
    for day in range(1, 7):
        url = f"{base}ICRA26_ContentListWeb_{day}.html"
        body = fetch(url, f"icra26-day-{day}.html")
        source_pages.append(
            {
                "url": url,
                "sha256": hashlib.sha256(body.encode()).hexdigest(),
            }
        )
        soup = BeautifulSoup(body, "html.parser")
        for header in soup.select("tr.pHdr"):
            header_text = clean_text(header.get_text(" ", strip=True))
            match = re.search(r"Paper\s+([A-Za-z0-9.]+)", header_text)
            if not match:
                continue
            paper_code = match.group(1)
            siblings = []
            for sibling in header.find_next_siblings("tr"):
                if "pHdr" in (sibling.get("class") or []):
                    break
                siblings.append(sibling)
            title_node = next(
                (node.select_one("span.pTtl") for node in siblings if node.select_one("span.pTtl")),
                None,
            )
            if not title_node:
                continue
            title = clean_text(title_node.get_text(" ", strip=True))
            authors = []
            institutions = []
            keywords = []
            abstract = ""
            for node in siblings:
                author_anchor = node.select_one('a[href*="AuthorIndexWeb.html#"]')
                if author_anchor:
                    raw_name = clean_text(author_anchor.get_text(" ", strip=True))
                    if "," in raw_name:
                        family, given = [part.strip() for part in raw_name.split(",", 1)]
                        raw_name = f"{given} {family}".strip()
                    if raw_name and raw_name not in authors:
                        authors.append(raw_name)
                    cells = node.find_all("td")
                    if len(cells) > 1:
                        institution = clean_text(cells[-1].get_text(" ", strip=True))
                        if institution and institution not in institutions:
                            institutions.append(institution)
                abstract_node = node.select_one('div[id^="Ab"]')
                if abstract_node:
                    keyword_links = abstract_node.select('a[href*="KeywordIndexWeb.html#"]')
                    keywords = [clean_text(link.get_text(" ", strip=True)) for link in keyword_links]
                    text = clean_text(abstract_node.get_text(" ", strip=True))
                    abstract = re.sub(r"^Keywords:\s*.*?\s+Abstract:\s*", "", text, flags=re.I)
            official_url = f"{url}#{header.select_one('a[name]').get('name')}"
            record = {
                "program_id": f"ICRA26:{paper_code}",
                "work_id": canonical_work_id(
                    title=title,
                    first_author=(authors or [None])[0],
                    year=2026,
                ),
                "title": title,
                "authors": authors,
                "institutions": institutions,
                "abstract": abstract,
                "keywords": keywords,
                "venue": "ICRA",
                "year": 2026,
                "publication_type": "conference_program",
                "official_url": official_url,
                "official_container_url": url,
                "verification_status": "official_program_only",
                "strict_peer_reviewed": False,
            }
            records.setdefault(normalize_title(title), classify_record(record))
    return list(records.values()), source_pages


def collect_rss_2026() -> tuple[list[dict], list[dict]]:
    url = "https://roboticsconference.org/program/papers/"
    body = fetch(url, "rss26-accepted.html")
    soup = BeautifulSoup(body, "html.parser")
    records = []
    for row in soup.select("table#myTable tr[session]"):
        cells = row.find_all("td", recursive=False)
        if len(cells) < 4:
            continue
        paper_id = clean_text(cells[0].get_text(" ", strip=True))
        session = clean_text(cells[1].get_text(" ", strip=True))
        title = clean_text(cells[2].get_text(" ", strip=True))
        author_cell = cells[3]
        hidden = author_cell.select_one("div.content")
        if hidden:
            hidden.extract()
        authors = [
            clean_text(name)
            for name in clean_text(author_cell.get_text(" ", strip=True)).split(",")
            if clean_text(name)
        ]
        link = cells[2].select_one("a[href]")
        official_url = urllib.parse.urljoin(url, link.get("href")) if link else url
        record = {
            "program_id": f"RSS26:{paper_id}",
            "work_id": canonical_work_id(
                title=title,
                first_author=(authors or [None])[0],
                year=2026,
            ),
            "title": title,
            "authors": authors,
            "institutions": [],
            "abstract": "",
            "keywords": [session],
            "session": session,
            "venue": "RSS",
            "year": 2026,
            "publication_type": "accepted_paper",
            "official_url": official_url,
            "official_container_url": url,
            "verification_status": "official_accepted_pending_proceedings",
            "strict_peer_reviewed": False,
        }
        records.append(classify_record(record))
    return records, [{"url": url, "sha256": hashlib.sha256(body.encode()).hexdigest()}]


def main() -> None:
    icra, icra_pages = collect_icra_2026()
    rss, rss_pages = collect_rss_2026()
    if not (2500 <= len(icra) <= 3500):
        raise SystemExit(f"unexpected ICRA 2026 program count: {len(icra)}")
    if len(rss) != 210:
        raise SystemExit(f"unexpected RSS 2026 accepted count: {len(rss)}")
    records = sorted([*icra, *rss], key=lambda row: (row["venue"], row["title"]))
    OUTPUT.write_text(
        json.dumps(records, ensure_ascii=False, separators=(",", ":")) + "\n"
    )
    coverage = {
        "generated_at": SNAPSHOT_DATE,
        "records": len(records),
        "by_venue": dict(Counter(record["venue"] for record in records)),
        "by_status": dict(
            Counter(record["verification_status"] for record in records)
        ),
        "relevance_screen": dict(
            Counter(record["relevance"]["status"] for record in records)
        ),
        "strict_peer_reviewed_records": 0,
        "source_pages": [*icra_pages, *rss_pages],
        "source_refresh": FETCH_AUDIT,
        "warning": (
            "ICRA 2026 records are official program entries, not verified proceedings. "
            "RSS 2026 records are accepted papers pending an official proceedings volume. "
            "Neither enters the strict peer-review coverage numerator."
        ),
    }
    COVERAGE.write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n")
    print(
        f"Saved {len(icra)} ICRA 2026 program records and "
        f"{len(rss)} RSS 2026 pending acceptances.",
        flush=True,
    )


if __name__ == "__main__":
    main()
