"""Compact, read-only publishing of the whole-catalog hardware census.

Metadata-only discovery, fetched body text, dictionary scans, and verified
relationships remain separate. Public exports contain no paper excerpts or
local cache paths. The full census is written once, as a compressed download;
API shards and SQLite retain small status projections rather than copies of
its large JSON rows. No network, canonical writes, or implicit source reads.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import re
import tempfile
from collections import defaultdict
from pathlib import Path

from catalog_store import encode, fingerprint, write_if_changed
from hardware_census import FAILED_STATUSES, _counts, build_census, detect_mentions


PRIVATE_KEYS = {
    "excerpt", "excerpts", "text", "body", "body_text", "full_text", "raw_text", "raw_html", "html",
    "content", "blocks", "pages", "cache_ref", "blocks_ref", "cache_root", "cache_dir", "local_path",
    "text_path", "raw_path", "path", "error", "traceback", "stdout", "stderr", "source_text",
    "quote", "quotes", "quotation", "snippet", "snippets", "transcript", "statement",
}
PRIVATE_PATH = re.compile(r"(?:/(?:Users|home|private|tmp|var|Volumes|mnt|workspace|root)/|(?<![A-Za-z0-9])[A-Za-z]:[\\/])")
STATE_FIELDS = (
    "work_id", "metadata_hits", "body_source_state", "body_scan_status", "body_hits", "verified_count",
    "full_text_scanned", "partial_text_scanned", "relevance",
)
SQL_COLUMNS = (
    "work_id", "metadata_hits", "body_source_state", "body_scan_status", "body_hits", "verified_count",
    "relevance_status", "first_public_month", "primary_direction", "abstract_present", "source_attempted",
    "full_text_scanned", "partial_text_scanned", "full_text_hits", "metadata_scanned",
)


def _public(value):
    """Drop content/private cache fields at every nesting depth, not just top-level."""
    if isinstance(value, dict):
        return {key: _public(item) for key, item in value.items()
                if key not in PRIVATE_KEYS and not key.endswith(("_path", "_file", "_directory"))
                and not (isinstance(item, str) and (PRIVATE_PATH.search(item) or item.startswith(("file://", ".research/"))))}
    if isinstance(value, list):
        return [_public(item) for item in value
                if not (isinstance(item, str) and (PRIVATE_PATH.search(item) or item.startswith(("file://", ".research/"))))]
    return value


def project_work(row):
    """Approximately 230 bytes/work; descriptions live in existing work shards."""
    return {
        "work_id": row["work_id"], "metadata_hits": row["metadata_scan"]["mention_count"],
        "body_source_state": row["body_source_state"], "body_scan_status": row["body_scan_status"],
        "body_hits": row["body_mention_count"], "verified_count": row["verified_usage_count"],
        "full_text_scanned": row["full_text_screened_current_dictionary"],
        "partial_text_scanned": row["partial_text_screened_current_dictionary"],
        "relevance": row["relevance_status"],
    }


def _sql_row(row):
    return (row["work_id"], row["metadata_scan"]["mention_count"], row["body_source_state"], row["body_scan_status"],
            row["body_mention_count"], row["verified_usage_count"], row["relevance_status"], row["first_public_month"],
            row["primary_direction"], int("abstract" in row["metadata_scan"]["nonempty_fields"]),
            int(row["source_attempt_count"] > 0), int(row["full_text_screened_current_dictionary"]),
            int(row["partial_text_screened_current_dictionary"]), row["full_text_mention_count"],
            int(row["metadata_scan"]["status"] == "scanned"))


def _common(summary):
    return {key: summary[key] for key in ("schema_version", "dataset_version", "data_through", "dictionary_hash")}


def _public_observation(record):
    fields = ("work_id", "source_url", "effective_url", "observed_at", "status", "raw_sha256", "text_sha256",
              "version", "body_characters", "http_status", "error_code", "fetched_at", "processing_basis",
              "observation_id", "parent_observation_id", "parser_version", "manual_reviewed", "text_scope",
              "images_not_inspected", "supplementary_materials_not_inspected", "transport_verification",
              "transport_complete", "transport_returncode", "transport_truncated", "curl_exit_code")
    return _public({key: record[key] for key in fields if key in record})


def _public_scan(record):
    fields = ("work_id", "source_url", "effective_url", "observed_at", "scope", "status", "dictionary_hash",
              "content_hash", "source_observation_hash", "detector_version", "parser_version", "version")
    result = {key: record[key] for key in fields if key in record}
    if "matches" in record:
        result["matches"] = [{key: match[key] for key in ("dictionary_id", "term", "start", "end", "section", "section_id", "section_title") if key in match}
                             for match in record["matches"]]
    return _public(result)


def load_hardware_dictionary(path):
    """Required configuration, never an implicit empty discovery dictionary."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError("hardware_coverage_dictionary_required:" + str(path))
    dictionary = json.loads(path.read_text())
    if not isinstance(dictionary, dict) or str(dictionary.get("version", "")).strip() in {"", "None", "unconfigured"}:
        raise ValueError("hardware_coverage_dictionary_version_required")
    # Validate every entry before any public output is written. A deliberately
    # supplied empty dictionary is valid for isolated fixtures, not a fallback.
    detect_mentions("", dictionary)
    if _public(dictionary) != dictionary:
        raise ValueError("hardware_coverage_dictionary_contains_private_content")
    return dictionary


def _models(dictionary, candidates, included, common):
    mentions = defaultdict(lambda: {"metadata_mention": set(), "body_mention": set()})
    for candidate in candidates:
        mentions[candidate["dictionary_id"]][candidate["candidate_kind"]].add(candidate["work_id"])
    result = []
    for entry in sorted(dictionary["entries"], key=lambda row: row["dictionary_id"]):
        by_kind = mentions[entry["dictionary_id"]]
        metadata, body = by_kind["metadata_mention"], by_kind["body_mention"]
        combined = metadata | body
        result.append({
            **{key: entry[key] for key in ("dictionary_id", "name", "category", "identity_level", "hardware_ids", "source_urls") if key in entry},
            "evidence_status": "unverified_mention", "usage_inference": "none",
            "metadata_work_count": len(metadata), "body_work_count": len(body), "candidate_work_count": len(combined),
            "included_metadata_work_count": len(metadata & included), "included_body_work_count": len(body & included),
            "included_candidate_work_count": len(combined & included),
            "metadata_work_ids": sorted(metadata), "body_work_ids": sorted(body), "work_ids": sorted(combined),
        })
    return {**common, "scope": "dictionary_mentions_only_not_verified_usage", "models": result,
            "counts": {"dictionary_entries": len(result), "models_with_mentions": sum(bool(row["work_ids"]) for row in result),
                       "candidate_works": len({wid for row in result for wid in row["work_ids"]})},
            "limits": ["Title/abstract matches are metadata-only, not whole-paper review.",
                       "Body counts include current-hash full or partial body-text mentions, not verified device use.",
                       "Counts are unique canonical works per dictionary identity; identities can overlap across works.",
                       "A no-hit dictionary entry does not imply absence or zero use. Existing verified relationships remain separate."]}


def build_coverage(payload, authority, dictionary, source_scans, source_observations, manifest):
    """Build from caller-supplied inputs and share the site's dataset revision."""
    if not manifest.get("dataset_version") or not manifest.get("data_through"):
        raise ValueError("hardware_coverage_manifest_version_and_date_required")
    census = build_census(payload, authority, dictionary, source_scans, source_observations,
                          manifest["data_through"], include_excerpts=False)
    public_dictionary = _public(dictionary)
    if fingerprint(public_dictionary) != census["summary"]["dictionary_hash"]:
        raise ValueError("hardware_coverage_dictionary_contains_private_content")
    summary = {**census["summary"], "dataset_version": manifest["dataset_version"], "data_through": manifest["data_through"],
               "downloads": {"coverage": "/downloads/equipment/hardware-coverage.jsonl.gz"},
               "work_shards": 256, "work_shard_algorithm": "sha1(work_id UTF-8)[:2]",
               "work_shard_template": "coverage/works/{shard}.json", "work_projection_fields": list(STATE_FIELDS),
               "public_content_policy": "No paper excerpts, raw body text, or local cache paths; complete census rows are compressed once."}
    included = {row["work_id"] for row in census["rows"] if row["relevance_status"] == "included"}
    models = _models(public_dictionary, census["candidates"], included, _common(summary))
    # Keep a single reference to the full census rows. Sanitization occurs one
    # row at a time during export, rather than duplicating tens of MB in RAM.
    return {"summary": summary, "models": models, "rows": census["rows"], "dictionary": public_dictionary,
            "source_observations": [_public_observation(row) for row in source_observations or []],
            "source_scans": [_public_scan(row) for row in source_scans or []]}


def _shard_id(work_id):
    return hashlib.sha1(work_id.encode()).hexdigest()[:2]


def _row_index(bundle):
    rows = bundle["rows"]
    by_work = {row["work_id"]: row for row in rows}
    if len(by_work) != len(rows):
        raise ValueError("hardware_coverage_duplicate_work_id")
    if fingerprint(sorted(by_work)) != bundle["summary"]["work_set_hash"]:
        raise ValueError("hardware_coverage_work_set_hash_mismatch")
    return by_work


def _hash_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_gzip_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False) as target:
            temporary = Path(target.name)
            # No varying timestamp or local filename enters the gzip header.
            with gzip.GzipFile(filename="", mode="wb", compresslevel=9, fileobj=target, mtime=0) as compressed:
                for row in rows:
                    compressed.write((encode(_public(row)) + "\n").encode())
        if path.exists() and _hash_file(path) == _hash_file(temporary):
            temporary.unlink()
        else:
            temporary.replace(path)
        temporary = None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def export_coverage(bundle, api_equipment_dir, downloads_dir):
    """Publish compact API shards and exactly one compressed full-row copy."""
    _row_index(bundle)
    api, downloads = Path(api_equipment_dir), Path(downloads_dir)
    for name, key in (("coverage-summary.json", "summary"), ("coverage-model-candidates.json", "models")):
        write_if_changed(api / name, encode(_public(bundle[key])) + "\n")
    grouped = defaultdict(dict)
    for row in bundle["rows"]:
        grouped[_shard_id(row["work_id"])][row["work_id"]] = project_work(row)
    for number in range(256):
        shard = f"{number:02x}"
        write_if_changed(api / "coverage/works" / (shard + ".json"),
                         encode({**_common(bundle["summary"]), "by_work": grouped[shard]}) + "\n")
    _write_gzip_rows(downloads / "hardware-coverage.jsonl.gz", bundle["rows"])


def _metadata(bundle):
    return {key: _public(bundle[key]) for key in ("summary", "dictionary", "source_observations", "source_scans", "models")}


def coverage_sqlite(connection, bundle):
    """Narrow typed rows plus reproducible source/dictionary metadata, no body."""
    _row_index(bundle)
    connection.executescript("""
        CREATE TABLE hardware_coverage (
            work_id TEXT PRIMARY KEY,
            metadata_hits INTEGER NOT NULL CHECK(metadata_hits >= 0),
            body_source_state TEXT NOT NULL,
            body_scan_status TEXT NOT NULL,
            body_hits INTEGER NOT NULL CHECK(body_hits >= 0),
            verified_count INTEGER NOT NULL CHECK(verified_count >= 0),
            relevance_status TEXT NOT NULL,
            first_public_month TEXT NOT NULL,
            primary_direction TEXT NOT NULL,
            abstract_present INTEGER NOT NULL CHECK(abstract_present IN (0,1)),
            source_attempted INTEGER NOT NULL CHECK(source_attempted IN (0,1)),
            full_text_scanned INTEGER NOT NULL CHECK(full_text_scanned IN (0,1)),
            partial_text_scanned INTEGER NOT NULL CHECK(partial_text_scanned IN (0,1)),
            full_text_hits INTEGER NOT NULL CHECK(full_text_hits >= 0),
            metadata_scanned INTEGER NOT NULL CHECK(metadata_scanned IN (0,1))
        );
        CREATE TABLE coverage_metadata (key TEXT PRIMARY KEY, payload_json TEXT NOT NULL);
    """)
    connection.executemany("INSERT INTO hardware_coverage VALUES (" + ",".join("?" for _ in SQL_COLUMNS) + ")",
                           (_sql_row(row) for row in bundle["rows"]))
    connection.executemany("INSERT INTO coverage_metadata VALUES (?,?)", ((key, encode(value)) for key, value in _metadata(bundle).items()))


def _sqlite_counts(connection, where="", parameters=()):
    # Recompute independently from typed SQLite columns; never trust saved
    # summary JSON to stand in for physical-row coverage.
    expressions = {
        "denominator": "COUNT(*)",
        "metadata_screened_work_count": "SUM(metadata_scanned)",
        "metadata_nonempty_abstract_work_count": "SUM(abstract_present)",
        "metadata_mention_work_count": "SUM(metadata_hits > 0)",
        "body_attempted_work_count": "SUM(source_attempted)",
        "full_text_available_work_count": "SUM(body_source_state = 'full_text_available')",
        "partial_text_available_work_count": "SUM(body_source_state = 'partial_text')",
        "full_text_not_attempted_work_count": "SUM(body_source_state = 'not_attempted')",
        "full_text_failed_work_count": "SUM(body_source_state IN ('unavailable','blocked','identity_mismatch'))",
        "full_text_screened_current_dictionary_work_count": "SUM(full_text_scanned)",
        "full_text_available_pending_scan_work_count": "SUM(body_source_state = 'full_text_available' AND NOT full_text_scanned)",
        "full_text_scanned_no_dictionary_mentions_work_count": "SUM(full_text_scanned AND full_text_hits = 0)",
        "partial_text_screened_current_dictionary_work_count": "SUM(partial_text_scanned)",
        "body_mention_work_count": "SUM(body_hits > 0)",
        "verified_relationship_work_count": "SUM(verified_count > 0)",
        "verified_usage_relationship_count": "SUM(verified_count)",
        "unverified_work_count": "SUM(verified_count = 0)",
        **{"source_" + status + "_work_count": "SUM(body_source_state = '" + status + "')" for status in sorted(FAILED_STATUSES)},
    }
    values = connection.execute("SELECT " + ",".join(expressions.values()) + " FROM hardware_coverage" + (" WHERE " + where if where else ""), parameters).fetchone()
    result = {key: (value or 0) for key, value in zip(expressions, values)}
    result["metadata_missing_abstract_work_count"] = result["denominator"] - result["metadata_nonempty_abstract_work_count"]
    for name in ("metadata_screened", "full_text_screened_current_dictionary", "verified_relationship"):
        result[name + "_fraction_of_denominator"] = round(result[name + "_work_count"] / result["denominator"], 6) if result["denominator"] else None
    return result


def _audit_summary(bundle, connection):
    summary, rows = bundle["summary"], bundle["rows"]
    included = [row for row in rows if row["relevance_status"] == "included"]
    for key, selected, where in (("all_works", rows, ""), ("included", included, "relevance_status = 'included'")):
        expected = _counts(selected)
        if summary[key] != expected:
            raise ValueError("hardware_coverage_summary_count_mismatch:" + key)
        if _sqlite_counts(connection, where) != expected:
            raise ValueError("hardware_coverage_sqlite_count_mismatch:" + key)
    for key, field in (("by_month", "first_public_month"), ("by_direction", "primary_direction"), ("by_relevance", "relevance_status")):
        grouped = defaultdict(list)
        for row in rows:
            grouped[row[field]].append(row)
        expected_groups = [{field: value, "all_works": _counts(group),
                            "included": _counts([row for row in group if row["relevance_status"] == "included"])}
                           for value, group in sorted(grouped.items())]
        if summary[key] != expected_groups:
            raise ValueError("hardware_coverage_summary_group_mismatch:" + key)
        for group in expected_groups:
            if _sqlite_counts(connection, field + " = ?", (group[field],)) != group["all_works"]:
                raise ValueError("hardware_coverage_sqlite_group_mismatch:" + key)
            if _sqlite_counts(connection, field + " = ? AND relevance_status = 'included'", (group[field],)) != group["included"]:
                raise ValueError("hardware_coverage_sqlite_included_group_mismatch:" + key)


def audit_coverage(bundle, api, downloads, connection):
    """Fail closed on any lost/duplicated ID, changed state, or public leak."""
    api, downloads = Path(api), Path(downloads)
    by_work = _row_index(bundle)
    _audit_summary(bundle, connection)
    if connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='works'").fetchone():
        canonical_ids = {row[0] for row in connection.execute("SELECT work_id FROM works")}
        if canonical_ids != set(by_work):
            raise ValueError("hardware_coverage_sqlite_canonical_id_mismatch")
    for filename, key in (("coverage-summary.json", "summary"), ("coverage-model-candidates.json", "models")):
        if json.loads((api / filename).read_text()) != _public(bundle[key]):
            raise ValueError("hardware_coverage_api_mismatch:" + filename)
    shard_directory = api / "coverage/works"
    if {path.name for path in shard_directory.glob("*.json")} != {f"{number:02x}.json" for number in range(256)}:
        raise ValueError("hardware_coverage_shard_file_set_mismatch")
    api_ids = set()
    for number in range(256):
        shard = f"{number:02x}"
        saved = json.loads((shard_directory / (shard + ".json")).read_text())
        if {key: value for key, value in saved.items() if key != "by_work"} != _common(bundle["summary"]):
            raise ValueError("hardware_coverage_shard_metadata_mismatch:" + shard)
        for wid, row in saved["by_work"].items():
            if wid not in by_work or wid in api_ids or _shard_id(wid) != shard or row != project_work(by_work[wid]):
                raise ValueError("hardware_coverage_api_work_mismatch:" + wid)
            api_ids.add(wid)
    if api_ids != set(by_work):
        raise ValueError("hardware_coverage_api_work_set_mismatch")
    downloaded_ids = set()
    with gzip.open(downloads / "hardware-coverage.jsonl.gz", "rt", encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            wid = row.get("work_id")
            if wid not in by_work or wid in downloaded_ids or row != _public(by_work[wid]):
                raise ValueError("hardware_coverage_download_work_mismatch:" + str(wid))
            downloaded_ids.add(wid)
    if downloaded_ids != set(by_work):
        raise ValueError("hardware_coverage_download_work_set_mismatch")
    sql_ids = set()
    for row in connection.execute("SELECT " + ",".join(SQL_COLUMNS) + " FROM hardware_coverage"):
        if row[0] not in by_work or row[0] in sql_ids or tuple(row) != _sql_row(by_work[row[0]]):
            raise ValueError("hardware_coverage_sqlite_work_mismatch:" + str(row[0]))
        sql_ids.add(row[0])
    if sql_ids != set(by_work):
        raise ValueError("hardware_coverage_sqlite_work_set_mismatch")
    saved_metadata = {key: json.loads(value) for key, value in connection.execute("SELECT key,payload_json FROM coverage_metadata")}
    if saved_metadata != _metadata(bundle):
        raise ValueError("hardware_coverage_sqlite_metadata_mismatch")
    # A malformed generated bundle must not be able to advertise inflated
    # unique model counts or unknown IDs even if files copied it faithfully.
    known_dictionary_ids = {entry["dictionary_id"] for entry in bundle["dictionary"]["entries"]}
    models = bundle["models"]["models"]
    if len(models) != len(known_dictionary_ids) or {row["dictionary_id"] for row in models} != known_dictionary_ids:
        raise ValueError("hardware_coverage_model_dictionary_mismatch")
    for model in models:
        sets = {key: set(model[key]) for key in ("work_ids", "metadata_work_ids", "body_work_ids")}
        if any(len(sets[key]) != len(model[key]) or not sets[key] <= by_work.keys() for key in sets):
            raise ValueError("hardware_coverage_model_work_ids_invalid")
        if (sets["work_ids"] != sets["metadata_work_ids"] | sets["body_work_ids"]
                or model["candidate_work_count"] != len(sets["work_ids"])
                or model["metadata_work_count"] != len(sets["metadata_work_ids"])
                or model["body_work_count"] != len(sets["body_work_ids"])
                or model["evidence_status"] != "unverified_mention" or model["usage_inference"] != "none"):
            raise ValueError("hardware_coverage_model_count_or_status_invalid")
        for prefix, ids_key in (("candidate", "work_ids"), ("metadata", "metadata_work_ids"), ("body", "body_work_ids")):
            if model["included_" + prefix + "_work_count"] != sum(by_work[wid]["relevance_status"] == "included" for wid in sets[ids_key]):
                raise ValueError("hardware_coverage_model_included_count_invalid")
    return {"status": "ok", "work_count": len(by_work), "dataset_version": bundle["summary"]["dataset_version"],
            "dictionary_hash": bundle["summary"]["dictionary_hash"], "shards": 256,
            "download_bytes": (downloads / "hardware-coverage.jsonl.gz").stat().st_size}
