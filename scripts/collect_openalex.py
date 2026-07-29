#!/usr/bin/env python3
"""Collect a reproducible high-recall arXiv corpus through OpenAlex.

This is the rate-limit fallback for the arXiv Atom API. OpenAlex provides the
official arXiv landing URL, abstract, authors and normalized institutions. The
curated set is later revalidated against each arXiv abstract page.
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from collect_arxiv import MONTHS, PROCESSED, classify, period

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "openalex"
RAW.mkdir(parents=True, exist_ok=True)

SOURCE_ID = "S4306400194"
QUERIES = {
    "foundation": '"vision language action" OR "robot foundation model" OR "generalist robot" OR "language conditioned robot"',
    "dual_system": '"high-level planner" "low-level policy" robot OR "hierarchical reasoning" robot OR "fast slow" robot',
    "dexterous": '"dexterous manipulation" robot OR "tactile manipulation" robot OR "bimanual manipulation" robot',
    "world_model": '"world model" robot OR "action-conditioned video" robot OR "latent action" robot',
    "general_learning": '"diffusion policy" robot OR "flow policy" robot OR "cross embodiment" robot OR "imitation learning" manipulation',
}


def month_end(month_key: str) -> str:
    year, month = map(int, month_key.split("-"))
    if month_key == "2026-07":
        return "2026-07-29"
    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1
    import datetime

    return (datetime.date(next_year, next_month, 1) - datetime.timedelta(days=1)).isoformat()


def reconstruct_abstract(index: dict | None) -> str:
    if not index:
        return ""
    positions = [(position, word) for word, values in index.items() for position in values]
    return " ".join(word for _, word in sorted(positions))


def fetch(month_key: str, topic: str, query: str) -> dict:
    cache = RAW / f"{month_key}-{topic}.json"
    if cache.exists() and cache.stat().st_size > 100:
        return json.loads(cache.read_text())
    filters = ",".join(
        [
            f"primary_location.source.id:{SOURCE_ID}",
            f"from_publication_date:{month_key}-01",
            f"to_publication_date:{month_end(month_key)}",
        ]
    )
    params = urllib.parse.urlencode(
        {
            "filter": filters,
            "search": query,
            "per-page": 200,
            "select": "id,title,publication_date,authorships,abstract_inverted_index,primary_location,locations,doi,type",
            "mailto": "research-radar@example.com",
        }
    )
    url = f"https://api.openalex.org/works?{params}"
    request = urllib.request.Request(url, headers={"User-Agent": "embodied-ai-radar/1.0"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                payload = json.loads(response.read().decode("utf-8"))
            cache.write_text(json.dumps(payload, ensure_ascii=False))
            time.sleep(1.05)
            return payload
        except urllib.error.HTTPError as exc:
            if attempt == 3:
                raise
            retry_after = int(exc.headers.get("Retry-After", "20")) if exc.code == 429 else 2 ** attempt
            print(f"OpenAlex {exc.code}; retrying in {retry_after}s", flush=True)
            time.sleep(retry_after)
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def normalize(work: dict) -> dict | None:
    locations = [work.get("primary_location") or {}, *(work.get("locations") or [])]
    landing_urls = [location.get("landing_page_url") or "" for location in locations]
    match = next(
        (
            re.search(r"arxiv\.org/abs/(\d{4}\.\d{4,5})", url, flags=re.I)
            for url in landing_urls
            if "arxiv.org/abs/" in url.lower()
        ),
        None,
    )
    if not match:
        return None
    arxiv_id = match.group(1)
    authors = []
    institutions = []
    for authorship in work.get("authorships") or []:
        author = (authorship.get("author") or {}).get("display_name")
        if author and author not in authors:
            authors.append(author)
        for institution in authorship.get("institutions") or []:
            name = institution.get("display_name")
            if name and name not in institutions:
                institutions.append(name)
    row = {
        "id": arxiv_id,
        "title": work.get("title") or "",
        "authors": authors,
        "institutions": institutions,
        "first_submitted": work.get("publication_date"),
        "updated": work.get("publication_date"),
        "abstract": reconstruct_abstract(work.get("abstract_inverted_index")),
        "categories": [],
        "comment": "",
        "journal_ref": "",
        "doi": work.get("doi"),
        "arxiv_url": f"https://arxiv.org/abs/{arxiv_id}",
        "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}",
        "openalex_id": work.get("id"),
    }
    return row


def main() -> None:
    merged: dict[str, dict] = {}
    for month_index, month_key in enumerate(MONTHS, 1):
        print(f"[{month_index}/{len(MONTHS)}] {month_key}", flush=True)
        for topic, query in QUERIES.items():
            payload = fetch(month_key, topic, query)
            for work in payload.get("results", []):
                row = normalize(work)
                if not row:
                    continue
                if row["id"] not in merged:
                    merged[row["id"]] = row
                    merged[row["id"]]["query_topics"] = []
                if topic not in merged[row["id"]]["query_topics"]:
                    merged[row["id"]]["query_topics"].append(topic)
                for institution in row["institutions"]:
                    if institution not in merged[row["id"]]["institutions"]:
                        merged[row["id"]]["institutions"].append(institution)

    candidates = []
    for row in merged.values():
        result = classify(row)
        if not result:
            continue
        result["query_topics"] = row["query_topics"]
        # Search-query membership is useful supporting evidence, but never
        # overrides the transparent title/abstract primary classification.
        result["period"] = period(result)
        result["source"] = "OpenAlex + official arXiv landing URL"
        candidates.append(result)
    candidates.sort(key=lambda item: (item["first_submitted"], item["id"]))
    (PROCESSED / "openalex-candidates.json").write_text(
        json.dumps(candidates, ensure_ascii=False, indent=2)
    )
    print(f"Saved {len(candidates)} unique high-recall candidates.")


if __name__ == "__main__":
    main()
