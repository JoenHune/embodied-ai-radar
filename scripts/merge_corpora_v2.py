#!/usr/bin/env python3
"""Merge preprints, publication versions, official evidence, and GitHub assets.

The result is a canonical work graph. A work can exist without an arXiv ID, and
publication dates never overwrite the arXiv v1 date used for monthly trends.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from radar_common import (
    ROOT,
    TAXONOMY,
    canonical_work_id,
    normalize_doi,
    normalize_title,
)

PREPRINTS = ROOT / "data" / "preprints.json"
PUBLICATIONS = ROOT / "data" / "publications.json"
OFFICIAL = ROOT / "data" / "official-proceedings.json"
OFFICIAL_PROGRAMS = ROOT / "data" / "official-programs.json"
REPOSITORIES = ROOT / "data" / "repositories.json"
LEGACY_PAPERS = ROOT / "data" / "papers.json"
LEGACY_PEERS = ROOT / "data" / "peer-review.json"
OUTPUT = ROOT / "data" / "works.json"
COVERAGE = ROOT / "data" / "work-coverage.json"
SNAPSHOT_DATE = "2026-07-29"


def read(path: Path, fallback):
    return json.loads(path.read_text()) if path.exists() else fallback


def empty_work(work_id: str, title: str) -> dict:
    return {
        "work_id": work_id,
        "title": title,
        "authors": [],
        "institutions": [],
        "abstract": "",
        "first_public_date": None,
        "first_public_date_precision": "unknown",
        "first_public_date_source": "unknown",
        "arxiv_id": None,
        "doi": None,
        "primary_topic": None,
        "topics": [],
        "tags": [],
        "relevance": {
            "status": "manual_review",
            "score": 0,
            "classifier_version": TAXONOMY["version"],
            "reasons": [],
        },
        "versions": [],
        "repositories": [],
        "strict_peer_reviewed": False,
        "strict_peer_review_evidence": [],
        "curated": False,
    }


def merge_unique(left: list, right: list) -> list:
    return list(dict.fromkeys([*(left or []), *(right or [])]))


def version_key(version: dict) -> str:
    return "|".join(
        [
            version.get("kind") or "",
            version.get("url") or "",
            version.get("venue") or "",
            str(version.get("year") or ""),
        ]
    )


def add_version(work: dict, version: dict) -> None:
    keys = {version_key(item) for item in work["versions"]}
    if version_key(version) not in keys:
        work["versions"].append(version)


def stronger_relevance(current: dict, incoming: dict) -> dict:
    rank = {"excluded": 0, "manual_review": 1, "candidate": 2, "included": 3}
    if rank.get(incoming.get("status"), 0) > rank.get(current.get("status"), 0):
        return incoming
    if (
        incoming.get("status") == current.get("status")
        and incoming.get("score", 0) > current.get("score", 0)
    ):
        return incoming
    return current


def main() -> None:
    preprints = read(PREPRINTS, [])
    publications = read(PUBLICATIONS, [])
    official_records = read(OFFICIAL, [])
    official_programs = read(OFFICIAL_PROGRAMS, [])
    repositories = read(REPOSITORIES, [])
    legacy_papers = read(LEGACY_PAPERS, [])
    legacy_peers = read(LEGACY_PEERS, {"records": []}).get("records", [])

    works: dict[str, dict] = {}
    by_arxiv: dict[str, str] = {}
    by_doi: dict[str, str] = {}
    by_title: dict[str, str] = {}

    def register(work: dict) -> None:
        works[work["work_id"]] = work
        if work.get("arxiv_id"):
            by_arxiv[work["arxiv_id"]] = work["work_id"]
        if work.get("doi"):
            by_doi[normalize_doi(work["doi"])] = work["work_id"]
        if work.get("title"):
            by_title.setdefault(normalize_title(work["title"]), work["work_id"])

    def locate(
        *,
        arxiv_id: str | None,
        doi: str | None,
        title: str,
        authors: list[str] | None = None,
        year: int | None = None,
    ) -> dict:
        doi = normalize_doi(doi)
        key = (
            (by_arxiv.get(arxiv_id) if arxiv_id else None)
            or (by_doi.get(doi) if doi else None)
            or by_title.get(normalize_title(title))
        )
        if key:
            work = works[key]
            if arxiv_id and not work.get("arxiv_id"):
                work["arxiv_id"] = arxiv_id
                by_arxiv[arxiv_id] = key
                if work.get("first_public_date_source") != "arxiv_v1":
                    work["first_public_date"] = None
                    work["first_public_date_precision"] = "unknown"
                    work["first_public_date_source"] = "unknown"
            if doi and not work.get("doi"):
                work["doi"] = doi
                by_doi[doi] = key
            return work
        work_id = canonical_work_id(
            arxiv_id=arxiv_id,
            doi=doi,
            title=title,
            first_author=(authors or [None])[0],
            year=year,
        )
        work = empty_work(work_id, title)
        work["arxiv_id"] = arxiv_id
        work["doi"] = doi
        register(work)
        return work

    for row in preprints:
        work = locate(
            arxiv_id=row["arxiv_id"],
            doi=row.get("doi"),
            title=row["title"],
            authors=row.get("authors"),
            year=int(row["first_submitted"][:4]),
        )
        work.update(
            {
                "title": row["title"],
                "authors": row.get("authors") or [],
                "institutions": row.get("institutions") or [],
                "abstract": row.get("abstract") or "",
                "first_public_date": row["first_submitted"],
                "first_public_date_precision": "day",
                "first_public_date_source": "arxiv_v1",
                "arxiv_id": row["arxiv_id"],
                "doi": normalize_doi(row.get("doi")),
                "primary_topic": row.get("primary_topic"),
                "topics": row.get("topics") or [],
                "tags": row.get("tags") or [],
                "relevance": row.get("relevance") or work["relevance"],
                "arxiv_categories": row.get("categories") or [],
                "period": row.get("period"),
            }
        )
        add_version(
            work,
            {
                "kind": "preprint",
                "url": row["arxiv_url"],
                "date": row["first_submitted"],
                "venue": "arXiv",
                "year": int(row["first_submitted"][:4]),
                "status": "preprint",
                "evidence_source": "arXiv Atom API",
            },
        )
        register(work)

    for row in publications:
        work = locate(
            arxiv_id=row.get("arxiv_id"),
            doi=row.get("doi"),
            title=row["title"],
            authors=row.get("authors"),
            year=row.get("year"),
        )
        if not work["abstract"] and row.get("abstract"):
            work["abstract"] = row["abstract"]
        work["authors"] = merge_unique(work["authors"], row.get("authors") or [])
        work["institutions"] = merge_unique(
            work["institutions"], row.get("institutions") or []
        )
        work["topics"] = merge_unique(work["topics"], row.get("topics") or [])
        work["tags"] = merge_unique(work["tags"], row.get("tags") or [])
        work["relevance"] = stronger_relevance(
            work["relevance"], row.get("relevance") or {}
        )
        if not work["primary_topic"] and row.get("primary_topic"):
            work["primary_topic"] = row["primary_topic"]
        if (
            not work["first_public_date"]
            and not work.get("arxiv_id")
            and row.get("publication_date")
        ):
            work["first_public_date"] = row["publication_date"]
            work["first_public_date_precision"] = row.get("date_precision", "unknown")
            work["first_public_date_source"] = "publication"
        add_version(
            work,
            {
                "kind": row["publication_type"],
                "url": row["official_url"],
                "date": row.get("publication_date"),
                "venue": row["venue"],
                "year": row["year"],
                "status": row["verification_status"],
                "doi": row.get("doi"),
                "evidence_source": row.get("discovery_source"),
            },
        )
        if row.get("citation_count_snapshot") is not None:
            work["citation_count_snapshot"] = row["citation_count_snapshot"]
            work["citation_snapshot_date"] = row.get("citation_snapshot_date")
        register(work)

    for row in official_records:
        work = locate(
            arxiv_id=row.get("arxiv_id"),
            doi=row.get("doi"),
            title=row["title"],
            authors=row.get("authors"),
            year=row.get("event_year"),
        )
        work["authors"] = merge_unique(work["authors"], row.get("authors") or [])
        work["topics"] = merge_unique(work["topics"], row.get("topics") or [])
        work["tags"] = merge_unique(work["tags"], row.get("tags") or [])
        work["relevance"] = stronger_relevance(
            work["relevance"], row.get("relevance") or {}
        )
        if not work["primary_topic"] and row.get("primary_topic"):
            work["primary_topic"] = row["primary_topic"]
        if not work["first_public_date"] and not work.get("arxiv_id"):
            work["first_public_date"] = row["publication_date"]
            work["first_public_date_precision"] = "day"
            work["first_public_date_source"] = "publication"
        add_version(
            work,
            {
                "kind": "conference",
                "url": row["official_url"],
                "date": row["publication_date"],
                "venue": row["venue"],
                "year": row["event_year"],
                "status": row["verification_status"],
                "evidence_source": row["official_container_url"],
            },
        )
        work["strict_peer_reviewed"] = True
        work["strict_peer_review_evidence"] = merge_unique(
            work["strict_peer_review_evidence"], [row["official_url"]]
        )
        register(work)

    for row in official_programs:
        work = locate(
            arxiv_id=row.get("arxiv_id"),
            doi=row.get("doi"),
            title=row["title"],
            authors=row.get("authors"),
            year=row.get("year"),
        )
        if not work["abstract"] and row.get("abstract"):
            work["abstract"] = row["abstract"]
        work["authors"] = merge_unique(work["authors"], row.get("authors") or [])
        work["institutions"] = merge_unique(
            work["institutions"], row.get("institutions") or []
        )
        work["topics"] = merge_unique(work["topics"], row.get("topics") or [])
        work["tags"] = merge_unique(work["tags"], row.get("tags") or [])
        work["relevance"] = stronger_relevance(
            work["relevance"], row.get("relevance") or {}
        )
        if not work["primary_topic"] and row.get("primary_topic"):
            work["primary_topic"] = row["primary_topic"]
        add_version(
            work,
            {
                "kind": "conference",
                "url": row["official_url"],
                "date": None,
                "venue": row["venue"],
                "year": row["year"],
                "status": row["verification_status"],
                "evidence_source": row["official_container_url"],
            },
        )
        register(work)

    # Preserve the manually verified cross-field anchors while the new official
    # source crawlers are expanded beyond RSS/CoRL.
    for row in legacy_peers:
        work = locate(
            arxiv_id=row.get("arxiv_id"),
            doi=row.get("doi"),
            title=row["title"],
            authors=row.get("authors"),
            year=int(row["year"]),
        )
        add_version(
            work,
            {
                "kind": "conference",
                "url": row["official_url"],
                "date": None,
                "venue": row["venue"],
                "year": int(row["year"]),
                "status": row.get("status") or "peer_reviewed_official",
                "evidence_source": "manually verified official page",
            },
        )
        work["strict_peer_reviewed"] = True
        work["strict_peer_review_evidence"] = merge_unique(
            work["strict_peer_review_evidence"], [row["official_url"]]
        )
        if row.get("arxiv_v1_date"):
            work["first_public_date"] = row["arxiv_v1_date"]
            work["first_public_date_precision"] = "day"
            work["first_public_date_source"] = "arxiv_v1"
            add_version(
                work,
                {
                    "kind": "preprint",
                    "url": f"https://arxiv.org/abs/{row['arxiv_id']}",
                    "date": row["arxiv_v1_date"],
                    "venue": "arXiv",
                    "year": int(row["arxiv_v1_date"][:4]),
                    "status": "preprint",
                    "evidence_source": "manually verified legacy anchor",
                },
            )

    legacy_by_id = {row["id"]: row for row in legacy_papers}
    for arxiv_id, key in by_arxiv.items():
        legacy = legacy_by_id.get(arxiv_id)
        if not legacy:
            continue
        work = works[key]
        if legacy.get("curated"):
            work["curated"] = True
            work["contribution_zh"] = legacy.get("contribution_zh") or ""
            work["limitation_zh"] = legacy.get("limitation_zh") or ""
            work["selection_reason_zh"] = legacy.get("selection_reason_zh") or ""
            work["evidence"] = legacy.get("evidence") or {}
            work["institutions"] = merge_unique(
                work["institutions"], legacy.get("institutions") or []
            )

    for repo in repositories:
        keys = []
        for arxiv_id in repo.get("paper_ids") or []:
            if arxiv_id in by_arxiv:
                keys.append(by_arxiv[arxiv_id])
        for doi in repo.get("dois") or []:
            doi_key = normalize_doi(doi)
            if doi_key in by_doi:
                keys.append(by_doi[doi_key])
        for key in set(keys):
            work = works[key]
            work["repositories"] = merge_unique(
                work["repositories"], [repo["repo_full_name"]]
            )
            add_version(
                work,
                {
                    "kind": "repository",
                    "url": repo["html_url"],
                    "date": repo["created_at"][:10],
                    "venue": "GitHub",
                    "year": int(repo["created_at"][:4]),
                    "status": "verified_repository",
                    "evidence_source": "GitHub API snapshot",
                },
            )

    output = sorted(
        works.values(),
        key=lambda row: (
            row.get("first_public_date") or "9999-12-31",
            row["work_id"],
        ),
    )
    for work in output:
        work["versions"].sort(
            key=lambda row: (row.get("date") or "9999-12-31", row.get("url") or "")
        )
        # Abstracts remain in the source-version stores. Avoid duplicating tens
        # of megabytes in the canonical graph.
        work["abstract_available"] = bool(work.get("abstract"))
        work.pop("abstract", None)
    OUTPUT.write_text(
        json.dumps(output, ensure_ascii=False, separators=(",", ":")) + "\n"
    )
    coverage = {
        "generated_at": SNAPSHOT_DATE,
        "canonical_works": len(output),
        "with_arxiv": sum(bool(row.get("arxiv_id")) for row in output),
        "published_versions": sum(
            version["kind"] in {"conference", "journal"}
            for row in output
            for version in row["versions"]
        ),
        "works_with_publication": sum(
            any(version["kind"] in {"conference", "journal"} for version in row["versions"])
            for row in output
        ),
        "strict_peer_reviewed_works": sum(row["strict_peer_reviewed"] for row in output),
        "works_with_repository": sum(bool(row["repositories"]) for row in output),
        "curated_works": sum(row["curated"] for row in output),
        "included_works": sum(
            row["relevance"].get("status") == "included" for row in output
        ),
        "candidate_works": sum(
            row["relevance"].get("status") == "candidate" for row in output
        ),
        "manual_review_works": sum(
            row["relevance"].get("status") == "manual_review" for row in output
        ),
        "by_primary_topic": dict(
            Counter(
                row["primary_topic"]
                for row in output
                if row.get("primary_topic")
                and row["relevance"].get("status") == "included"
            )
        ),
        "source_counts": {
            "preprints": len(preprints),
            "publication_records": len(publications),
            "strict_official_records": len(official_records),
            "official_program_or_pending_records": len(official_programs),
            "verified_repositories": len(repositories),
            "legacy_manual_peer_anchors": len(legacy_peers),
        },
        "date_rule": (
            "Monthly trend date is arXiv v1 when available; publication dates are "
            "kept on versions and never overwrite the first-public date."
        ),
    }
    COVERAGE.write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n")
    print(
        f"Saved {len(output)} canonical works; "
        f"{coverage['strict_peer_reviewed_works']} strict peer-reviewed, "
        f"{coverage['works_with_repository']} linked to repositories.",
        flush=True,
    )


if __name__ == "__main__":
    main()
