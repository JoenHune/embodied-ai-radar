#!/usr/bin/env python3
"""Fallback high-recall discovery through Semantic Scholar Academic Graph.

Only records with an official ArXiv external ID are retained. The v1 date is
revalidated for selected papers against arXiv; this corpus supplies the light
baseline and discovery pool when arXiv's Atom endpoint is rate limited.
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from collect_arxiv import PROCESSED, classify, period

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "semantic-scholar"
RAW.mkdir(parents=True, exist_ok=True)

QUERIES = {
    "foundation": '("vision language action" | "robot foundation model" | "generalist robot" | "language conditioned robot")',
    "dual_system": '(("high level planner" + "low level policy" + robot) | ("hierarchical reasoning" + robot) | ("fast slow" + robot))',
    "dexterous": '("dexterous manipulation" | "bimanual manipulation" | "tactile manipulation") + robot',
    "world_model": '(("world model" + robot) | ("action conditioned video" + robot) | ("latent action" + robot))',
    "general_learning": '(("diffusion policy" + robot) | ("flow policy" + robot) | ("cross embodiment" + robot) | ("imitation learning" + manipulation))',
}


def fetch(topic: str, query: str, year: int) -> dict:
    cache = RAW / f"{year}-{topic}.json"
    if cache.exists() and cache.stat().st_size > 100:
        return json.loads(cache.read_text())
    params = urllib.parse.urlencode(
        {
            "query": query,
            "year": str(year),
            "fields": "title,abstract,authors,publicationDate,externalIds,venue,url,openAccessPdf,publicationTypes",
        }
    )
    url = f"https://api.semanticscholar.org/graph/v1/paper/search/bulk?{params}"
    request = urllib.request.Request(url, headers={"User-Agent": "embodied-ai-radar/1.0"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                payload = json.loads(response.read().decode("utf-8"))
            cache.write_text(json.dumps(payload, ensure_ascii=False))
            time.sleep(1.1)
            return payload
        except urllib.error.HTTPError as exc:
            if attempt == 4:
                raise
            delay = min(int(exc.headers.get("Retry-After", "15")), 60) if exc.code == 429 else 2 ** attempt
            print(f"Semantic Scholar {exc.code}; retrying in {delay}s", flush=True)
            time.sleep(delay)
        except Exception:
            if attempt == 4:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def normalize(work: dict) -> dict | None:
    external = work.get("externalIds") or {}
    arxiv_id = external.get("ArXiv")
    if not arxiv_id or not re.fullmatch(r"\d{4}\.\d{4,5}", arxiv_id):
        return None
    submitted = work.get("publicationDate")
    if not submitted:
        # arXiv IDs encode year and month but not day; records without an exact
        # publication date are excluded from monthly statistics.
        return None
    authors = [author.get("name") for author in work.get("authors") or [] if author.get("name")]
    encoded_month = f"20{arxiv_id[:2]}-{arxiv_id[2:4]}"
    date_precision = "day"
    if submitted[:7] != encoded_month:
        # Semantic Scholar occasionally assigns a conference or early-online
        # date to an arXiv record. The arXiv identifier is authoritative for
        # the v1 month; curated records later restore the exact day.
        submitted = f"{encoded_month}-01"
        date_precision = "month"
    return {
        "id": arxiv_id,
        "title": work.get("title") or "",
        "authors": authors,
        "institutions": [],
        "first_submitted": submitted,
        "updated": submitted,
        "abstract": work.get("abstract") or "",
        "categories": [],
        "comment": "",
        "journal_ref": work.get("venue") or "",
        "doi": external.get("DOI"),
        "arxiv_url": f"https://arxiv.org/abs/{arxiv_id}",
        "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}",
        "semantic_scholar_id": work.get("paperId"),
        "date_precision": date_precision,
        "v1_month": encoded_month,
    }


def main() -> None:
    merged: dict[str, dict] = {}
    for year in [2024, 2025, 2026]:
        for topic, query in QUERIES.items():
            print(f"{year} {topic}", flush=True)
            payload = fetch(topic, query, year)
            for work in payload.get("data", []):
                row = normalize(work)
                if not row or not ("2024-07-01" <= row["first_submitted"] <= "2026-07-29"):
                    continue
                if row["id"] not in merged:
                    merged[row["id"]] = row
                    merged[row["id"]]["query_topics"] = []
                if topic not in merged[row["id"]]["query_topics"]:
                    merged[row["id"]]["query_topics"].append(topic)
    candidates = []
    for row in merged.values():
        result = classify(row)
        if not result:
            continue
        result["query_topics"] = row["query_topics"]
        result["period"] = period(result)
        result["source"] = "Semantic Scholar discovery + arXiv external ID"
        candidates.append(result)
    candidates.sort(key=lambda item: (item["first_submitted"], item["id"]))
    (PROCESSED / "semantic-scholar-candidates.json").write_text(
        json.dumps(candidates, ensure_ascii=False, indent=2)
    )
    print(f"Saved {len(candidates)} candidates from {len(merged)} unique arXiv records.")


if __name__ == "__main__":
    main()
