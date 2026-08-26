#!/usr/bin/env python3
"""End-to-end fixture test for X collection, privacy and weekly ranking."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(*args: str) -> None:
    subprocess.run([sys.executable, *args], cwd=ROOT, check=True, capture_output=True, text=True)


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="x-radar-fixture-") as raw:
        target = Path(raw)
        store = target / "posts.json"
        weekly = target / "weekly.json"
        docs = target / "docs"
        run(
            "scripts/collect_x_discussions.py",
            "--fixture", "tests/fixtures/x-recent-search.json",
            "--store", str(store),
            "--start", "2026-08-17T00:00:00Z",
            "--end", "2026-08-24T00:00:00Z",
        )
        run(
            "scripts/generate_x_weekly.py",
            "--store", str(store),
            "--output-data", str(weekly),
            "--docs-root", str(docs),
            "--week", "2026-W34",
        )
        post_store = json.loads(store.read_text())
        report = json.loads(weekly.read_text())["weeks"][0]
        assert len(post_store["posts"]) == 6
        assert all("text" not in post for post in post_store["posts"])
        assert report["post_count"] == 6
        assert report["unique_authors"] == 6
        assert report["ranked_topic_count"] == 3
        assert {row["lane"] for row in report["top_topics"]} == {"research", "startup", "discussion"}
        assert any(row["cluster_key"] == "arxiv:2608.00001" for row in report["top_topics"])
        assert any(row["label_zh"].startswith("Genesis AI") for row in report["top_topics"])
        assert (docs / "social" / "weekly" / "2026-w34.md").exists()
    print("X discussion fixture test passed: collection, privacy, clustering and three-lane ranking.")


if __name__ == "__main__":
    main()
