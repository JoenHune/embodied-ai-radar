#!/usr/bin/env python3
"""Paginated multi-query arXiv collection for the expanded research radar.

Unlike the legacy fallback, this collector:
- fetches all cs.RO records in the window;
- supplements cs.AI/cs.CV/cs.LG with robot/embodied queries;
- follows pagination and caches every page for resumability;
- keeps the mother corpus and attaches relevance states instead of discarding
  low-confidence records during collection.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

from radar_common import ROOT, canonical_work_id, classify_research, clean_text, normalize_doi

REGISTRY = json.loads((ROOT / "config" / "source-registry.json").read_text())
RAW = ROOT / "data" / "raw" / "arxiv-v2"
OUTPUT = ROOT / "data" / "preprints.json"
COVERAGE = ROOT / "data" / "preprint-coverage.json"
RAW.mkdir(parents=True, exist_ok=True)
ATOM = {
    "a": "http://www.w3.org/2005/Atom",
    "x": "http://arxiv.org/schemas/atom",
    "o": "http://a9.com/-/spec/opensearch/1.1/",
}
USER_AGENT = "embodied-ai-radar/2.0 research-radar@example.com"


def month_keys() -> list[str]:
    start = REGISTRY["window"]["from"][:7]
    end = REGISTRY["window"]["until"][:7]
    year, month = map(int, start.split("-"))
    keys = []
    while True:
        key = f"{year:04d}-{month:02d}"
        keys.append(key)
        if key == end:
            return keys
        month += 1
        if month == 13:
            year += 1
            month = 1


def month_bounds(key: str) -> tuple[str, str]:
    year, month = map(int, key.split("-"))
    if month == 12:
        next_date = date(year + 1, 1, 1)
    else:
        next_date = date(year, month + 1, 1)
    last = next_date - timedelta(days=1)
    if key == REGISTRY["window"]["until"][:7]:
        last = date.fromisoformat(REGISTRY["window"]["until"])
    return f"{key.replace('-', '')}01000000", f"{last:%Y%m%d}235959"


def fetch(query_id: str, query: str, month: str, start: int, page_size: int) -> str:
    cache = RAW / f"{month}-{query_id}-{start:05d}.xml"
    if cache.exists() and cache.stat().st_size > 1000:
        return cache.read_text()
    lower, upper = month_bounds(month)
    full_query = f"({query}) AND submittedDate:[{lower} TO {upper}]"
    params = urllib.parse.urlencode(
        {
            "search_query": full_query,
            "start": start,
            "max_results": page_size,
            "sortBy": "submittedDate",
            "sortOrder": "ascending",
        }
    )
    url = f"https://export.arxiv.org/api/query?{params}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(7):
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                body = response.read().decode("utf-8")
            if "<feed" not in body:
                raise RuntimeError("arXiv returned an empty/non-feed response")
            cache.write_text(body)
            time.sleep(3.1)
            return body
        except urllib.error.HTTPError as exc:
            if attempt == 6:
                raise
            delay = min(
                int(exc.headers.get("Retry-After", "20")) if exc.code == 429 else 5 * (attempt + 1),
                90,
            )
            print(f"arXiv HTTP {exc.code}; retry in {delay}s", file=sys.stderr, flush=True)
            time.sleep(delay)
        except Exception as exc:
            if attempt == 6:
                raise
            delay = min(5 * (attempt + 1), 60)
            print(f"arXiv {type(exc).__name__}; retry in {delay}s", file=sys.stderr, flush=True)
            time.sleep(delay)
    raise RuntimeError("unreachable")


def parse_feed(body: str) -> tuple[int, list[dict]]:
    root = ET.fromstring(body)
    total = int(root.findtext("o:totalResults", default="0", namespaces=ATOM))
    rows = []
    for entry in root.findall("a:entry", ATOM):
        raw_id = clean_text(entry.findtext("a:id", namespaces=ATOM))
        match = re.search(r"/(\d{4}\.\d{4,5})(?:v\d+)?$", raw_id)
        if not match:
            continue
        arxiv_id = match.group(1)
        links = {
            node.attrib.get("title") or node.attrib.get("rel") or "": node.attrib.get("href")
            for node in entry.findall("a:link", ATOM)
        }
        title = clean_text(entry.findtext("a:title", namespaces=ATOM))
        authors = [
            clean_text(author.findtext("a:name", namespaces=ATOM))
            for author in entry.findall("a:author", ATOM)
        ]
        categories = [
            node.attrib.get("term", "")
            for node in entry.findall("a:category", ATOM)
            if node.attrib.get("term")
        ]
        doi = normalize_doi(entry.findtext("x:doi", namespaces=ATOM))
        submitted = clean_text(entry.findtext("a:published", namespaces=ATOM))[:10]
        updated = clean_text(entry.findtext("a:updated", namespaces=ATOM))[:10]
        rows.append(
            {
                "preprint_id": f"arxiv:{arxiv_id}",
                "work_id": f"arxiv:{arxiv_id}",
                "arxiv_id": arxiv_id,
                "title": title,
                "authors": [author for author in authors if author],
                "institutions": [],
                "abstract": clean_text(entry.findtext("a:summary", namespaces=ATOM)),
                "categories": categories,
                "primary_category": categories[0] if categories else None,
                "first_submitted": submitted,
                "updated": updated,
                "date_precision": "day",
                "doi": doi,
                "arxiv_url": f"https://arxiv.org/abs/{arxiv_id}",
                "pdf_url": links.get("pdf") or f"https://arxiv.org/pdf/{arxiv_id}",
                "comment": clean_text(entry.findtext("x:comment", namespaces=ATOM)),
                "journal_ref": clean_text(entry.findtext("x:journal_ref", namespaces=ATOM)),
            }
        )
    return total, rows


def collect_query(query_spec: dict, month: str, page_size: int) -> list[dict]:
    start = 0
    collected = []
    total = None
    while total is None or start < total:
        body = fetch(query_spec["id"], query_spec["query"], month, start, page_size)
        total, batch = parse_feed(body)
        collected.extend(batch)
        print(
            f"arXiv {month} {query_spec['id']}: {len(collected)}/{total}",
            flush=True,
        )
        if not batch:
            break
        start += len(batch)
    return collected


def merge_record(existing: dict, incoming: dict, query_id: str) -> dict:
    if not existing:
        incoming["discovery_queries"] = [query_id]
        return incoming
    if query_id not in existing["discovery_queries"]:
        existing["discovery_queries"].append(query_id)
    existing["categories"] = list(dict.fromkeys([*existing["categories"], *incoming["categories"]]))
    return existing


def classify(records: list[dict]) -> None:
    for record in records:
        is_cs_ro = "cs.RO" in record["categories"] or "cs_ro" in record["discovery_queries"]
        result = classify_research(
            title=record["title"],
            abstract=record["abstract"],
            extra_text=f"{record['comment']} {record['journal_ref']}",
            source_is_robotics=is_cs_ro,
        )
        record["primary_topic"] = result.pop("primary_topic")
        record["topics"] = result.pop("topics")
        record["tags"] = result.pop("tags")
        record["topic_scores"] = result.pop("topic_scores")
        record["relevance"] = result
        record["included"] = result["status"] == "included"
        if record["first_submitted"] < "2025-07-01":
            record["period"] = "baseline"
        elif record["first_submitted"] <= "2026-06-30":
            record["period"] = "analysis"
        else:
            record["period"] = "provisional"


def summarize(records: list[dict]) -> dict:
    months = {}
    for month in month_keys():
        subset = [row for row in records if row["first_submitted"][:7] == month]
        months[month] = {
            "mother_corpus": len(subset),
            "included": sum(row["included"] for row in subset),
            "candidate": sum(row["relevance"]["status"] == "candidate" for row in subset),
            "manual_review": sum(
                row["relevance"]["status"] == "manual_review" for row in subset
            ),
            "cs_ro": sum("cs.RO" in row["categories"] for row in subset),
            "supplement_only": sum("cs.RO" not in row["categories"] for row in subset),
        }
    return {
        "generated_at": date.today().isoformat(),
        "window": REGISTRY["window"],
        "mother_corpus": len(records),
        "included": sum(row["included"] for row in records),
        "candidate": sum(row["relevance"]["status"] == "candidate" for row in records),
        "manual_review": sum(
            row["relevance"]["status"] == "manual_review" for row in records
        ),
        "with_doi": sum(bool(row.get("doi")) for row in records),
        "by_query": dict(
            Counter(query for row in records for query in row["discovery_queries"])
        ),
        "by_primary_topic": dict(
            Counter(
                row["primary_topic"]
                for row in records
                if row["included"] and row["primary_topic"]
            )
        ),
        "months": months,
        "method_note": (
            "Mother corpus is the deduplicated union of complete cs.RO monthly pulls "
            "and targeted cs.AI/cs.CV/cs.LG supplementary queries. Included is an "
            "automated v2 relevance state, not the hand-curated top-paper set."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--page-size", type=int, default=500)
    parser.add_argument("--month", help="collect only YYYY-MM for a smoke test")
    args = parser.parse_args()
    months = [args.month] if args.month else month_keys()
    if any(month not in month_keys() for month in months):
        raise SystemExit("month must be inside the configured collection window")

    merged: dict[str, dict] = {}
    for month in months:
        for query_spec in REGISTRY["arxiv_sources"]["queries"]:
            for record in collect_query(query_spec, month, args.page_size):
                merged[record["arxiv_id"]] = merge_record(
                    merged.get(record["arxiv_id"], {}),
                    record,
                    query_spec["id"],
                )
    records = sorted(merged.values(), key=lambda row: (row["first_submitted"], row["arxiv_id"]))
    classify(records)
    if args.month and OUTPUT.exists():
        # A smoke-test month must never overwrite the complete corpus.
        target = ROOT / "data" / f"preprints-{args.month}.json"
        coverage_target = ROOT / "data" / f"preprint-coverage-{args.month}.json"
    else:
        target = OUTPUT
        coverage_target = COVERAGE
    target.write_text(
        json.dumps(records, ensure_ascii=False, separators=(",", ":")) + "\n"
    )
    coverage = summarize(records)
    coverage_target.write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n")
    print(
        f"Saved {len(records)} arXiv records; {coverage['included']} included, "
        f"{coverage['candidate']} candidates, {coverage['manual_review']} manual-review.",
        flush=True,
    )


if __name__ == "__main__":
    main()
