#!/usr/bin/env python3
"""Build the official-publication mother corpus, then classify embodied-AI relevance.

Discovery and verification are intentionally separated:
- DBLP supplies complete conference metadata and DOI discovery.
- Crossref exact-ISSN streams supply complete journal metadata.
- DOI resolver or official proceedings pages provide the official evidence URL.
- Semantic Scholar enriches abstracts/arXiv IDs for screening, but never proves
  peer-review status.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from radar_common import (
    ROOT,
    canonical_work_id,
    classify_research,
    clean_text,
    date_from_parts,
    extract_arxiv_id,
    normalize_doi,
    normalize_title,
)

REGISTRY = json.loads((ROOT / "config" / "source-registry.json").read_text())
RAW = ROOT / "data" / "raw" / "publications"
OUTPUT = ROOT / "data" / "publications.json"
SUMMARY = ROOT / "data" / "publication-coverage.json"
RAW.mkdir(parents=True, exist_ok=True)
USER_AGENT = "embodied-ai-radar/2.0 (mailto:research-radar@example.com)"
S2_FIELDS = ",".join(
    [
        "title",
        "abstract",
        "authors",
        "publicationDate",
        "externalIds",
        "venue",
        "url",
        "openAccessPdf",
        "citationCount",
        "influentialCitationCount",
        "publicationTypes",
    ]
)


def request_json(
    url: str,
    *,
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    attempts: int = 6,
) -> Any:
    request_headers = {"User-Agent": USER_AGENT, **(headers or {})}
    request = urllib.request.Request(url, data=data, headers=request_headers)
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if attempt == attempts - 1:
                raise
            if exc.code == 429:
                delay = min(int(exc.headers.get("Retry-After", "30")), 90)
            elif exc.code >= 500:
                delay = min(3 * (attempt + 1), 30)
            else:
                raise
            print(f"HTTP {exc.code}; retrying in {delay}s", file=sys.stderr, flush=True)
            time.sleep(delay)
        except Exception as exc:
            if attempt == attempts - 1:
                raise
            delay = min(3 * (attempt + 1), 30)
            print(f"{type(exc).__name__}; retrying in {delay}s", file=sys.stderr, flush=True)
            time.sleep(delay)
    raise RuntimeError("unreachable")


def author_names(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, dict) and "author" in value:
        value = value["author"]
    if not isinstance(value, list):
        value = [value]
    result = []
    for item in value:
        if isinstance(item, str):
            name = item
        elif isinstance(item, dict):
            name = item.get("text") or item.get("name")
            if not name:
                given = item.get("given") or ""
                family = item.get("family") or ""
                name = f"{given} {family}".strip()
        else:
            name = ""
        name = clean_text(name)
        if name and name not in result:
            result.append(name)
    return result


def publication_id(doi: str | None, title: str, venue: str, year: int) -> str:
    if doi:
        return f"doi:{doi}"
    digest = hashlib.sha1(f"{normalize_title(title)}|{venue}|{year}".encode()).hexdigest()[:20]
    return f"publication:{digest}"


def publisher_url(doi: str | None, fallback: str) -> str:
    """Construct a publisher-domain landing page from a registered DOI."""
    doi = normalize_doi(doi)
    if not doi:
        return fallback
    ieee_match = re.search(r"\.(\d{7,9})$", doi)
    if doi.startswith("10.1109/") and ieee_match:
        return f"https://ieeexplore.ieee.org/document/{ieee_match.group(1)}"
    if doi.startswith("10.1126/scirobotics."):
        return f"https://www.science.org/doi/{doi}"
    if doi.startswith("10.1177/"):
        return f"https://journals.sagepub.com/doi/{doi}"
    return f"https://doi.org/{doi}"


def collect_dblp(source: dict) -> list[dict]:
    records = []
    for year in source["years"]:
        cache = RAW / f"dblp-{source['venue'].lower()}-{year}.json"
        if cache.exists() and cache.stat().st_size > 0:
            cached = json.loads(cache.read_text())
            hits = cached.get("hits", [])
            expected_total = cached.get("expected_total")
            needs_fetch = (
                expected_total is not None
                and not cached.get("complete", len(hits) >= int(expected_total))
            )
        else:
            hits = []
            expected_total = None
            needs_fetch = True
        if needs_fetch:
            offset = len(hits)
            total = int(expected_total) if expected_total is not None else None
            while total is None or offset < total:
                params = urllib.parse.urlencode(
                    {
                        "q": f"stream:{source['dblp_stream']}: year:{year}:",
                        "h": 1000,
                        "f": offset,
                        "format": "json",
                    }
                )
                payload = request_json(f"https://dblp.org/search/publ/api?{params}")
                result = payload.get("result", {})
                batch = (result.get("hits") or {}).get("hit") or []
                if isinstance(batch, dict):
                    batch = [batch]
                total = int((result.get("hits") or {}).get("@total") or 0)
                hits.extend(batch)
                offset += len(batch)
                cache.write_text(
                    json.dumps(
                        {
                            "hits": hits,
                            "expected_total": total,
                            "complete": len(hits) >= total,
                        },
                        ensure_ascii=False,
                    )
                )
                print(
                    f"DBLP {source['venue']} {year}: {len(hits)}/{total}",
                    flush=True,
                )
                if not batch:
                    break
                time.sleep(1.1)
        for hit in hits:
            info = hit.get("info") or {}
            title = clean_text(info.get("title")).rstrip(".")
            if not title:
                continue
            doi = normalize_doi(info.get("doi"))
            record_year = int(info.get("year") or year)
            event_date = (source.get("event_dates") or {}).get(str(record_year))
            url = clean_text(info.get("url")) or None
            official_url = publisher_url(doi, source["official_index"])
            records.append(
                {
                    "publication_id": publication_id(doi, title, source["venue"], record_year),
                    "work_id": canonical_work_id(
                        doi=doi,
                        title=title,
                        first_author=(author_names(info.get("authors")) or [None])[0],
                        year=record_year,
                    ),
                    "title": title,
                    "authors": author_names(info.get("authors")),
                    "institutions": [],
                    "abstract": "",
                    "venue": source["venue"],
                    "venue_full_name": source["full_name"],
                    "year": record_year,
                    "publication_type": "conference",
                    "publication_date": event_date or f"{record_year:04d}-01-01",
                    "date_precision": "day" if event_date else "year",
                    "doi": doi,
                    "arxiv_id": None,
                    "official_url": official_url,
                    "official_index": source["official_index"],
                    "discovery_url": url,
                    "discovery_source": "DBLP stream",
                    "verification_status": (
                        "publisher_url_from_registered_doi"
                        if doi
                        else "discovered_needs_official_check"
                    ),
                    "source_tier": source["tier"],
                }
            )
    return records


def choose_crossref_date(item: dict) -> tuple[str | None, str]:
    for key in ["published-online", "published-print", "published", "issued", "created"]:
        if item.get(key):
            if key == "created" and item[key].get("date-time"):
                return item[key]["date-time"][:10], "day"
            return date_from_parts(item[key])
    return None, "unknown"


def collect_crossref(source: dict) -> list[dict]:
    cutoff = REGISTRY["window"]["until"]
    cache = RAW / (
        f"crossref-{source['venue'].lower().replace(' ', '-')}-through-{cutoff}.json"
    )
    if cache.exists() and cache.stat().st_size > 100:
        cached = json.loads(cache.read_text())
        items = cached.get("items", [])
        expected_total = int(cached.get("expected_total") or 0)
    else:
        items = []
        expected_total = 0
    if not expected_total or len(items) < expected_total:
        items = []
        offset = 0
        while True:
            params = urllib.parse.urlencode(
                {
                    "filter": (
                        f"from-pub-date:{REGISTRY['window']['from']},"
                        f"until-pub-date:{REGISTRY['window']['until']}"
                    ),
                    "rows": 1000,
                    "offset": offset,
                    "select": (
                        "DOI,title,author,published-online,published-print,published,"
                        "issued,created,URL,container-title,ISSN,subject,type,publisher"
                    ),
                }
            )
            url = f"https://api.crossref.org/journals/{source['issn']}/works?{params}"
            payload = request_json(url)
            message = payload.get("message") or {}
            batch = message.get("items") or []
            items.extend(batch)
            expected_total = int(message.get("total-results") or len(items))
            print(
                f"Crossref {source['venue']}: {len(items)}/{expected_total}",
                flush=True,
            )
            if not batch or len(items) >= expected_total:
                break
            offset += len(batch)
            time.sleep(1.1)
        cache.write_text(
            json.dumps(
                {"items": items, "expected_total": expected_total},
                ensure_ascii=False,
            )
        )

    records = []
    for item in items:
        title = clean_text(item.get("title"))
        if not title:
            continue
        doi = normalize_doi(item.get("DOI"))
        publication_date, precision = choose_crossref_date(item)
        record_year = int((publication_date or REGISTRY["window"]["from"])[:4])
        authors = author_names(item.get("author"))
        official_url = publisher_url(doi, source["official_index"])
        records.append(
            {
                "publication_id": publication_id(doi, title, source["venue"], record_year),
                "work_id": canonical_work_id(
                    doi=doi,
                    title=title,
                    first_author=(authors or [None])[0],
                    year=record_year,
                ),
                "title": title,
                "authors": authors,
                "institutions": [],
                "abstract": clean_text(item.get("abstract")),
                "venue": source["venue"],
                "venue_full_name": source["full_name"],
                "year": record_year,
                "publication_type": "journal",
                "publication_date": publication_date,
                "date_precision": precision,
                "doi": doi,
                "arxiv_id": None,
                "official_url": official_url,
                "official_index": source["official_index"],
                "discovery_url": clean_text(item.get("URL")) or None,
                "discovery_source": "Crossref exact ISSN stream",
                "verification_status": (
                    "publisher_url_from_registered_doi"
                    if doi
                    else "discovered_needs_official_check"
                ),
                "source_tier": source["tier"],
                "publisher": clean_text(item.get("publisher")) or None,
            }
        )
    return records


def apply_semantic_scholar_work(work: dict, by_doi: dict[str, dict]) -> None:
    if not work:
        return
    external = work.get("externalIds") or {}
    doi = normalize_doi(external.get("DOI"))
    if not doi or doi not in by_doi:
        return
    record = by_doi[doi]
    record["semantic_scholar_id"] = work.get("paperId")
    record["abstract"] = clean_text(work.get("abstract")) or record.get("abstract", "")
    s2_authors = author_names(work.get("authors"))
    if s2_authors:
        record["authors"] = s2_authors
    arxiv_id = extract_arxiv_id(external.get("ArXiv"))
    if arxiv_id:
        record["arxiv_id"] = arxiv_id
        record["work_id"] = f"arxiv:{arxiv_id}"
    if work.get("publicationDate"):
        # Semantic Scholar may expose a preprint/first-public date for a DOI-linked
        # work. Keep it as enrichment evidence, but never let it overwrite the
        # conference year or the publisher/Crossref publication date.
        record["semantic_scholar_publication_date"] = work["publicationDate"][:10]
    record["citation_count_snapshot"] = work.get("citationCount")
    record["influential_citation_count_snapshot"] = work.get("influentialCitationCount")
    record["citation_snapshot_date"] = REGISTRY["window"]["until"]


def fetch_semantic_scholar_batch(batch_dois: list[str]) -> list:
    """Fetch a batch, isolating malformed identifiers on HTTP 400."""
    body = json.dumps({"ids": [f"DOI:{doi}" for doi in batch_dois]}).encode()
    try:
        return request_json(
            f"https://api.semanticscholar.org/graph/v1/paper/batch?fields={S2_FIELDS}",
            data=body,
            headers={"Content-Type": "application/json"},
        )
    except urllib.error.HTTPError as exc:
        if exc.code != 400:
            raise
        if len(batch_dois) == 1:
            print(
                f"Semantic Scholar rejected DOI; keeping metadata-only: {batch_dois[0]}",
                file=sys.stderr,
                flush=True,
            )
            return [None]
        middle = len(batch_dois) // 2
        return [
            *fetch_semantic_scholar_batch(batch_dois[:middle]),
            *fetch_semantic_scholar_batch(batch_dois[middle:]),
        ]


def enrich_semantic_scholar(
    records: list[dict],
    *,
    force: bool = False,
    cached_only: bool = False,
) -> None:
    by_doi = {record["doi"]: record for record in records if record.get("doi")}
    cached_works: dict[str, dict] = {}
    if not force:
        for cache in RAW.glob("semantic-scholar-*.json"):
            try:
                for work in json.loads(cache.read_text()):
                    if not work:
                        continue
                    doi = normalize_doi((work.get("externalIds") or {}).get("DOI"))
                    if doi:
                        cached_works[doi] = work
            except (json.JSONDecodeError, OSError):
                continue
    for work in cached_works.values():
        apply_semantic_scholar_work(work, by_doi)
    # DBLP occasionally exposes placeholder RSS DOI strings such as
    # `10.15607/rss.2024.xx.068`.  They are not resolvable identifiers and
    # recursively splitting them against Semantic Scholar causes avoidable
    # 400/429 storms during a month-end refresh.
    identifiers = sorted(
        doi for doi in by_doi
        if ".xx." not in doi.lower() and (force or doi not in cached_works)
    )
    print(
        f"Semantic Scholar cache: {len(by_doi) - len(identifiers)}/{len(by_doi)} DOI records",
        flush=True,
    )
    if cached_only:
        return
    for index in range(0, len(identifiers), 400):
        batch_dois = identifiers[index : index + 400]
        cache_key = hashlib.sha1("\n".join(batch_dois).encode()).hexdigest()[:16]
        cache = RAW / f"semantic-scholar-{cache_key}.json"
        if cache.exists() and cache.stat().st_size > 10 and not force:
            payload = json.loads(cache.read_text())
        else:
            payload = fetch_semantic_scholar_batch(batch_dois)
            cache.write_text(json.dumps(payload, ensure_ascii=False))
            time.sleep(1.1)
        for work in payload:
            apply_semantic_scholar_work(work, by_doi)
        print(
            f"Semantic Scholar new publications: "
            f"{min(index + 400, len(identifiers))}/{len(identifiers)}",
            flush=True,
        )


def apply_classification(records: list[dict]) -> None:
    robotics_venues = {
        source["venue"]
        for source in [
            *REGISTRY["conference_sources"],
            *REGISTRY["journal_sources"],
        ]
        if source["tier"] in {"core", "extended"}
    }
    for record in records:
        result = classify_research(
            title=record["title"],
            abstract=record.get("abstract") or "",
            extra_text=record.get("venue_full_name") or "",
            source_is_robotics=record["venue"] in robotics_venues,
        )
        record["primary_topic"] = result.pop("primary_topic")
        record["topics"] = result.pop("topics")
        record["tags"] = result.pop("tags")
        record["topic_scores"] = result.pop("topic_scores")
        record["relevance"] = result
        record["included"] = result["status"] == "included"
        date_value = record.get("publication_date")
        if date_value and record.get("date_precision") in {"day", "month"}:
            record["in_peer_review_window"] = (
                REGISTRY["window"]["from"] <= date_value <= REGISTRY["window"]["until"]
            )
        else:
            record["in_peer_review_window"] = (
                int(REGISTRY["window"]["from"][:4])
                <= int(record["year"])
                <= int(REGISTRY["window"]["until"][:4])
            )


def deduplicate(records: list[dict]) -> list[dict]:
    merged: dict[str, dict] = {}
    title_keys: dict[str, str] = {}
    for record in records:
        key = record["publication_id"]
        title_key = f"{normalize_title(record['title'])}|{record['venue']}|{record['year']}"
        if key not in merged and title_key in title_keys:
            key = title_keys[title_key]
        if key not in merged:
            merged[key] = record
            title_keys[title_key] = key
            continue
        existing = merged[key]
        for field in ["abstract", "doi", "arxiv_id", "official_url", "discovery_url"]:
            if not existing.get(field) and record.get(field):
                existing[field] = record[field]
        existing["authors"] = list(dict.fromkeys([*existing["authors"], *record["authors"]]))
    return sorted(merged.values(), key=lambda row: (row["venue"], row["year"], row["title"]))


def summarize(records: list[dict], scope: str) -> dict:
    by_venue = {}
    for venue in sorted({row["venue"] for row in records}):
        subset = [row for row in records if row["venue"] == venue]
        by_venue[venue] = {
            "mother_corpus": len(subset),
            "in_window": sum(row["in_peer_review_window"] for row in subset),
            "included": sum(row["included"] for row in subset),
            "included_in_window": sum(
                row["included"] and row["in_peer_review_window"] for row in subset
            ),
            "candidate": sum(row["relevance"]["status"] == "candidate" for row in subset),
            "candidate_in_window": sum(
                row["relevance"]["status"] == "candidate"
                and row["in_peer_review_window"]
                for row in subset
            ),
            "manual_review": sum(
                row["relevance"]["status"] == "manual_review" for row in subset
            ),
            "manual_review_in_window": sum(
                row["relevance"]["status"] == "manual_review"
                and row["in_peer_review_window"]
                for row in subset
            ),
            "with_doi": sum(bool(row.get("doi")) for row in subset),
            "with_arxiv": sum(bool(row.get("arxiv_id")) for row in subset),
            "with_abstract": sum(bool(row.get("abstract")) for row in subset),
            "officially_verified": sum(
                row["verification_status"]
                in {
                    "peer_reviewed_official_proceedings",
                    "official_publisher_page_verified",
                }
                for row in subset
            ),
        }
    return {
        "generated_at": REGISTRY["window"]["until"],
        "window": REGISTRY["window"],
        "scope": scope,
        "mother_corpus": len(records),
        "in_window_records": sum(row["in_peer_review_window"] for row in records),
        "included": sum(row["included"] for row in records),
        "included_in_window": sum(
            row["included"] and row["in_peer_review_window"] for row in records
        ),
        "candidate": sum(row["relevance"]["status"] == "candidate" for row in records),
        "candidate_in_window": sum(
            row["relevance"]["status"] == "candidate"
            and row["in_peer_review_window"]
            for row in records
        ),
        "manual_review": sum(
            row["relevance"]["status"] == "manual_review" for row in records
        ),
        "manual_review_in_window": sum(
            row["relevance"]["status"] == "manual_review"
            and row["in_peer_review_window"]
            for row in records
        ),
        "with_doi": sum(bool(row.get("doi")) for row in records),
        "with_arxiv": sum(bool(row.get("arxiv_id")) for row in records),
        "with_abstract": sum(bool(row.get("abstract")) for row in records),
        "by_venue": by_venue,
        "by_topic": dict(
            Counter(
                row["primary_topic"]
                for row in records
                if row["included"] and row["primary_topic"]
            )
        ),
        "method_note": (
            "Mother-corpus counts are complete metadata pulls for selected sources. "
            "Included counts are automated v2 relevance candidates, not hand-curated top papers."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scope",
        choices=["core", "extended", "all"],
        default="core",
        help="core; core+extended; or all sources including cross-field venues",
    )
    parser.add_argument("--no-enrich", action="store_true")
    parser.add_argument(
        "--cached-enrich-only",
        action="store_true",
        help="apply existing Semantic Scholar caches without making network requests",
    )
    parser.add_argument("--force-enrich", action="store_true")
    parser.add_argument(
        "--reuse-output",
        action="store_true",
        help="reclassify and rebuild coverage from the existing enriched output",
    )
    args = parser.parse_args()
    if args.reuse_output:
        if not OUTPUT.exists():
            raise SystemExit("cannot reuse output before data/publications.json exists")
        records = json.loads(OUTPUT.read_text())
        apply_classification(records)
        coverage = summarize(records, "existing-output")
        OUTPUT.write_text(
            json.dumps(records, ensure_ascii=False, separators=(",", ":")) + "\n"
        )
        SUMMARY.write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n")
        print(
            f"Reclassified {len(records)} existing publications; "
            f"{coverage['included']} included and "
            f"{coverage['in_window_records']} inside the peer-review window.",
            flush=True,
        )
        return
    allowed_tiers = {
        "core": {"core"},
        "extended": {"core", "extended"},
        "all": {"core", "extended", "cross_field"},
    }[args.scope]

    records = []
    for source in REGISTRY["conference_sources"]:
        if source["tier"] in allowed_tiers:
            print(f"Collecting {source['venue']} conference stream", flush=True)
            records.extend(collect_dblp(source))
    for source in REGISTRY["journal_sources"]:
        if source["tier"] in allowed_tiers:
            print(f"Collecting {source['venue']} journal stream", flush=True)
            records.extend(collect_crossref(source))
    records = deduplicate(records)
    print(f"Publication mother corpus: {len(records)}", flush=True)
    if not args.no_enrich:
        enrich_semantic_scholar(
            records,
            force=args.force_enrich,
            cached_only=args.cached_enrich_only,
        )
    apply_classification(records)
    records = deduplicate(records)
    coverage = summarize(records, args.scope)
    OUTPUT.write_text(
        json.dumps(records, ensure_ascii=False, separators=(",", ":")) + "\n"
    )
    SUMMARY.write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n")
    print(
        f"Saved {len(records)} publications; {coverage['included']} included, "
        f"{coverage['candidate']} candidates, {coverage['manual_review']} manual-review.",
        flush=True,
    )


if __name__ == "__main__":
    main()
