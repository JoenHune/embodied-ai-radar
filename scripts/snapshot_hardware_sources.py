#!/usr/bin/env python3
"""Stage a source-bound, offline, incremental hardware coverage snapshot.

All source/destination arguments are explicit. The destination MUST be new. This
program never fetches, reparses, instantiates Collector, or changes source
files. It reads a fixed-size prefix of the append-only log exactly once.
If current sources need refreshing, it writes ONLY a manifest and a safe
pending-refresh list, never a misleading partially ready public snapshot.

Example (staging only; this command never updates the published baseline):
  python3 -B scripts/snapshot_hardware_sources.py \
    --cache PRIVATE_CACHE --observations PRIVATE_LOG \
    --published-dir PUBLISHED_SNAPSHOT --dictionary DICTIONARY_JSON --catalog CANONICAL_CATALOG \
    --staging-dir NEW_PRIVATE_DIRECTORY --snapshot-at 2026-09-15T10:00:00Z

Repeatability means identical inputs and snapshot-at produce identical bytes
in separate NEW directories. Existing outputs are never overwritten. A
ready manifest means ready for human review, NOT permission to publish. Omit
snapshot-at to use UTC immediately after reading the fixed log prefix.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from catalog_store import encode
from collect_hardware_sources import PARSER_VERSION, arxiv_identity, page_identity, transport_incomplete
from hardware_census import detect_mentions, dictionary_hash
from refresh_hardware_source_scans import trusted_path
from bs4 import BeautifulSoup

AVAILABLE = {"full_text_available", "partial_text"}
STATUSES = AVAILABLE | {"unavailable", "blocked", "identity_mismatch"}
HASH = re.compile(r"[0-9a-f]{64}\Z")
OID = re.compile(r"hardware-source:[0-9a-f]{32}\Z")
AID = re.compile(r"(?:\d{4}\.\d{4,5}|[A-Za-z][A-Za-z.\-]+/\d{7})\Z")
STAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z\Z")
BOOL_FIELDS = {"transport_complete", "transport_truncated", "manual_reviewed",
               "images_not_inspected", "supplementary_materials_not_inspected"}
INT_FIELDS = {"body_characters", "section_count", "http_status", "transport_returncode", "curl_exit_code"}
DATE_FIELDS = {"observed_at", "fetched_at", "next_retry_at"}
ENUMS = {
    "status": STATUSES,
    "scope": {"body"},
    "text_scope": {"main_document_text_excluding_references_related_work"},
    "processing_basis": {"cached_raw_reparse_no_network", "cached_transport_reclassification_no_network"},
    "transport_verification": {"complete", "incomplete", "legacy_unrecorded", "not_requested"},
}
THRESHOLDS = {"min_body_characters", "min_sections", "max_conversion_error_markers_for_available", "max_response_bytes"}
EXCLUDED = {"abstract", "references", "bibliography", "related work", "prior work", "literature review"}
PUBLIC_FIELDS = (BOOL_FIELDS | INT_FIELDS | DATE_FIELDS | set(ENUMS) |
                 {"work_id", "arxiv_id", "version", "source_url", "effective_url", "raw_sha256", "text_sha256",
                  "parser_version", "parent_observation_id", "observation_id", "excluded_sections", "thresholds", "error"})
SCAN_FIELDS = {"work_id", "source_url", "observed_at", "scope", "status", "dictionary_hash", "content_hash",
               "source_observation_hash", "parser_version", "matches", "review_status"}
MATCH_FIELDS = {"dictionary_id", "term", "start", "end", "section"}
MAX_LOG_BYTES = 256 * 1024 * 1024
MAX_OBJECT_BYTES = 64 * 1024 * 1024


class SnapshotError(ValueError):
    """Only fixed reason codes, never source text or private paths."""


def require(condition, reason):
    if not condition:
        raise SnapshotError(reason)


def sha256(value):
    return hashlib.sha256(value).hexdigest()


def strict_json(value):
    def pairs(items):
        result = {}
        for key, item in items:
            require(key not in result, "duplicate_json_key")
            result[key] = item
        return result
    def constant(_):
        raise SnapshotError("nonfinite_json_number")
    return json.loads(value, object_pairs_hook=pairs, parse_constant=constant)


def timestamp(value):
    require(isinstance(value, str) and STAMP.fullmatch(value), "invalid_timestamp")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise SnapshotError("invalid_timestamp") from None


def utc_snapshot_time():
    """Called only after capturing the fixed source-log prefix."""
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def safe_url(value):
    if value is None:
        return True
    if not isinstance(value, str) or len(value) > 256:
        return False
    try:
        parsed = urlsplit(value)
        return (parsed.scheme == "https" and parsed.netloc in {"arxiv.org", "www.arxiv.org"} and
                not parsed.query and not parsed.fragment and
                bool(re.fullmatch(r"/(?:html|abs|pdf)/(?:\d{4}\.\d{4,5}|[A-Za-z][A-Za-z.\-]+/\d{7})(?:v[1-9]\d*)?(?:\.pdf)?/?", parsed.path)))
    except ValueError:
        return False


def load_canonical_map(catalog):
    """Read only canonical work identities; never infer them from the log."""
    directory = Path(catalog) / "works"
    paths = sorted(directory.glob("*.jsonl")) if directory.is_dir() else [Path(catalog) / "works.jsonl"]
    require(bool(paths), "canonical_works_required")
    canonical_ids = {}
    for path in paths:
        require(path.is_file() and not path.is_symlink(), "canonical_works_required")
        for row in parse_jsonl(path.read_bytes())[0]:
            work_id = row.get("work_id")
            require(isinstance(work_id, str) and work_id not in canonical_ids, "canonical_work_id_missing_or_duplicate")
            identifiers = row.get("identifiers", {})
            require(isinstance(identifiers, dict), "canonical_identifiers_invalid")
            identity = arxiv_identity(identifiers.get("arxiv"))
            canonical_ids[work_id] = identity[0] if identity else None
    return canonical_ids


def validate_work(work_id, canonical_ids):
    """Bind a registered work key, not validate or repair its DOI identifier.

    Some immutable catalog keys predate identifier cleanup. A nonempty doi:
    key with damaged DOI syntax may remain an opaque legacy canonical ID,
    but only with an explicit valid arXiv mapping. Never infer a correction
    from the key, accept an unregistered key, or relax source/hash checks.
    """
    require(isinstance(work_id, str) and work_id in canonical_ids and 0 < len(work_id) <= 256 and
            all(character.isprintable() and not character.isspace() for character in work_id),
            "work_not_in_supported_canonical_mapping")
    aid = canonical_ids[work_id]
    require(aid is None or isinstance(aid, str) and AID.fullmatch(aid), "canonical_arxiv_identity_invalid")
    if work_id.startswith("arxiv:"):
        require(AID.fullmatch(work_id[6:]) and work_id[6:] == aid, "canonical_work_arxiv_identity_mismatch")
    elif re.fullmatch(r"doi:10\.\d{4,9}/[^\s\x00-\x1f]+", work_id):
        pass  # Preserve existing unresolved-source history for shaped DOI keys.
    else:
        require(work_id.startswith("doi:") and len(work_id) > 4,
                "work_not_in_supported_canonical_mapping")
        require(aid is not None, "legacy_canonical_arxiv_identity_required")
    return aid


def validate_source_identity(row, canonical_ids):
    aid = validate_work(row["work_id"], canonical_ids)
    require(row.get("arxiv_id") == aid, "source_canonical_arxiv_identity_mismatch")
    source = arxiv_identity(row.get("source_url"))
    if row.get("source_url") is not None:
        require(source and source[0] == aid, "source_url_canonical_identity_mismatch")
    if row["status"] in AVAILABLE:
        effective = arxiv_identity(row.get("effective_url"))
        require(aid and source and effective and effective[0] == aid, "available_source_effective_identity_mismatch")
        require(all(not identity[1] or identity[1] == row.get("version") for identity in (source, effective)),
                "available_source_version_binding_mismatch")
        require(row.get("version") or row["status"] == "partial_text", "available_source_version_required")


def validate_public(row, canonical_ids):
    require(isinstance(row, dict) and set(row) <= PUBLIC_FIELDS, "public_fields_not_allowlisted")
    for key in ("work_id", "observation_id", "observed_at", "status"):
        require(key in row and row[key] is not None, "required_public_field_missing")
    for key, value in row.items():
        if value is None:
            continue
        valid = True
        if key in BOOL_FIELDS:
            valid = type(value) is bool
        elif key in INT_FIELDS:
            valid = type(value) is int and value >= 0
        elif key in DATE_FIELDS:
            timestamp(value)
        elif key in ENUMS:
            valid = isinstance(value, str) and value in ENUMS[key]
        elif key in {"raw_sha256", "text_sha256"}:
            valid = isinstance(value, str) and bool(HASH.fullmatch(value))
        elif key in {"observation_id", "parent_observation_id"}:
            valid = isinstance(value, str) and bool(OID.fullmatch(value))
        elif key == "work_id":
            validate_work(value, canonical_ids)
        elif key == "arxiv_id":
            valid = isinstance(value, str) and bool(AID.fullmatch(value))
        elif key == "version":
            valid = isinstance(value, str) and bool(re.fullmatch(r"v[1-9]\d*", value))
        elif key in {"source_url", "effective_url"}:
            valid = safe_url(value)
        elif key == "parser_version":
            valid = isinstance(value, str) and bool(re.fullmatch(r"arxiv-html-body-v[1-9]\d*", value))
        elif key == "excluded_sections":
            valid = isinstance(value, list) and all(isinstance(item, str) and item in EXCLUDED for item in value)
        elif key == "thresholds":
            valid = isinstance(value, dict) and set(value) <= THRESHOLDS and all(type(item) is int and item >= 0 for item in value.values())
        elif key == "error":
            valid = isinstance(value, str) and bool(re.fullmatch(r"(?:http_[1-5]\d\d|transport_or_identity_error)", value))
        require(valid, "invalid_public_metadata:" + key)
    validate_source_identity(row, canonical_ids)
    return row


def project(row, canonical_ids):
    require(isinstance(row, dict), "observation_not_object")
    result = {key: value for key, value in row.items() if key in PUBLIC_FIELDS - {"error", "transport_verification"}}
    # Nested values are validated, not copied as arbitrary dictionaries.
    incomplete = transport_incomplete(row) or row.get("transport_verification") == "incomplete"
    result["transport_verification"] = ("incomplete" if incomplete else row.get("transport_verification") or
                                        ("complete" if row.get("transport_complete") is True else "legacy_unrecorded"))
    if row.get("error"):
        code = row.get("http_status")
        result["error"] = f"http_{code}" if type(code) is int and code != 200 else "transport_or_identity_error"
    return validate_public(result, canonical_ids)


def _incomplete_object_prefix(raw):
    """Recognize a syntactically valid unfinished JSON object (not garbage).

    A small syntax-only recognizer distinguishes truncated trailing writes
    from malformed final records. json.loads handles complete records.
    """
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        if exc.reason != "unexpected end of data" or exc.end != len(raw):
            return False
        text = raw[:exc.start].decode("utf-8")
    index = 0
    class Incomplete(Exception):
        pass
    class Invalid(Exception):
        pass
    def ws():
        nonlocal index
        while index < len(text) and text[index] in " \r\n\t":
            index += 1
    def char():
        if index == len(text):
            raise Incomplete
        return text[index]
    def string():
        nonlocal index
        if char() != '"':
            raise Invalid
        index += 1
        while True:
            item = char()
            index += 1
            if item == '"':
                return
            if ord(item) < 32:
                raise Invalid
            if item == "\\":
                item = char()
                index += 1
                if item == "u":
                    for _ in range(4):
                        if char() not in "0123456789abcdefABCDEF":
                            raise Invalid
                        index += 1
                elif item not in '"\\/bfnrt':
                    raise Invalid
    def value(depth=0):
        nonlocal index
        if depth > 100:
            raise Invalid
        ws()
        item = char()
        if item == '"':
            string()
        elif item in "[{":
            mapping, end = item == "{", "}" if item == "{" else "]"
            index += 1
            ws()
            if char() == end:
                index += 1
                return
            while True:
                if mapping:
                    ws()
                    string()
                    ws()
                    if char() != ":":
                        raise Invalid
                    index += 1
                value(depth + 1)
                ws()
                item = char()
                index += 1
                if item == end:
                    return
                if item != ",":
                    raise Invalid
        elif item in "tfn":
            token = {"t": "true", "f": "false", "n": "null"}[item]
            for expected in token:
                if char() != expected:
                    raise Invalid
                index += 1
        else:
            if item == "-":
                index += 1
                item = char()
            if item == "0":
                index += 1
            elif item in "123456789":
                index += 1
                while index < len(text) and text[index] in "0123456789":
                    index += 1
            else:
                raise Invalid
            if index < len(text) and text[index] == ".":
                index += 1
                if char() not in "0123456789":
                    raise Invalid
                while index < len(text) and text[index] in "0123456789":
                    index += 1
            if index < len(text) and text[index] in "eE":
                index += 1
                if char() in "+-":
                    index += 1
                if char() not in "0123456789":
                    raise Invalid
                while index < len(text) and text[index] in "0123456789":
                    index += 1
    try:
        ws()
        if char() != "{":
            return False
        value()
        ws()
        return False
    except Incomplete:
        return True
    except Invalid:
        return False


def parse_jsonl(raw, *, active=False):
    rows, ignored = [], False
    lines = raw.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            row = strict_json(line)
        except (json.JSONDecodeError, UnicodeDecodeError):
            if active and index == len(lines) - 1 and not line.endswith(b"\n") and _incomplete_object_prefix(line):
                ignored = True
                continue
            raise SnapshotError("observation_log_corrupt") from None
        require(isinstance(row, dict), "observation_not_object")
        rows.append(row)
    return rows, ignored


def read_active_log_once(path):
    require(not path.is_symlink(), "observation_log_is_symlink")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_size <= MAX_LOG_BYTES, "observation_log_not_bounded_regular_file")
        raw = os.pread(fd, before.st_size, 0)  # one fixed-size read, no follow-up tail reads
        after = os.fstat(fd)
        current = path.stat()
        require(len(raw) == before.st_size and after.st_size >= before.st_size and
                (current.st_dev, current.st_ino) == (before.st_dev, before.st_ino), "observation_log_replaced_or_truncated")
    finally:
        os.close(fd)
    rows, ignored = parse_jsonl(raw, active=True)
    return rows, {"log_prefix_bytes": len(raw), "log_prefix_sha256": sha256(raw), "incomplete_tail_ignored": ignored}


def read_object(cache, reference):
    require(isinstance(reference, str) and reference, "cached_object_reference_missing")
    require(not cache.is_symlink(), "cache_root_is_symlink")
    try:
        resolved = trusted_path(reference, cache)
        parts = resolved.relative_to(cache.resolve() / "objects").parts
        require(bool(parts), "cached_object_reference_not_file")
        # Every relative traversal is descriptor-bound and O_NOFOLLOW. This
        # also rejects an object/parent symlink swapped after trusted_path().
        directory = os.open(cache.resolve(), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            for part in ("objects", *parts[:-1]):
                next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
                os.close(directory)
                directory = next_fd
            fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        finally:
            os.close(directory)
        try:
            before = os.fstat(fd)
            require(stat.S_ISREG(before.st_mode) and before.st_size <= MAX_OBJECT_BYTES, "cached_object_not_bounded_regular_file")
            raw = os.pread(fd, before.st_size, 0)
            after = os.fstat(fd)
            require(len(raw) == before.st_size and
                    (before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
                    (after.st_size, after.st_mtime_ns, after.st_ctime_ns), "cached_object_changed_during_read")
            return raw
        finally:
            os.close(fd)
    except SnapshotError:
        raise
    except (OSError, ValueError):
        raise SnapshotError("cached_object_missing_external_or_symlink") from None


def verify_cache(cache, row):
    if row.get("cache_ref") or row.get("raw_sha256") or row["status"] in AVAILABLE:
        raw = read_object(cache, row.get("cache_ref"))
        require(sha256(raw) == row.get("raw_sha256"), "cached_raw_hash_mismatch")
    if row["status"] not in AVAILABLE:
        return []
    # Identity-only validation of the already cached raw bytes. Do NOT call
    # assess_html/extract_blocks or regenerate the parser's body cache.
    valid, version, _, _ = page_identity(BeautifulSoup(raw, "html.parser"), row["effective_url"],
                                         row["arxiv_id"], row.get("version"))
    require(valid and version == row.get("version"), "cached_page_identity_validation_failed")
    try:
        blocks = strict_json(read_object(cache, row.get("blocks_ref")))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise SnapshotError("cached_blocks_invalid_json") from None
    require(isinstance(blocks, list) and bool(blocks) and all(isinstance(block, dict) and isinstance(block.get("text"), str) and
                                                           isinstance(block.get("section_id"), str) and
                                                           re.fullmatch(r"[A-Za-z0-9_.:-]{1,256}", block["section_id"])
                                                           for block in blocks), "cached_blocks_invalid_schema")
    body = "\n\n".join(block["text"] for block in blocks).encode()
    require(sha256(body) == row.get("text_sha256"), "cached_body_hash_mismatch")
    stored_body = read_object(cache, row.get("body_cache_ref"))
    require(sha256(stored_body) == row.get("text_sha256") and stored_body == body, "cached_body_file_hash_mismatch")
    characters = sum(len(block["text"]) for block in blocks)
    sections = sum(block["section_id"] != "body" for block in blocks)
    require(row.get("body_characters") == characters and row.get("section_count") == sections,
            "cached_body_metadata_count_mismatch")
    if row["status"] == "full_text_available":
        thresholds = row.get("thresholds")
        require(isinstance(thresholds, dict) and {"min_body_characters", "min_sections"} <= set(thresholds),
                "cached_available_thresholds_missing")
        require(characters >= thresholds["min_body_characters"] and sections >= thresholds["min_sections"] and
                row.get("structured_document", True) is True and
                ("conversion_error_markers" not in row or type(row["conversion_error_markers"]) is int and
                 0 <= row["conversion_error_markers"] <= thresholds.get("max_conversion_error_markers_for_available", 4)),
                "cached_available_thresholds_inconsistent")
    return blocks


def scan_key(row):
    return tuple(row[key] for key in ("work_id", "source_url", "dictionary_hash", "content_hash"))


def validate_scan(row, canonical_ids):
    require(isinstance(row, dict) and set(row) <= SCAN_FIELDS and
            {"work_id", "source_url", "observed_at", "scope", "status", "dictionary_hash", "content_hash"} <= set(row),
            "scan_history_schema_invalid")
    aid = validate_work(row["work_id"], canonical_ids)
    require(safe_url(row["source_url"]), "scan_source_url_invalid")
    identity = arxiv_identity(row["source_url"])
    require(identity and identity[0] == aid, "scan_canonical_source_identity_mismatch")
    timestamp(row["observed_at"])
    require(row["scope"] == "body" and row["status"] in {"scanned", "failed"}, "scan_scope_or_status_invalid")
    require(row.get("review_status", "unverified_machine_mentions") == "unverified_machine_mentions", "scan_review_status_invalid")
    for key in ("dictionary_hash", "content_hash", "source_observation_hash"):
        require(key not in row or isinstance(row[key], str) and HASH.fullmatch(row[key]), "scan_hash_invalid")
    require("parser_version" not in row or isinstance(row["parser_version"], str) and
            re.fullmatch(r"arxiv-html-body-v[1-9]\d*", row["parser_version"]), "scan_parser_invalid")
    require(isinstance(row.get("matches", []), list) and ("matches" in row or row["status"] == "failed"), "scan_matches_invalid")
    for match in row.get("matches", []):
        require(isinstance(match, dict) and set(match) <= MATCH_FIELDS and
                {"dictionary_id", "term", "start", "end"} <= set(match), "scan_match_fields_not_allowlisted")
        require(all(isinstance(match[key], str) and 0 < len(match[key]) <= 512 for key in ("dictionary_id", "term")) and
                ("section" not in match or isinstance(match["section"], str) and len(match["section"]) <= 512) and
                type(match["start"]) is int and type(match["end"]) is int and 0 <= match["start"] < match["end"], "scan_match_invalid")
    return row


def build_scan(row, blocks, dictionary, stamp, canonical_ids):
    matches, offset = [], 0
    for block in blocks:
        for match in detect_mentions(block["text"], dictionary):
            # A finite dictionary hit retains literal/span semantics; neither
            # its surrounding body text nor the long section title is copied.
            matches.append({"dictionary_id": match["dictionary_id"], "term": match["term"],
                            "section": block["section_id"], "start": offset + match["start"], "end": offset + match["end"]})
        offset += len(block["text"]) + 2
    return validate_scan({"work_id": row["work_id"], "source_url": row["source_url"], "observed_at": stamp,
                          "scope": "body", "status": "scanned", "dictionary_hash": dictionary_hash(dictionary),
                          "content_hash": row["text_sha256"], "source_observation_hash": row["raw_sha256"],
                          "parser_version": row["parser_version"], "matches": matches, "review_status": "unverified_machine_mentions"}, canonical_ids)


def stage_snapshot(*, cache, observations, published_dir, dictionary, staging_dir, canonical_ids, snapshot_at=None):
    """Read-only incremental validation; write only a brand-new staging dir.

    Published latest observations with existing current body/dictionary scan
    history reuse that history after metadata binding checks, without opening
    or revalidating old cache objects. New observation IDs always verify their
    own cache, including when their body/dictionary key is already in history.
    """
    cache, observations, published_dir, staging_dir = map(Path, (cache, observations, published_dir, staging_dir))
    explicit_time = snapshot_at is not None
    scan_time = timestamp(snapshot_at) if explicit_time else None
    require(staging_dir.is_absolute(), "staging_directory_must_be_explicit_absolute_path")
    require(not staging_dir.exists() and not staging_dir.is_symlink(), "staging_directory_must_be_new")
    require(staging_dir.parent.is_dir() and not staging_dir.parent.is_symlink(), "staging_parent_must_exist_and_not_be_symlink")
    stage = staging_dir.resolve()
    for protected in (cache.resolve(), published_dir.resolve(), observations.resolve(), ROOT / "data", ROOT / "docs", ROOT / "scripts"):
        require(not stage.is_relative_to(protected) and not protected.is_relative_to(stage), "staging_overlaps_protected_source")
    if stage.is_relative_to(ROOT):
        require(stage.is_relative_to(ROOT / ".research"), "repository_staging_must_be_private")
    # Fully validate the dictionary even when there are no bodies to scan.
    detect_mentions("", dictionary)
    current_dictionary_hash = dictionary_hash(dictionary)
    baseline_path = published_dir / "source-observations.jsonl"
    require(baseline_path.is_file() and not baseline_path.is_symlink(), "published_snapshot_required")
    published_raw = baseline_path.read_bytes()
    published, _ = parse_jsonl(published_raw)
    history_path = published_dir / "source-scans.jsonl"
    require(not history_path.is_symlink(), "published_scan_history_is_symlink")
    history_raw = history_path.read_bytes() if history_path.exists() else b""
    history, _ = parse_jsonl(history_raw)
    known = {}
    for row in published:
        validate_public(row, canonical_ids)
        oid = row["observation_id"]
        require(oid not in known, "published_observation_id_duplicate")
        known[oid] = row
    rows, log_info = read_active_log_once(observations)
    if not explicit_time:
        snapshot_at = utc_snapshot_time()
        scan_time = timestamp(snapshot_at)
    indexed, ordered = {}, []
    for row in rows:
        projected = project(row, canonical_ids)
        require(all(row.get(key) is None or timestamp(row[key]) <= scan_time for key in ("observed_at", "fetched_at")),
                "snapshot_time_precedes_source_observation")
        oid = row["observation_id"]
        if oid in indexed:
            require(indexed[oid] == row, "private_observation_id_conflict")
        else:
            indexed[oid] = row
            ordered.append(row)
        if oid in known:
            require(all(projected.get(key) == value for key, value in known[oid].items()), "published_private_binding_mismatch")
    require(set(known) <= set(indexed), "published_observation_missing_from_log")
    latest = {}
    for row in ordered:
        key = row["work_id"], row.get("source_url")
        if key not in latest or timestamp(row["observed_at"]) >= timestamp(latest[key]["observed_at"]):
            latest[key] = row
    # Two prebuilt indices cover legacy scans without a raw hash and modern
    # scans with one. History validation is O(sources + scans), not O(N*M).
    published_body_bindings = {(row["work_id"], row.get("source_url"), row.get("text_sha256")) for row in published}
    published_raw_bindings = {(row["work_id"], row.get("source_url"), row.get("text_sha256"), row.get("raw_sha256"))
                              for row in published}
    scans, scan_events, scan_keys = [], {}, set()
    for row in history:
        validate_scan(row, canonical_ids)
        require(timestamp(row["observed_at"]) <= scan_time, "snapshot_time_precedes_scan_history")
        key = scan_key(row)
        event_key = (*key, row["observed_at"])
        require(event_key not in scan_events or scan_events[event_key] == row, "scan_history_key_conflict")
        binding = (row["work_id"], row["source_url"], row["content_hash"])
        require(((*binding, row["source_observation_hash"]) in published_raw_bindings
                 if "source_observation_hash" in row else binding in published_body_bindings),
                "scan_history_source_binding_missing")
        if event_key not in scan_events:
            scans.append(row)
            scan_events[event_key] = row
        scan_keys.add(key)
    pending, candidates = [], {}
    cache_verified = cache_verification_attempted = reused = new_scans_added = 0
    latest_ids = {row["observation_id"] for row in latest.values()}
    for row in ordered:
        reasons = []
        is_latest = row["observation_id"] in latest_ids
        if not row.get("source_url"):
            # The collector can record unresolved identity attempts, but the
            # downstream census requires a genuine source URL. Do not invent
            # one or drop the observation to make a snapshot appear ready.
            reasons.append("source_url_missing_requires_schema_policy")
        if is_latest and row["status"] in AVAILABLE:
            if row.get("parser_version") != PARSER_VERSION:
                reasons.append("parser_refresh_required")
            if row["status"] == "full_text_available" and (transport_incomplete(row) or row.get("transport_verification") == "incomplete"):
                reasons.append("transport_reclassification_required")
        current_scan_key = (row["work_id"], row.get("source_url"), current_dictionary_hash, row.get("text_sha256"))
        reuse_history = (row["observation_id"] in known and is_latest and row["status"] in AVAILABLE and
                         current_scan_key in scan_keys)
        if not reasons and reuse_history:
            # An existing failed event counts as history too. Do not reopen
            # old cache or manufacture a new success that hides its failure.
            reused += 1
        elif not reasons and (row["observation_id"] not in known or is_latest and row["status"] in AVAILABLE):
            try:
                has_cache = bool(row.get("cache_ref") or row.get("raw_sha256") or row["status"] in AVAILABLE)
                cache_verification_attempted += int(has_cache)
                blocks = verify_cache(cache, row)
                cache_verified += int(has_cache)
                if is_latest and row["status"] in AVAILABLE:
                    candidates[row["observation_id"]] = build_scan(row, blocks, dictionary, snapshot_at, canonical_ids)
                del blocks  # retain metadata scans, not a corpus of private bodies
            except SnapshotError as exc:
                reasons.append(str(exc))
        if reasons:
            pending.append({"observation_id": row["observation_id"], "work_id": row["work_id"],
                            "source_url": row.get("source_url"), "reasons": reasons})
    public = [*published, *(project(row, canonical_ids) for row in ordered if row["observation_id"] not in known)]
    if not pending:
        for row in latest.values():
            if row["observation_id"] in candidates:
                candidate = candidates[row["observation_id"]]
                if scan_key(candidate) not in scan_keys:
                    scans.append(candidate)
                    scan_keys.add(scan_key(candidate))
                    new_scans_added += 1
    payloads = {"pending-refresh.jsonl": "".join(encode(row) + "\n" for row in pending)}
    if not pending:
        payloads["source-observations.jsonl"] = "".join(encode(row) + "\n" for row in public)
        payloads["source-scans.jsonl"] = "".join(encode(row) + "\n" for row in scans)
    manifest = {"schema_version": "1", "kind": "hardware_source_snapshot", "prototype_only": False, "deployment_authorized": False,
                "ready_for_review": not pending, "snapshot_at": snapshot_at,
                "snapshot_time_basis": "explicit" if explicit_time else "utc_after_fixed_log_prefix_read", **log_info,
                "dictionary_hash": current_dictionary_hash, "parser_version": PARSER_VERSION,
                "canonical_mapping_sha256": sha256(encode(canonical_ids).encode()),
                "published_observations_sha256": sha256(published_raw), "published_scans_sha256": sha256(history_raw),
                "published_observations_retained": len(published), "observations_after_validation": len(public),
                "new_observations": len(public) - len(published), "pending_refresh_count": len(pending),
                "scan_history_input_records": len(history), "scan_history_retained": len(scan_events),
                "cache_verification_attempted": cache_verification_attempted, "cache_verified": cache_verified,
                "new_scanned": len(candidates), "new_scans_added": new_scans_added, "reused": reused,
                "total_scans": len(scans) if not pending else None,
                "source_snapshot_modified": False, "private_cache_modified": False, "network_requests": 0,
                "verification_scope": {
                    "all_observations": "canonical_identity_and_published_log_metadata_binding",
                    "cache_verified": "new_or_current_dictionary_unscanned_sources_only;raw_hash_and_available_body_hash_page_identity_counts",
                    "new_scanned": "newly_executed_latest_source_dictionary_scans;may_not_be_added_when_history_key_exists_or_batch_is_pending",
                    "reused": "published_latest_source_with_current_scan_key;history_retained_without_opening_or_revalidating_old_cache",
                    "failed_history": "retained_without_replacement_by_new_success_for_same_source_body_dictionary_key",
                    "not_completed_reading": True,
                },
                "output_sha256": {name: sha256(value.encode()) for name, value in payloads.items()}}
    # Avoid basing a new batch on a baseline that changed while validation ran.
    require(baseline_path.read_bytes() == published_raw and
            (history_path.read_bytes() if history_path.exists() else b"") == history_raw, "published_baseline_changed_during_snapshot")
    staging_dir.mkdir(mode=0o700)  # exist_ok=False: never reuse someone else's output
    for name, payload in payloads.items():
        with (staging_dir / name).open("x", encoding="utf-8") as handle:
            handle.write(payload)
    # Manifest LAST is the commit marker; missing manifest means interrupted.
    with (staging_dir / "snapshot-manifest.json").open("x", encoding="utf-8") as handle:
        handle.write(encode(manifest) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("cache", "observations", "published-dir", "dictionary", "staging-dir", "catalog"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--snapshot-at", help="Explicit reproducible batch timestamp; otherwise use UTC after the fixed log-prefix read")
    args = parser.parse_args()
    try:
        result = stage_snapshot(cache=args.cache, observations=args.observations, published_dir=args.published_dir,
                                dictionary=strict_json(args.dictionary.read_bytes()), staging_dir=args.staging_dir,
                                snapshot_at=args.snapshot_at, canonical_ids=load_canonical_map(args.catalog))
    except SnapshotError as exc:
        print(encode({"kind": "hardware_source_snapshot", "error": str(exc)}))
        return 2
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        print(encode({"kind": "hardware_source_snapshot", "error": "input_or_staging_io_failure"}))
        return 2
    print(encode(result))
    return 0 if result["ready_for_review"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
