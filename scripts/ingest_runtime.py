"""Timed, disk-backed incoming tables keep full source preparation out of RSS."""
from __future__ import annotations

import json
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from catalog_store import TABLES, encode
from weekly_runtime import wait_resource_headroom


def stage(name, function):
    reason = wait_resource_headroom(180)
    if reason:
        print(json.dumps({"status": "catalog_stage_blocked", "stage": name, "reason": reason}), flush=True)
        raise RuntimeError(reason)
    wall, cpu = time.monotonic(), time.process_time()
    print(json.dumps({"status": "catalog_stage_started", "stage": name,
                      "at": datetime.now(timezone.utc).isoformat()}), flush=True)
    try:
        value = function()
    except BaseException as error:
        print(json.dumps({"status": "catalog_stage_failed", "stage": name,
                          "error_type": type(error).__name__,
                          "wall_seconds": round(time.monotonic() - wall, 3),
                          "cpu_seconds": round(time.process_time() - cpu, 3)}), flush=True)
        raise
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(json.dumps({"status": "catalog_stage_finished", "stage": name,
                      "wall_seconds": round(time.monotonic() - wall, 3),
                      "cpu_seconds": round(time.process_time() - cpu, 3),
                      "peak_rss_mib": round(peak / (1024**2 if sys.platform == "darwin" else 1024), 1)}), flush=True)
    return value


class DiskRows:
    """Repeatable iteration; each consumer gets the same public source values."""
    def __init__(self, path):
        self.path = Path(path)

    def __iter__(self):
        keys = {}
        def shared_keys(pairs):
            return {keys.setdefault(key, key): value for key, value in pairs}
        with self.path.open() as stream:
            for line in stream:
                yield json.loads(line, object_pairs_hook=shared_keys)


def spool_incoming(folder, payload):
    folder = Path(folder)
    for table in TABLES:
        with (folder / (table + ".jsonl")).open("w") as stream:
            for row in payload.get(table, []):
                stream.write(encode(row) + "\n")
    (folder / "input-counts.json").write_text(encode({"input_counts": payload.get("input_counts", {}),
                                                   "tables": [key for key in TABLES if key in payload]}))


def load_incoming(folder):
    folder = Path(folder)
    metadata = json.loads((folder / "input-counts.json").read_text())
    return {**{table: DiskRows(folder / (table + ".jsonl")) for table in metadata["tables"]},
            "input_counts": metadata["input_counts"]}
