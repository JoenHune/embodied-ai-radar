#!/usr/bin/env python3
"""Validate, then explicitly promote a staged public hardware-source snapshot.

Default is read-only dry-run; --apply is the only write authorization. Supply
explicit absolute paths for stage-dir, target-dir, dictionary, and catalog.
Only source-observations.jsonl and source-scans.jsonl may change in target-dir.
No collector, raw HTML, body cache, acquisition log, or collector state is read.

Apply saves a recoverable private backup inside stage-dir before replacing
each public file with an atomic rename. The TWO replacements are NOT one
atomic transaction and are NOT power-loss safe. Ordinary replacement failures
trigger rollback; a rollback failure is reported explicitly with the backup
left intact. Run against a quiescent target: concurrent external writers are
detected at checkpoints, not coordinated by a shared global lock.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import uuid
from pathlib import Path

sys.dont_write_bytecode = True
from catalog_store import encode
from hardware_census import _compile_dictionary, detect_mentions, dictionary_hash
from snapshot_hardware_sources import (
    AVAILABLE, HASH, PARSER_VERSION, SnapshotError, arxiv_identity,
    parse_jsonl, scan_key, strict_json, timestamp, validate_public, validate_scan,
)

TARGET_NAMES = ("source-observations.jsonl", "source-scans.jsonl")
OUTPUT_NAMES = {*TARGET_NAMES, "pending-refresh.jsonl"}
MANIFEST_NAME = "snapshot-manifest.json"
BACKUP_ROOT = ".promotion-backups"
MAX_BYTES = 256 * 1024 * 1024


class PromotionError(SnapshotError):
    """Fixed reason codes only, never arbitrary input or private file paths."""


def require(condition, reason):
    if not condition:
        raise PromotionError(reason)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def _absolute(path):
    path = Path(path)
    require(path.is_absolute() and ".." not in path.parts, "explicit_absolute_path_required")
    return path


def _open_directory(path):
    """Bind every component with O_NOFOLLOW, including ancestor directories."""
    path = _absolute(path)
    descriptor = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in path.parts[1:]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except Exception:
        os.close(descriptor)
        raise PromotionError("input_directory_missing_unsafe_or_symlink") from None


def _directory_unchanged(path, descriptor):
    current = _open_directory(path)
    try:
        before, after = os.fstat(descriptor), os.fstat(current)
        require((before.st_dev, before.st_ino) == (after.st_dev, after.st_ino), "input_directory_replaced")
    finally:
        os.close(current)


def _read_file(directory, name, *, optional=False):
    """Read a bounded regular file through its already pinned parent."""
    try:
        descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    except FileNotFoundError:
        if optional:
            return None, None
        raise PromotionError("required_input_file_missing") from None
    except OSError:
        raise PromotionError("input_file_unsafe_or_symlink") from None
    try:
        before = os.fstat(descriptor)
        require(stat.S_ISREG(before.st_mode) and before.st_size <= MAX_BYTES,
                "input_not_bounded_regular_file")
        chunks, remaining = [], before.st_size
        while remaining:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            require(bool(chunk), "input_changed_during_read")
            chunks.append(chunk)
            remaining -= len(chunk)
        after = os.fstat(descriptor)
        require((before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
                (after.st_size, after.st_mtime_ns, after.st_ctime_ns), "input_changed_during_read")
        return b"".join(chunks), stat.S_IMODE(before.st_mode)
    finally:
        os.close(descriptor)


def _read_path(path):
    path = _absolute(path)
    descriptor = _open_directory(path.parent)
    try:
        return _read_file(descriptor, path.name)[0]
    finally:
        os.close(descriptor)


def _canonical_mapping(catalog):
    """Same canonical identity projection as staging, with no-follow reads."""
    descriptor = _open_directory(catalog)
    works = None
    try:
        try:
            metadata = os.stat("works", dir_fd=descriptor, follow_symlinks=False)
        except FileNotFoundError:
            metadata = None
        if metadata is not None:
            require(stat.S_ISDIR(metadata.st_mode), "canonical_works_unsafe_or_symlink")
            works = os.open("works", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            names = sorted(name for name in os.listdir(works) if name.endswith(".jsonl"))
        else:
            works, names = os.dup(descriptor), ["works.jsonl"]
        require(bool(names), "canonical_works_required")
        canonical = {}
        for name in names:
            for row in parse_jsonl(_read_file(works, name)[0])[0]:
                work_id = row.get("work_id")
                require(isinstance(work_id, str) and work_id not in canonical,
                        "canonical_work_id_missing_or_duplicate")
                identifiers = row.get("identifiers", {})
                require(isinstance(identifiers, dict), "canonical_identifiers_invalid")
                identity = arxiv_identity(identifiers.get("arxiv"))
                canonical[work_id] = identity[0] if identity else None
        return canonical
    finally:
        if works is not None:
            os.close(works)
        os.close(descriptor)


def _manifest(raw):
    result = strict_json(raw)
    require(isinstance(result, dict), "snapshot_manifest_not_object")
    require(result.get("schema_version") == "1" and result.get("kind") == "hardware_source_snapshot" and
            result.get("prototype_only") is False, "unsupported_snapshot_manifest")
    require(result.get("ready_for_review") is True and type(result.get("pending_refresh_count")) is int and
            result["pending_refresh_count"] == 0, "snapshot_has_pending_refresh")
    hashes = result.get("output_sha256")
    require(isinstance(hashes, dict) and set(hashes) == OUTPUT_NAMES, "snapshot_output_set_invalid")
    for value in [*hashes.values(), result.get("published_observations_sha256"),
                  result.get("published_scans_sha256"), result.get("dictionary_hash"),
                  result.get("canonical_mapping_sha256")]:
        require(isinstance(value, str) and HASH.fullmatch(value), "snapshot_hash_invalid")
    require(result.get("parser_version") == PARSER_VERSION, "snapshot_parser_version_mismatch")
    timestamp(result.get("snapshot_at"))
    # deployment_authorized:false is intentional. Only this call's apply flag
    # authorizes mutation; a manifest cannot authorize itself.
    return result


def _observations(rows, canonical, at):
    indexed = {}
    for row in rows:
        validate_public(row, canonical)
        oid = row["observation_id"]
        require(oid not in indexed, "observation_id_duplicate")
        require(all(row.get(key) is None or timestamp(row[key]) <= at for key in ("observed_at", "fetched_at")),
                "snapshot_time_precedes_source_observation")
        require(row.get("source_url") is not None, "source_url_required")
        indexed[oid] = row
    for oid, row in indexed.items():
        parent_id = row.get("parent_observation_id")
        if parent_id is None:
            continue
        parent = indexed.get(parent_id)
        require(parent is not None and parent_id != oid and
                (parent["work_id"], parent.get("source_url")) == (row["work_id"], row.get("source_url")) and
                timestamp(parent["observed_at"]) <= timestamp(row["observed_at"]),
                "observation_parent_binding_invalid")
    # Iterative traversal is bounded and also handles same-timestamp cycles.
    completed = set()
    for oid in indexed:
        chain = set()
        while oid is not None and oid not in completed:
            require(oid not in chain, "observation_parent_cycle")
            chain.add(oid)
            oid = indexed[oid].get("parent_observation_id")
        completed.update(chain)
    return indexed


def _scan_events(rows, canonical, observations, at, *, allow_exact_duplicates=False):
    # An old scan may be reused by a newer observation of the same body, but
    # cannot predate every observation that fully matches its own provenance.
    bodies, raws = {}, {}
    for row in observations:
        binding = row["work_id"], row.get("source_url"), row.get("text_sha256")
        observed = timestamp(row["observed_at"])
        for index, key in ((bodies, binding), (raws, (*binding, row.get("raw_sha256")))):
            index[key] = min(index.get(key, observed), observed)
    events, unique = {}, []
    for row in rows:
        validate_scan(row, canonical)
        require(timestamp(row["observed_at"]) <= at, "snapshot_time_precedes_scan_history")
        key = (*scan_key(row), row["observed_at"])
        if key in events:
            require(allow_exact_duplicates and events[key] == row, "scan_event_duplicate_or_conflict")
            continue
        binding = row["work_id"], row["source_url"], row["content_hash"]
        earliest = (raws.get((*binding, row["source_observation_hash"]))
                    if "source_observation_hash" in row else bodies.get(binding))
        require(earliest is not None, "scan_source_binding_missing")
        require(timestamp(row["observed_at"]) >= earliest, "scan_time_precedes_bound_source_observation")
        events[key] = row
        unique.append(row)
    return unique


def _available_hashes(row):
    if row["status"] in AVAILABLE:
        for key in ("raw_sha256", "text_sha256"):
            require(isinstance(row.get(key), str) and HASH.fullmatch(row[key]), "available_source_hash_required:" + key)


def _ready_sources(observations, scans, current_dictionary_hash):
    latest = {}
    for row in observations:
        key = row["work_id"], row.get("source_url")
        if key not in latest or timestamp(row["observed_at"]) >= timestamp(latest[key]["observed_at"]):
            latest[key] = row
    scan_keys = {scan_key(row) for row in scans}
    for row in latest.values():
        if row["status"] not in AVAILABLE:
            continue
        _available_hashes(row)
        require(row.get("parser_version") == PARSER_VERSION, "latest_source_parser_refresh_required")
        require(row["status"] != "full_text_available" or
                (row.get("transport_complete") is not False and row.get("transport_truncated") is not True and
                 row.get("transport_verification") != "incomplete" and
                 row.get("transport_returncode", 0) in (None, 0) and row.get("curl_exit_code", 0) in (None, 0)),
                "latest_source_transport_refresh_required")
        require((row["work_id"], row["source_url"], current_dictionary_hash, row.get("text_sha256")) in scan_keys,
                "latest_source_current_dictionary_scan_missing")


def _verify_history(manifest, old_rows, old_scans, rows, scans, dictionary):
    require(rows[:len(old_rows)] == old_rows, "published_observation_history_not_preserved")
    require(scans[:len(old_scans)] == old_scans, "published_scan_history_not_preserved")
    for row in rows[len(old_rows):]:
        _available_hashes(row)
    for key, count in (("published_observations_retained", len(old_rows)),
                       ("observations_after_validation", len(rows)), ("new_observations", len(rows) - len(old_rows)),
                       ("scan_history_retained", len(old_scans)), ("total_scans", len(scans)),
                       ("new_scans_added", len(scans) - len(old_scans))):
        require(type(manifest.get(key)) is int and manifest[key] == count, "snapshot_count_mismatch:" + key)
    historical_keys = {scan_key(row) for row in old_scans}
    literal_patterns = {}
    for did, pattern, *_ in _compile_dictionary(encode(dictionary)):
        literal_patterns.setdefault(did, []).append(pattern)
    for row in scans[len(old_scans):]:
        require(row["dictionary_hash"] == manifest["dictionary_hash"] and row["status"] == "scanned" and
                row.get("parser_version") == PARSER_VERSION and row.get("source_observation_hash") is not None,
                "new_scan_not_current_verified_machine_scan")
        require(scan_key(row) not in historical_keys, "new_scan_replaces_existing_history_key")
        historical_keys.add(scan_key(row))
        for match in row["matches"]:
            require(match["end"] - match["start"] == len(match["term"]), "new_scan_match_span_invalid")
            require(isinstance(match.get("section"), str) and
                    re.fullmatch(r"[A-Za-z0-9_.:-]{1,256}", match["section"]), "new_scan_section_id_invalid")
            # Context-gated aliases (e.g. bare G1) legitimately retain only the
            # hit, not their private surrounding body. Staging verified context;
            # promotion can verify only dictionary identity and finite literal.
            require(any(pattern.fullmatch(match["term"]) for pattern in literal_patterns.get(match["dictionary_id"], [])),
                    "new_scan_dictionary_match_invalid")


def _target_state(descriptor):
    return {name: _read_file(descriptor, name, optional=name == TARGET_NAMES[1]) for name in TARGET_NAMES}


def _assert_target(descriptor, expected):
    require(_target_state(descriptor) == expected, "target_baseline_changed_during_promotion")


def _write_new(descriptor, name, raw, mode):
    handle = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode, dir_fd=descriptor)
    try:
        os.fchmod(handle, mode)
        with os.fdopen(handle, "wb", closefd=False) as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(handle)


def _backup(stage_fd, snapshot_id, state):
    """Save only two baseline files plus a small private recovery manifest."""
    try:
        os.mkdir(BACKUP_ROOT, mode=0o700, dir_fd=stage_fd)
    except FileExistsError:
        pass
    parent = os.open(BACKUP_ROOT, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=stage_fd)
    backup = None
    try:
        require(stat.S_IMODE(os.fstat(parent).st_mode) & 0o077 == 0, "backup_directory_not_private")
        try:
            os.mkdir(snapshot_id, mode=0o700, dir_fd=parent)
        except FileExistsError:
            pass
        backup = os.open(snapshot_id, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
        require(stat.S_IMODE(os.fstat(backup).st_mode) & 0o077 == 0, "backup_directory_not_private")
        metadata = {"schema_version": "1", "kind": "hardware_snapshot_promotion_backup",
                    "snapshot_manifest_sha256": snapshot_id,
                    "files": {name: {"existed": raw is not None, "sha256": sha256(raw or b""), "mode": mode}
                              for name, (raw, mode) in state.items()},
                    "recovery": "Restore the two saved files to the explicit original target; remove source-scans.jsonl if existed=false.",
                    "cross_file_atomic": False, "power_loss_safe": False}
        expected = {name: raw for name, (raw, _) in state.items() if raw is not None}
        expected["backup-manifest.json"] = (encode(metadata) + "\n").encode()
        require(set(os.listdir(backup)) <= set(expected), "backup_contains_unexpected_files")
        for name, raw in expected.items():
            existing, _ = _read_file(backup, name, optional=True)
            if existing is None:
                _write_new(backup, name, raw, 0o600)
            else:
                require(existing == raw, "existing_backup_mismatch")
        return BACKUP_ROOT + "/" + snapshot_id
    finally:
        if backup is not None:
            os.close(backup)
        os.close(parent)


def _atomic_replace(directory, name, raw, mode):
    temporary = "." + name + ".promotion-" + uuid.uuid4().hex
    try:
        _write_new(directory, temporary, raw, mode)
        os.replace(temporary, name, src_dir_fd=directory, dst_dir_fd=directory)
    finally:
        try:
            os.unlink(temporary, dir_fd=directory)
        except FileNotFoundError:
            pass


def promote_snapshot(*, stage_dir, target_dir, dictionary, catalog, apply=False):
    """Return a safe summary; neither dry-run nor already-applied writes files."""
    stage_dir, target_dir, dictionary, catalog = map(_absolute, (stage_dir, target_dir, dictionary, catalog))
    require(not stage_dir.is_relative_to(target_dir) and not target_dir.is_relative_to(stage_dir),
            "stage_target_overlap")
    # Backups cannot cause the explicit read-only inputs to be overwritten.
    for source in (dictionary, catalog):
        require(not source.is_relative_to(stage_dir / BACKUP_ROOT), "backup_overlaps_readonly_input")
    stage_fd = _open_directory(stage_dir)
    target_fd = None
    try:
        target_fd = _open_directory(target_dir)
        manifest_raw = _read_file(stage_fd, MANIFEST_NAME)[0]
        manifest = _manifest(manifest_raw)
        outputs = {name: _read_file(stage_fd, name)[0] for name in sorted(OUTPUT_NAMES)}
        require(all(sha256(raw) == manifest["output_sha256"][name] for name, raw in outputs.items()),
                "staged_output_hash_mismatch")
        require(not parse_jsonl(outputs["pending-refresh.jsonl"])[0], "snapshot_has_pending_refresh")
        dictionary_raw = _read_path(dictionary)
        vocabulary = strict_json(dictionary_raw)
        detect_mentions("", vocabulary)
        require(dictionary_hash(vocabulary) == manifest["dictionary_hash"], "dictionary_hash_mismatch")
        canonical = _canonical_mapping(catalog)
        require(sha256(encode(canonical).encode()) == manifest["canonical_mapping_sha256"],
                "canonical_mapping_hash_mismatch")
        at = timestamp(manifest["snapshot_at"])
        rows = parse_jsonl(outputs[TARGET_NAMES[0]])[0]
        scans = parse_jsonl(outputs[TARGET_NAMES[1]])[0]
        _observations(rows, canonical, at)
        _scan_events(scans, canonical, rows, at)
        _ready_sources(rows, scans, manifest["dictionary_hash"])
        state = _target_state(target_fd)
        already_applied = all(state[name][0] == outputs[name] for name in TARGET_NAMES)
        if not already_applied:
            require(sha256(state[TARGET_NAMES[0]][0]) == manifest["published_observations_sha256"] and
                    sha256(state[TARGET_NAMES[1]][0] or b"") == manifest["published_scans_sha256"],
                    "target_baseline_hash_mismatch")
            old_rows = parse_jsonl(state[TARGET_NAMES[0]][0])[0]
            old_scan_input = parse_jsonl(state[TARGET_NAMES[1]][0] or b"")[0]
            _observations(old_rows, canonical, at)
            old_scans = _scan_events(old_scan_input, canonical, old_rows, at, allow_exact_duplicates=True)
            require(type(manifest.get("scan_history_input_records")) is int and
                    manifest["scan_history_input_records"] == len(old_scan_input),
                    "snapshot_count_mismatch:scan_history_input_records")
            _verify_history(manifest, old_rows, old_scans, rows, scans, vocabulary)
        summary = {"schema_version": "1", "kind": "hardware_snapshot_promotion", "applied": False,
                   "dry_run": not apply, "already_applied": already_applied, "validated": True,
                   "snapshot_manifest_sha256": sha256(manifest_raw), "observations": len(rows), "scans": len(scans),
                   "target_files": list(TARGET_NAMES), "cross_file_atomic": False, "power_loss_safe": False,
                   "private_source_reverified": False, "network_requests": 0,
                   "dictionary_match_verification": "finite_alias_literal_only;context_verified_by_staging_not_reverified"}
        if not apply or already_applied:
            return summary
        _directory_unchanged(stage_dir, stage_fd)
        _directory_unchanged(target_dir, target_fd)
        require(_read_file(stage_fd, MANIFEST_NAME)[0] == manifest_raw and
                all(_read_file(stage_fd, name)[0] == raw for name, raw in outputs.items()),
                "staged_inputs_changed_during_promotion")
        require(_read_path(dictionary) == dictionary_raw and _canonical_mapping(catalog) == canonical,
                "readonly_inputs_changed_during_promotion")
        _assert_target(target_fd, state)
        summary["backup_relative_path"] = _backup(stage_fd, summary["snapshot_manifest_sha256"], state)
        # Backup must finish successfully before either target file changes.
        _directory_unchanged(target_dir, target_fd)
        _assert_target(target_fd, state)
        changed, attempted = [], []
        try:
            for name in TARGET_NAMES:
                expected = dict(state)
                expected.update({done: (outputs[done], state[done][1] if state[done][1] is not None else 0o644)
                                 for done in changed})
                _assert_target(target_fd, expected)
                # Register before calling: a wrapper or an ordinary I/O error
                # can raise after the rename has already succeeded.
                attempted.append(name)
                _atomic_replace(target_fd, name, outputs[name], state[name][1] if state[name][1] is not None else 0o644)
                changed.append(name)
            require(all(_read_file(target_fd, name)[0] == outputs[name] for name in TARGET_NAMES),
                    "target_postwrite_verification_failed")
        except Exception:
            rollback_failed = False
            for name in reversed(attempted):
                try:
                    original, mode = state[name]
                    current, _ = _read_file(target_fd, name, optional=True)
                    if current == original:
                        continue  # An attempted replacement did not take effect.
                    # Do not overwrite a concurrent writer while rolling back.
                    require(current == outputs[name], "rollback_target_changed")
                    if original is None:
                        os.unlink(name, dir_fd=target_fd)
                    else:
                        _atomic_replace(target_fd, name, original, mode)
                except Exception:
                    rollback_failed = True
            if rollback_failed:
                raise PromotionError("promotion_failed_rollback_incomplete_restore_private_backup") from None
            raise PromotionError("promotion_failed_target_changes_rolled_back_private_backup_retained") from None
        summary["applied"] = True
        return summary
    finally:
        if target_fd is not None:
            os.close(target_fd)
        os.close(stage_fd)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("stage-dir", "target-dir", "dictionary", "catalog"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--apply", action="store_true", help="Explicitly replace only the two validated public snapshot files")
    args = parser.parse_args(argv)
    try:
        result = promote_snapshot(stage_dir=args.stage_dir, target_dir=args.target_dir,
                                  dictionary=args.dictionary, catalog=args.catalog, apply=args.apply)
    except SnapshotError as exc:
        print(encode({"applied": False, "error": str(exc)}))
        return 2
    except (OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
        print(encode({"applied": False, "error": "input_or_promotion_io_failure"}))
        return 2
    print(encode(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
