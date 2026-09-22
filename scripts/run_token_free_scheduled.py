#!/usr/bin/env python3
"""Run one bounded token-free research batch for the local LaunchAgent."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIN_FREE_GIB = 6
FETCH_LIMIT = 25
PROCESS_LIMIT = 25
PUBLISH_INTERVAL_SECONDS = 2 * 60 * 60
PUBLISH_STATE = ROOT / ".research/token-free-research/publish-state.json"


def publish_due() -> bool:
    if not PUBLISH_STATE.is_file():
        return True
    try:
        previous = json.loads(PUBLISH_STATE.read_text())["last_success_at"]
        at = datetime.fromisoformat(previous.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - at).total_seconds() >= PUBLISH_INTERVAL_SECONDS
    except (KeyError, ValueError, OSError):
        return True


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    free_bytes = shutil.disk_usage(ROOT).free
    reserve_bytes = MIN_FREE_GIB * 1024**3
    low_disk = free_bytes < reserve_bytes
    if low_disk:
        print(json.dumps({"status": "paused_low_disk_space", "free_bytes": free_bytes,
                          "required_free_bytes": reserve_bytes}), flush=True)

    command = [sys.executable, str(ROOT / "scripts/token_free_research.py"),
               "--fetch", "--fetch-limit", str(FETCH_LIMIT),
               "--process-limit", str(PROCESS_LIMIT)]
    publish_command = [sys.executable, str(ROOT / "scripts/publish_token_free_batch.py"), "--apply"]
    due = low_disk or publish_due()
    if args.dry_run:
        print(json.dumps({"status": "paused_low_disk_space" if low_disk else "ready",
                          "free_bytes": free_bytes,
                          "required_free_bytes": reserve_bytes,
                          "fetch_limit": FETCH_LIMIT, "process_limit": PROCESS_LIMIT,
                          "fetch_command": None if low_disk else command,
                          "publish_due": due, "publish_command": publish_command if due else None}), flush=True)
        return 0
    fetch_status = 0 if low_disk else subprocess.call(command, cwd=ROOT)
    publish_status = subprocess.call(publish_command, cwd=ROOT) if due else 0
    return fetch_status or publish_status


if __name__ == "__main__":
    raise SystemExit(main())
