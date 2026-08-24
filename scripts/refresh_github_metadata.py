#!/usr/bin/env python3
"""Refresh current GitHub metadata and collect a recent-paper watchlist.

The independent-adoption score is intentionally not recomputed here: it uses
issue/PR author sampling and dependency evidence from the deeper audit. This
script refreshes volatile repository metadata, preserves the score's original
observation date, and keeps newly discovered repositories in a separate
watchlist until they receive the same adoption audit.
"""

from __future__ import annotations

import json
import subprocess
import time
from collections import Counter

from radar_common import ROOT

REPOSITORIES = ROOT / "data" / "repositories.json"
COVERAGE = ROOT / "data" / "repository-coverage.json"
SEEDS = ROOT / "config" / "github-watchlist-seeds.json"
WATCHLIST = ROOT / "data" / "github-watchlist.json"
SNAPSHOT_DATE = json.loads(
    (ROOT / "config" / "source-registry.json").read_text()
)["window"]["until"]


def github_repo(full_name: str) -> dict:
    for attempt in range(5):
        result = subprocess.run(
            ["gh", "api", f"repos/{full_name}"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            # GitHub applies secondary burst limits before the hourly quota.
            # A small delay keeps a full 42-repository refresh reproducible.
            time.sleep(1.8)
            return json.loads(result.stdout)
        if attempt == 4:
            raise RuntimeError(
                f"GitHub metadata failed for {full_name}: {result.stderr.strip()}"
            )
        time.sleep(10 * (attempt + 1))
    raise RuntimeError("unreachable")


def apply_metadata(record: dict, payload: dict) -> None:
    previous_snapshot = record.get("metadata_snapshot_date") or record.get("snapshot_date")
    record.update(
        {
            "repo_full_name": payload["full_name"],
            "html_url": payload["html_url"],
            "url_verified": True,
            "description": payload.get("description"),
            "homepage": payload.get("homepage"),
            "topics": payload.get("topics") or [],
            "stars": payload["stargazers_count"],
            "forks": payload["forks_count"],
            "watchers_subscribers": payload["subscribers_count"],
            "created_at": payload["created_at"],
            "updated_at": payload["updated_at"],
            "pushed_at": payload["pushed_at"],
            "license": (payload.get("license") or {}).get("spdx_id"),
            "archived": payload["archived"],
            "fork_repository": payload["fork"],
            "open_items_github": payload["open_issues_count"],
            "metadata_snapshot_date": SNAPSHOT_DATE,
            "adoption_snapshot_date": record.get("adoption_snapshot_date") or previous_snapshot,
            "snapshot_date": SNAPSHOT_DATE,
        }
    )
    signals = record.get("independent_adoption", {}).get("signals", [])
    record.get("independent_adoption", {})["signals"] = [
        f"forks:{record['forks']}" if signal.startswith("forks:") else signal
        for signal in signals
    ]


def main() -> None:
    records = json.loads(REPOSITORIES.read_text())
    for index, record in enumerate(records, 1):
        payload = github_repo(record["repo_full_name"])
        apply_metadata(record, payload)
        print(f"metadata {index}/{len(records)}: {payload['full_name']}", flush=True)
    REPOSITORIES.write_text(
        json.dumps(records, ensure_ascii=False, separators=(",", ":")) + "\n"
    )

    seed_rows = json.loads(SEEDS.read_text())["repositories"]
    watch_rows = []
    audited = {record["repo_full_name"].lower() for record in records}
    for seed in seed_rows:
        payload = github_repo(seed["repo_full_name"])
        if payload["full_name"].lower() in audited:
            continue
        watch_rows.append(
            {
                **seed,
                "repo_full_name": payload["full_name"],
                "html_url": payload["html_url"],
                "description": payload.get("description"),
                "homepage": payload.get("homepage"),
                "topics": payload.get("topics") or [],
                "stars": payload["stargazers_count"],
                "forks": payload["forks_count"],
                "created_at": payload["created_at"],
                "updated_at": payload["updated_at"],
                "pushed_at": payload["pushed_at"],
                "license": (payload.get("license") or {}).get("spdx_id"),
                "archived": payload["archived"],
                "snapshot_date": SNAPSHOT_DATE,
                "status": "new_repo_pending_adoption_audit",
            }
        )
    WATCHLIST.write_text(
        json.dumps(watch_rows, ensure_ascii=False, separators=(",", ":")) + "\n"
    )

    old_coverage = json.loads(COVERAGE.read_text())
    old_coverage.update(
        {
            "generated_at": SNAPSHOT_DATE,
            "metadata_refreshed": len(records),
            "adoption_score_snapshot": min(
                record["adoption_snapshot_date"] for record in records
            ),
            "new_watchlist_count": len(watch_rows),
            "new_watchlist_status": dict(Counter(row["status"] for row in watch_rows)),
            "warning": (
                "Stars, forks and repository metadata were refreshed on the generated date. "
                "Independent-adoption scores retain their earlier observation date; newly "
                "discovered repositories remain a separate watchlist until the same issue/PR "
                "and dependency audit is completed."
            ),
        }
    )
    COVERAGE.write_text(json.dumps(old_coverage, ensure_ascii=False, indent=2) + "\n")
    print(
        f"Refreshed {len(records)} audited repositories; "
        f"added {len(watch_rows)} recent-paper watchlist repositories.",
        flush=True,
    )


if __name__ == "__main__":
    main()
