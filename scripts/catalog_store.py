"""Persistent, sharded catalog IO; exports must never mutate this store."""
from __future__ import annotations

import hashlib
import json
import copy
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timezone
try:
    from source_record_store import read_source_records, source_record_layout, source_record_paths, validated_rows, write_source_records
except ModuleNotFoundError:
    from scripts.source_record_store import read_source_records, source_record_layout, source_record_paths, validated_rows, write_source_records

TABLES = {
    "works": "work_id", "manifestations": "manifestation_id",
    "organizations": "organization_id", "work-organization-links": None,
    "source-records": "source_record_id", "field-provenance": None,
    "work-aliases": None, "evidence-events": "event_id",
    "editorial-claims": "claim_id", "work-relations": None,
    "reconciliation": "source_record_id", "taxonomy-assignments": None,
    "source-health": "source_id",
    "organization-candidates": "candidate_id",
    "text-snapshots": "snapshot_id",
    "report-text-snapshots": "snapshot_id",
}


def encode(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value) -> str:
    return hashlib.sha256(encode(value).encode()).hexdigest()


def write_if_changed(path: Path, text: str) -> bool:
    if path.exists() and path.read_text() == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text)
    temporary.replace(path)
    return True


def read_table(root: Path, table: str) -> list[dict]:
    if table == "source-records":
        return read_source_records(root)
    directory = root / table
    paths = sorted(directory.glob("*.jsonl")) if directory.is_dir() else [root / f"{table}.jsonl"]
    result = []
    for path in paths:
        if path.exists():
            result.extend(json.loads(line) for line in path.read_text().splitlines() if line.strip())
    return result


def write_table(root: Path, table: str, rows: list[dict]) -> None:
    if table == "source-records":
        write_source_records(root, rows, write_if_changed)
        return
    key = TABLES[table]
    ordered = sorted(rows, key=lambda row: str(row.get(key, "")) if key else encode(row))
    if table in {"works", "text-snapshots"}:
        shards = defaultdict(list)
        for row in ordered:
            shards[hashlib.sha1(row[key].encode()).hexdigest()[:2]].append(row)
        for number in range(256):
            shard = f"{number:02x}"
            write_if_changed(root / table / f"{shard}.jsonl", "".join(encode(row) + "\n" for row in shards[shard]))
        legacy = root / "works.jsonl" if table == "works" else root / "no-legacy-text-table"
        if legacy.exists():
            # The superseded generated prototype is backed up outside the public
            # catalog; never remove the user's only copy on the first migration.
            backup = root.parent / "migration-archive" / "v3-prototype-works.jsonl"
            if not backup.exists():
                backup.parent.mkdir(parents=True, exist_ok=True)
                legacy.replace(backup)
            else:
                legacy.unlink()
    else:
        write_if_changed(root / f"{table}.jsonl", "".join(encode(row) + "\n" for row in ordered))


def save_catalog(root: Path, payload: dict, metadata: dict) -> dict:
    # Fail before writing ANY table if an explicit migration is in progress or
    # source records are invalid. Existing legacy layout is not migrated here.
    source_record_layout(root)
    validated_rows(payload.get("source-records", []))
    for table in TABLES:
        write_table(root, table, payload.get(table, []))
    hashes = {}
    for table in TABLES:
        hashes[table] = fingerprint(sorted(payload.get(table, []), key=encode))
    result = {**metadata, "schema_version": "3.1", "table_hashes": hashes,
              "catalog_hash": fingerprint(hashes)}
    if result["catalog_hash"] != metadata.get("catalog_hash") or not metadata.get("ingested_at"):
        result["ingested_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    write_if_changed(root / "manifest.json", encode(result) + "\n")
    return result


def table_output_paths(root: Path, table: str) -> list[Path]:
    """Exact writes for weekly checkpoint/rollback; never a cleanup glob."""
    if table == "source-records":
        return source_record_paths(root, for_write=True)
    if table in {"works", "text-snapshots"}:
        return [root / table / f"{number:02x}.jsonl" for number in range(256)]
    return [root / f"{table}.jsonl"]


def load_catalog(root: Path) -> tuple[dict, dict]:
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError("Catalog has not been migrated. Run v3:migrate once before building.")
    return ({table: read_table(root, table) for table in TABLES},
            json.loads(manifest_path.read_text()))


def revision_snapshot(root: Path, month: str, payload: dict, *, persist: bool) -> dict:
    """Version based on content, not build time; read-only CI exports use the ledger."""
    path = root / month / "history.json"
    history = json.loads(path.read_text()) if path.exists() else []
    current = copy.deepcopy({key: value for key, value in payload.items() if key not in {"revision", "revision_persisted", "revisions", "generated_at", "data_through"}})
    # Advancing the observation clock alone is not a new research revision.
    retrospective = current.get("retrospective_evidence", {})
    retrospective.pop("as_of", None)
    for signal in retrospective.get("trend_ledger", []):
        signal.pop("evidence_as_of", None)
    content_hash = fingerprint(current)
    entry = history[-1] if history and history[-1]["content_hash"] == content_hash else None
    if entry is None:
        previous_path = root / month / f"r{history[-1]['revision']}.json" if history else None
        previous = json.loads(previous_path.read_text()) if previous_path and previous_path.exists() else {}
        coverage_before, coverage_after = previous.get("coverage", {}), payload.get("coverage", {})
        differences = {"coverage": {key: {"before": coverage_before.get(key), "after": value} for key, value in coverage_after.items() if coverage_before.get(key) != value}}
        if "work_ids" in previous and "work_ids" in payload:
            differences["added_work_ids"] = sorted(set(payload["work_ids"]) - set(previous["work_ids"]))
            differences["removed_work_ids"] = sorted(set(previous["work_ids"]) - set(payload["work_ids"]))
        previous_claims = {row["claim_id"]: row for row in previous.get("executive_findings", [])}
        current_claims = {row["claim_id"]: row for row in payload.get("executive_findings", [])}
        differences["changed_claim_ids"] = sorted(key for key in previous_claims.keys() | current_claims.keys() if previous_claims.get(key) != current_claims.get(key))
        entry = {"revision": len(history) + 1, "content_hash": content_hash,
                 "data_through": payload.get("data_through"),
                 "summary": "首次月份快照" if not history else "来源、分类或证据更新",
                 "differences": differences}
        if persist:
            history.append(entry)
            write_if_changed(path, encode(history) + "\n")
            write_if_changed(root / month / f"r{entry['revision']}.json", encode({**payload, "revision": entry["revision"]}) + "\n")
    visible_history = history if history and history[-1] == entry else [*history, entry]
    return {**payload, "revision": entry["revision"], "revision_persisted": bool(history and history[-1] == entry), "revisions": visible_history}
