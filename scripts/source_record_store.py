"""Source-record storage layouts. No implicit migration and no record rewriting.

Legacy files remain writable until the explicit migration CLI is used. A
sharded source table has exactly 00..ff.jsonl, including empty partitions.
Both layouts return global source_record_id order, so physical partitioning
does not change research-state hashes or downstream insertion order.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path

TABLE = "source-records"
ID = "source_record_id"
LEGACY = TABLE + ".jsonl"
MIGRATION_MARKER = ".source-records-migration.json"
SHARD_NAMES = tuple(f"{i:02x}.jsonl" for i in range(256))


def fail(code):
    raise ValueError("source_record_store:" + code)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def strict_json(raw):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                fail("duplicate_json_key")
            out[key] = value
        return out

    def nonfinite(_):
        fail("nonfinite_json_number")

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def shard_name(source_id):
    if not isinstance(source_id, str) or not source_id:
        fail("missing_or_invalid_source_record_id")
    return hashlib.sha1(source_id.encode("utf-8")).hexdigest()[:2] + ".jsonl"


def _regular(path):
    try:
        status = path.lstat()
    except FileNotFoundError:
        fail("source_file_missing")
    if not stat.S_ISREG(status.st_mode):
        fail("regular_source_file_required")


def read_bytes(path):
    """Reject symlinks and detect changes to this opened regular file."""
    path = Path(path)
    _regular(path)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            fail("regular_source_file_required")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            raw = stream.read()
        after = os.fstat(descriptor)
        current = path.lstat()
        fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns", "st_mode")
        if any(getattr(before, field) != getattr(after, field) or getattr(after, field) != getattr(current, field)
               for field in fields):
            fail("source_changed_while_reading")
        return raw
    finally:
        os.close(descriptor)


def partition_paths(directory):
    directory = Path(directory)
    if directory.is_symlink() or not directory.is_dir():
        fail("regular_shard_directory_required")
    if {entry.name for entry in directory.iterdir()} != set(SHARD_NAMES):
        fail("incomplete_or_unexpected_shard_files")
    paths = [directory / name for name in SHARD_NAMES]
    for path in paths:
        _regular(path)
    return paths


def source_record_layout(root):
    root = Path(root)
    if root.is_symlink():
        fail("catalog_symlink_not_allowed")
    if os.path.lexists(root / MIGRATION_MARKER):
        fail("migration_in_progress_recovery_required")
    legacy, directory = root / LEGACY, root / TABLE
    has_file, has_directory = os.path.lexists(legacy), os.path.lexists(directory)
    if has_file and has_directory:
        fail("mixed_legacy_and_sharded_layout")
    if has_directory:
        partition_paths(directory)
        return "sharded"
    if has_file:
        _regular(legacy)
        return "legacy"
    manifest_path = root / "manifest.json"
    if os.path.lexists(manifest_path):
        manifest = strict_json(read_bytes(manifest_path).decode("utf-8"))
        if not isinstance(manifest, dict):
            fail("catalog_manifest_object_required")
        hashes = manifest.get("table_hashes")
        if isinstance(hashes, dict) and TABLE in hashes and hashes[TABLE] != digest([]):
            fail("declared_nonempty_source_table_missing")
    return "missing"


def source_record_paths(root, *, for_write=False):
    root = Path(root)
    layout = source_record_layout(root)
    if layout == "sharded":
        return [root / TABLE / name for name in SHARD_NAMES]
    # No implicit migration when creating a new catalogue or running ingestion.
    return [root / LEGACY] if layout == "legacy" or for_write else []


def parse_lines(raw, *, expected_shard=None, strict_lines=False):
    """Return records with their original bytes; never silently deduplicate."""
    entries = []
    for line in raw.splitlines(keepends=True):
        if not line.strip():
            if strict_lines:
                fail("blank_legacy_line_requires_review")
            continue
        if strict_lines and not line.endswith(b"\n"):
            fail("unterminated_legacy_line_requires_review")
        row = strict_json(line.decode("utf-8"))
        if not isinstance(row, dict):
            fail("source_record_object_required")
        name = shard_name(row.get(ID))
        if expected_shard is not None and name != expected_shard:
            fail("source_record_in_wrong_shard")
        entries.append((row, line))
    return entries


def validated_rows(rows):
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            fail("source_record_object_required")
        shard_name(row.get(ID))
        if row[ID] in seen:
            fail("duplicate_source_record_id")
        seen.add(row[ID])
        canonical(row)  # Includes unknown/nested fields and rejects NaN.
    return sorted(rows, key=lambda row: row[ID])


def read_source_records(root):
    paths = source_record_paths(root)
    rows = []
    signatures = {}
    fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns", "st_mode")
    def signature(path):
        current = path.lstat()
        return tuple(getattr(current, field) for field in fields)
    for path in paths:
        signatures[path] = signature(path)
        rows.extend(row for row, _ in parse_lines(read_bytes(path),
                    expected_shard=path.name if path.parent == Path(root) / TABLE else None))
    # Recheck the file set after reading; a partial/mixed layout is never valid.
    if paths != source_record_paths(root):
        fail("source_layout_changed_while_reading")
    if any(signature(path) != signatures[path] for path in paths):
        fail("source_changed_while_reading")
    return validated_rows(rows)


def write_source_records(root, rows, write_if_changed):
    root = Path(root)
    layout = source_record_layout(root)
    ordered = validated_rows(rows)
    def unchanged(path, values, expected_shard=None):
        if not path.exists():
            return False
        original = validated_rows([row for row, _ in parse_lines(read_bytes(path), expected_shard=expected_shard)])
        return [canonical(row) for row in original] == [canonical(row) for row in values]
    if layout != "sharded":
        if not unchanged(root / LEGACY, ordered):
            write_if_changed(root / LEGACY, "".join(canonical(row) + "\n" for row in ordered))
        return
    groups = {name: [] for name in SHARD_NAMES}
    for row in ordered:
        groups[shard_name(row[ID])].append(row)
    for name in SHARD_NAMES:
        if not unchanged(root / TABLE / name, groups[name], name):
            write_if_changed(root / TABLE / name, "".join(canonical(row) + "\n" for row in groups[name]))
