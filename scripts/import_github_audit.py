#!/usr/bin/env python3
"""Normalize the verified GitHub audit into the v2 structured evidence store."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from radar_common import ROOT, classify_research, extract_arxiv_id, normalize_doi

SOURCE = ROOT / ".research" / "github-expansion-audit.json"
OUTPUT = ROOT / "data" / "repositories.json"
COVERAGE = ROOT / "data" / "repository-coverage.json"
SNAPSHOT_DATE = json.loads((ROOT / "config" / "source-registry.json").read_text())["window"]["until"]


def extract_links(record: dict) -> tuple[list[str], list[str]]:
    urls = []
    paper = record.get("associated_paper")
    if paper and paper.get("url"):
        urls.append(paper["url"])
    urls.extend(record.get("additional_paper_links_from_readme") or [])
    arxiv_ids = list(dict.fromkeys(filter(None, (extract_arxiv_id(url) for url in urls))))
    dois = []
    for url in urls:
        match = re.search(r"(?:doi\.org/|doi:)(10\.\d{4,9}/\S+)", url, re.I)
        if match:
            doi = normalize_doi(match.group(1))
            if doi and doi not in dois:
                dois.append(doi)
    return arxiv_ids, dois


def asset_type(category: str) -> str:
    if "Awesome" in category:
        return "awesome_list"
    if "Benchmark" in category:
        return "benchmark"
    if "数据" in category:
        return "dataset"
    if any(term in category for term in ["平台", "运行时", "框架", "仿真", "引擎", "接口"]):
        return "framework"
    if any(term in category for term in ["基础模型", "VLA", "世界模型"]):
        return "model"
    return "code"


def normalize(record: dict) -> dict:
    snapshot = record["github_snapshot"]
    activity = record["issue_pr_activity"]
    adoption = record["external_adoption_and_dependencies"]
    release = record["release"]
    assets = record["assets"]
    paper_ids, dois = extract_links(record)
    paper_title = (record.get("associated_paper") or {}).get("title") or ""
    classification = classify_research(
        title=f"{paper_title} {record['repo']}",
        abstract=record.get("description") or "",
        extra_text=record.get("category") or "",
        source_is_robotics=True,
    )
    primary_topic = classification.pop("primary_topic")
    topics = classification.pop("topics")
    tags = classification.pop("tags")
    classification.pop("topic_scores")
    signals = [
        f"external_pr_authors_12m:{activity['external_pr_authors_in_first_100']}",
        f"external_issue_authors_12m:{activity['external_issue_authors_in_first_100']}",
        f"contributors_first_page:{record['contributors']['first_page_count']}",
        f"merged_prs_recent_sample:{activity['merged_prs_in_first_100_recent_prs']}",
        f"forks:{snapshot['forks']}",
    ]
    return {
        "repo_full_name": record["repo"],
        "html_url": record["canonical_url"],
        "url_verified": record["url_verified"],
        "description": record.get("description"),
        "homepage": record.get("homepage"),
        "topics": snapshot.get("topics") or [],
        "stars": snapshot["stars"],
        "forks": snapshot["forks"],
        "watchers_subscribers": snapshot["watchers_subscribers"],
        "created_at": snapshot["created_at"],
        "updated_at": snapshot["updated_at"],
        "pushed_at": snapshot["pushed_at"],
        "license": snapshot.get("license_spdx"),
        "archived": snapshot["archived"],
        "fork_repository": snapshot["fork_repository"],
        "open_issues": snapshot["open_issues"],
        "open_pull_requests": snapshot["open_pull_requests"],
        "asset_type": asset_type(record["category"]),
        "category_zh": record["category"],
        "tracking_priority": record["tracking_priority"],
        "paper_ids": paper_ids,
        "dois": dois,
        "associated_paper": record.get("associated_paper"),
        "primary_topic": primary_topic,
        "topics_research": topics,
        "tags": tags,
        "latest_release": release.get("latest"),
        "release_count": release.get("total_releases", 0),
        "contributors": record["contributors"],
        "activity_12m": activity,
        "independent_adoption": {
            "score": int(adoption["independent_adoption_score"]),
            "band_zh": adoption["score_band"],
            "confidence": adoption["confidence"],
            "signals": signals,
            "dependency_count": adoption.get("dependency_graph_dependents"),
            "dependency_note": adoption.get("dependency_note"),
        },
        "assets": assets,
        "relevance": classification,
        "snapshot_date": SNAPSHOT_DATE,
    }


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"missing verified source audit: {SOURCE}")
    source = json.loads(SOURCE.read_text())
    records = [normalize(record) for record in source["records"]]
    records.sort(
        key=lambda row: (
            row["tracking_priority"],
            -row["independent_adoption"]["score"],
            row["repo_full_name"].lower(),
        )
    )
    OUTPUT.write_text(
        json.dumps(records, ensure_ascii=False, separators=(",", ":")) + "\n"
    )
    mapped = [record for record in records if record["paper_ids"] or record["dois"]]
    coverage = {
        "generated_at": SNAPSHOT_DATE,
        "repository_count": len(records),
        "url_verified": sum(record["url_verified"] for record in records),
        "paper_mapped": len(mapped),
        "arxiv_mapped": sum(bool(record["paper_ids"]) for record in records),
        "doi_mapped": sum(bool(record["dois"]) for record in records),
        "archived": sum(record["archived"] for record in records),
        "license_missing_or_unrecognized": sum(
            record["license"] in {None, "NOASSERTION"} for record in records
        ),
        "by_asset_type": dict(Counter(record["asset_type"] for record in records)),
        "by_topic": dict(
            Counter(record["primary_topic"] for record in records if record["primary_topic"])
        ),
        "independent_adoption_bands": dict(
            Counter(record["independent_adoption"]["band_zh"] for record in records)
        ),
        "scoring_note": source["scoring_note"],
        "warning": (
            "Stars are stored as reach metadata but excluded from the independent-adoption score. "
            "A missing reverse-dependency count remains null and is never replaced by forks."
        ),
    }
    COVERAGE.write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n")
    print(
        f"Saved {len(records)} verified repositories; {len(mapped)} linked to paper evidence.",
        flush=True,
    )


if __name__ == "__main__":
    main()
