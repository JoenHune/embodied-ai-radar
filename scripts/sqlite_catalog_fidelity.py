"""Lossless catalogue restore views over existing SQLite export storage.

No files, network, commits, Python UDFs, or edits to business tables. JSON
records are compared as multisets; original JSON whitespace/key order is not
part of the contract. Requires SQLite JSON functions and the standard ->
operator (feature-probed, including null, huge integers and escaped keys).
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections import Counter, defaultdict
from contextlib import contextmanager

FULL = {
    "source-records": "source_records", "work-aliases": "work_aliases", "evidence-events": "evidence_events",
    "work-relations": "work_relations", "reconciliation": "source_reconciliation", "text-snapshots": "text_snapshots",
    "report-text-snapshots": "report_text_snapshots",
}
PARTIAL = {
    "manifestations": ("manifestations", {key: key for key in ["manifestation_id", "work_id", "kind", "url", "published_at", "venue", "year", "status", "peer_reviewed", "source_record_id"]}, ("manifestation_id",)),
    "organizations": ("organizations", {"organization_id": "organization_id", "display_name": "name", **{key: key for key in ["slug", "tier", "entity_type", "region", "country", "source_health"]}}, ("organization_id",)),
    "work-organization-links": ("work_organizations", {"work_id": "work_id", "organization_id": "organization_id", "role": "role", "evidence_grade": "attribution_grade", "confidence": "confidence", "evidence_url": "evidence_url"}, ("work_id", "organization_id", "evidence_url")),
    "field-provenance": ("field_provenance", {key: key for key in ["work_id", "field", "source_record_id", "observed_at"]}, ("work_id", "field", "source_record_id", "observed_at")),
    "taxonomy-assignments": ("taxonomy_assignments", {key: key for key in ["work_id", "axis", "code", "is_primary", "confidence", "classifier_version"]}, ("work_id", "axis", "code")),
}
RAW = {"source-health", "organization-candidates", "editorial-claims"}
TABLES = ("works", "manifestations", "organizations", "work-organization-links", "source-records", "field-provenance",
          "work-aliases", "evidence-events", "editorial-claims", "work-relations", "reconciliation", "taxonomy-assignments",
          "source-health", "organization-candidates", "text-snapshots", "report-text-snapshots")
DIGEST_METHOD = "sha256_of_sorted_canonical_row_sha256_bytes_with_multiplicity"


def _encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _counter(rows):
    return Counter(hashlib.sha256(_encode(row).encode()).digest() for row in rows)


def _digest(counter):
    value = hashlib.sha256()
    for row_hash, count in sorted(counter.items()):
        for _ in range(count):
            value.update(row_hash)
    return value.hexdigest()


def _name(table):
    return table.replace("-", "_")


def _query(connection, sql, values=()):
    cursor = connection.cursor()
    cursor.row_factory = None
    return cursor.execute(sql, values)


def _exists(connection, name):
    return _query(connection, "SELECT 1 FROM sqlite_master WHERE name=? AND type IN ('table','view')", (name,)).fetchone() is not None


@contextmanager
def _transaction(connection):
    # Releasing an outermost SAVEPOINT commits in SQLite. Open an explicit
    # caller-owned transaction first so this function never commits implicitly.
    if not connection.in_transaction:
        connection.execute("BEGIN")
    connection.execute("SAVEPOINT catalog_fidelity_build")
    try:
        yield
    except Exception:
        connection.execute("ROLLBACK TO catalog_fidelity_build")
        connection.execute("RELEASE catalog_fidelity_build")
        raise
    else:
        connection.execute("RELEASE catalog_fidelity_build")


def _probe_json(connection):
    value = {"a\".x": [None, True, False], "large": 123456789012345678901234567890, "null": None}
    original = _encode(value)
    restored = _query(connection, "SELECT json_group_object(key,json(? -> fullkey)) FROM json_each(?)", (original, original)).fetchone()[0]
    if _encode(json.loads(restored)) != original:
        raise ValueError("sqlite_json_restore_features_unavailable")


def _base(connection, table):
    """Return base view name/source name/key fields, without changing sources."""
    stem = _name(table)
    base = "catalog_fidelity_base_" + stem
    if table == "works" and _exists(connection, "works") and _exists(connection, "work_payloads"):
        # source_rowid is a logical key order, not SQLite's mutable physical
        # rowid. VACUUM may renumber physical rowids on TEXT-primary-key tables.
        sql = "SELECT CAST(row_number() OVER (ORDER BY w.work_id) AS INTEGER) AS source_rowid,p.payload_json FROM works w JOIN work_payloads p ON p.work_id=w.work_id"
        source, keys = "work_payloads", ("work_id",)
    elif table in FULL and _exists(connection, FULL[table]):
        source, keys = FULL[table], ()
        sql = f"SELECT rowid AS source_rowid,payload_json FROM {source}"
    elif table in PARTIAL and _exists(connection, PARTIAL[table][0]):
        source, mapping, keys = PARTIAL[table]
        columns = {row[1] for row in _query(connection, f"PRAGMA table_info({source})")}
        values, ordering = [], []
        for key, column in mapping.items():
            if column not in columns:
                continue
            expression = f'"{column}"'
            if key in {"is_primary", "peer_reviewed"}:
                expression = f"json(CASE WHEN {expression} IS NULL THEN 'null' WHEN {expression} THEN 'true' ELSE 'false' END)"
            values.extend(["'" + key + "'", expression])
            ordering.append(expression)
        # Ties are safe: every value used to reconstruct the baseline is
        # identical. Distinct authority extras live in their separate bindings.
        # Integer affinity is required for SQLite to build the automatic
        # covering index used by the binding join (without it: nested scans).
        sql = f"SELECT CAST(row_number() OVER (ORDER BY {','.join(ordering) or '1'}) AS INTEGER) AS source_rowid,json_object({','.join(values)}) AS payload_json FROM {source}"
    else:
        source, keys = None, ()
        sql = "SELECT NULL AS source_rowid,'{}' AS payload_json WHERE 0"
    connection.execute(f"CREATE VIEW {base} AS {sql}")
    return base, source, keys


def _restore_view(connection, table, base):
    stem = _name(table)
    binding, view = "catalog_fidelity_rows_" + stem, "catalog_restore_" + stem
    # -> returns the original JSON token, unlike json_each.value which can
    # coerce booleans or huge integers. json() restores the JSON subtype after
    # UNION/subquery boundaries, preserving arrays/objects rather than strings.
    connection.execute(f"""
        CREATE VIEW {view} AS
        SELECT r.ordinal,
          CASE WHEN r.managed_hashes THEN json_set(r.restored,'$._managed_field_hashes',json(COALESCE(
            (SELECT payload_json FROM catalog_fidelity_managed_hash_objects h WHERE h.work_rowid=r.source_rowid),'{{}}')))
          ELSE r.restored END AS payload_json
        FROM (
          SELECT a.ordinal,a.source_rowid,a.managed_hashes,
            CASE WHEN a.patch_id=0 THEN COALESCE(b.payload_json,'{{}}') ELSE (
              SELECT json_group_object(key,json(fragment)) FROM (
                SELECT j.key, b.payload_json -> j.fullkey AS fragment
                  FROM json_each(COALESCE(b.payload_json,'{{}}')) j
                 WHERE NOT EXISTS (SELECT 1 FROM json_each(p.set_json) x WHERE x.key=j.key)
                   AND NOT EXISTS (SELECT 1 FROM json_each(p.remove_json) x WHERE x.value=j.key)
                UNION ALL
                SELECT j.key,p.set_json -> j.fullkey AS fragment FROM json_each(p.set_json) j
              )
            ) END AS restored
          FROM {binding} a LEFT JOIN {base} b ON b.source_rowid=a.source_rowid
          LEFT JOIN catalog_fidelity_patches p ON p.patch_id=a.patch_id
        ) r
    """)


def build_catalog_fidelity(connection, payload):
    """Build 16 restore views atomically; leave commit control to the caller."""
    _probe_json(connection)
    manifest = {"schema_version": "1", "digest_method": DIGEST_METHOD, "record_order": "multiset_not_jsonl_line_order",
                "sqlite_features": ["json", "json_each", "json_group_object", "json_set", "->", "lower(hex(blob))"], "tables": []}
    with _transaction(connection):
        for table in TABLES:
            stem = _name(table)
            for view in ["catalog_restore_" + stem, "catalog_fidelity_base_" + stem]:
                connection.execute(f"DROP VIEW IF EXISTS {view}")
        connection.execute("DROP VIEW IF EXISTS catalog_fidelity_managed_hash_objects")
        for table in TABLES:
            for name in ["catalog_fidelity_rows_" + _name(table), "catalog_fidelity_raw_" + _name(table)]:
                connection.execute(f"DROP TABLE IF EXISTS {name}")
        for name in ["catalog_fidelity_manifest", "catalog_fidelity_patches", "catalog_fidelity_work_hashes", "catalog_fidelity_hash_fields"]:
            connection.execute(f"DROP TABLE IF EXISTS {name}")
        connection.execute("CREATE TABLE catalog_fidelity_manifest(table_name TEXT PRIMARY KEY,source_table TEXT,restore_view TEXT NOT NULL,record_count INTEGER NOT NULL,digest TEXT NOT NULL,digest_method TEXT NOT NULL,storage_mode TEXT NOT NULL)")
        connection.execute("CREATE TABLE catalog_fidelity_patches(patch_id INTEGER PRIMARY KEY,set_json TEXT NOT NULL,remove_json TEXT NOT NULL)")
        connection.execute("INSERT INTO catalog_fidelity_patches VALUES(0,'{}','[]')")
        connection.execute("CREATE TABLE catalog_fidelity_hash_fields(field_id INTEGER PRIMARY KEY,name TEXT NOT NULL UNIQUE)")
        connection.execute("CREATE TABLE catalog_fidelity_work_hashes(work_rowid INTEGER NOT NULL,field_id INTEGER NOT NULL,hash_bytes BLOB NOT NULL CHECK(length(hash_bytes)=32),PRIMARY KEY(work_rowid,field_id)) WITHOUT ROWID")
        connection.execute("""CREATE VIEW catalog_fidelity_managed_hash_objects AS
            SELECT h.work_rowid,json_group_object(f.name,lower(hex(h.hash_bytes))) AS payload_json
            FROM catalog_fidelity_work_hashes h JOIN catalog_fidelity_hash_fields f USING(field_id) GROUP BY h.work_rowid""")
        patches = {("{}", "[]"): 0}
        fields, managed_by_work = {}, {}
        def patch_id(set_values, remove):
            key = (_encode(set_values), _encode(sorted(remove)))
            if key not in patches:
                pid = len(patches)
                connection.execute("INSERT INTO catalog_fidelity_patches VALUES(?,?,?)", (pid, *key))
                patches[key] = pid
            return patches[key]
        for table in TABLES:
            originals = payload.get(table, [])
            if not isinstance(originals, list) or any(not isinstance(row, dict) for row in originals):
                raise ValueError("catalog_fidelity_requires_json_object_rows:" + table)
            expected = _counter(originals)
            stem, view = _name(table), "catalog_restore_" + _name(table)
            if table in RAW:
                source = "catalog_fidelity_raw_" + stem
                connection.execute(f"CREATE TABLE {source}(ordinal INTEGER PRIMARY KEY,payload_json TEXT NOT NULL)")
                connection.executemany(f"INSERT INTO {source} VALUES(?,?)", ((index, _encode(row)) for index, row in enumerate(originals)))
                connection.execute(f"CREATE VIEW {view} AS SELECT ordinal,payload_json FROM {source}")
                mode = "authority_payload_separate_from_derived_tables"
            else:
                base, source, key_fields = _base(connection, table)
                base_rows = [(rid, json.loads(text)) for rid, text in _query(connection, f"SELECT source_rowid,payload_json FROM {base}")]
                if table in FULL and _counter(row for _, row in base_rows) == expected:
                    connection.execute(f"CREATE VIEW {view} AS SELECT source_rowid AS ordinal,payload_json FROM {base}")
                    mode = "reused_complete_payload"
                else:
                    mode = "sparse_field_patch" if source else "missing_source_payload_fallback"
                    if table in FULL and source:
                        # The normal complete-payload path above needs no
                        # anchors/sort. Only exceptional subset/duplicate/fallback
                        # bindings need stable logical ordering of payloads.
                        connection.execute(f"DROP VIEW {base}")
                        connection.execute(f"CREATE VIEW {base} AS SELECT CAST(row_number() OVER (ORDER BY payload_json) AS INTEGER) AS source_rowid,payload_json FROM {source}")
                        base_rows = [(rid, json.loads(text)) for rid, text in _query(connection, f"SELECT source_rowid,payload_json FROM {base}")]
                    binding = "catalog_fidelity_rows_" + stem
                    connection.execute(f"CREATE TABLE {binding}(ordinal INTEGER PRIMARY KEY,source_rowid INTEGER,patch_id INTEGER NOT NULL,managed_hashes INTEGER NOT NULL)")
                    candidates = defaultdict(list)
                    for rid, row in base_rows:
                        key = _encode([row.get(field) for field in key_fields]) if key_fields else hashlib.sha256(_encode(row).encode()).digest()
                        candidates[key].append((rid, row))
                    positions = Counter()
                    bindings = []
                    for index, row in enumerate(originals):
                        key = _encode([row.get(field) for field in key_fields]) if key_fields else hashlib.sha256(_encode(row).encode()).digest()
                        choices = candidates.get(key, [])
                        rid, original_base = choices[positions[key] % len(choices)] if choices else (None, {})
                        positions[key] += 1
                        normalized = False
                        desired = dict(row)
                        if table == "works" and rid is not None:
                            for field in ["title", "abstract"]:
                                if field in row and (field not in original_base or _encode(row[field]) != _encode(original_base[field])):
                                    raise ValueError("canonical_work_text_base_mismatch:" + str(row.get("work_id")) + ":" + field)
                            hashes = row.get("_managed_field_hashes")
                            if isinstance(hashes, dict) and all(isinstance(name, str) and isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) for name, value in hashes.items()):
                                if rid not in managed_by_work or managed_by_work[rid] == hashes:
                                    normalized = True
                                    desired.pop("_managed_field_hashes")
                                    if rid not in managed_by_work:
                                        managed_by_work[rid] = hashes
                                        for name, value in hashes.items():
                                            if name not in fields:
                                                fields[name] = len(fields) + 1
                                                connection.execute("INSERT INTO catalog_fidelity_hash_fields VALUES(?,?)", (fields[name], name))
                                            connection.execute("INSERT INTO catalog_fidelity_work_hashes VALUES(?,?,?)", (rid, fields[name], bytes.fromhex(value)))
                        changes = {key: value for key, value in desired.items() if key not in original_base or _encode(value) != _encode(original_base[key])}
                        removes = set(original_base) - set(desired)
                        bindings.append((index, rid, patch_id(changes, removes), int(normalized)))
                    connection.executemany(f"INSERT INTO {binding} VALUES(?,?,?,?)", bindings)
                    _restore_view(connection, table, base)
                del base_rows
            entry = {"table_name": table, "source_table": source, "restore_view": view, "record_count": len(originals),
                     "digest": _digest(expected), "digest_method": DIGEST_METHOD, "storage_mode": mode}
            connection.execute("INSERT INTO catalog_fidelity_manifest VALUES(?,?,?,?,?,?,?)", tuple(entry[key] for key in ["table_name", "source_table", "restore_view", "record_count", "digest", "digest_method", "storage_mode"]))
            manifest["tables"].append(entry)
        manifest["storage"] = {"patch_templates": len(patches) - 1, "managed_hash_fields": len(fields),
                               "managed_hash_entries": _query(connection, "SELECT count(*) FROM catalog_fidelity_work_hashes").fetchone()[0]}
        checked = audit_catalog_fidelity(connection, payload)
        if checked["status"] != "passed":
            raise ValueError("catalog_fidelity_build_failed:" + _encode(checked["errors"][:5]))
        manifest["status"] = "passed"
    return manifest


def audit_catalog_fidelity(connection, payload):
    """Read-only full-field/multiset audit; rejects altered values at equal count."""
    errors, tables = [], []
    if not _exists(connection, "catalog_fidelity_manifest"):
        return {"status": "failed", "tables": [], "errors": [{"reason": "fidelity_manifest_missing"}]}
    columns = ["table_name", "source_table", "restore_view", "record_count", "digest", "digest_method", "storage_mode"]
    metadata = {row[0]: dict(zip(columns, row)) for row in _query(connection, "SELECT " + ",".join(columns) + " FROM catalog_fidelity_manifest")}
    if set(metadata) != set(TABLES):
        errors.append({"reason": "fidelity_manifest_table_set_changed"})
    for table in TABLES:
        entry = metadata.get(table)
        view = "catalog_restore_" + _name(table)
        if not entry or entry["restore_view"] != view or not _exists(connection, view):
            errors.append({"table_name": table, "reason": "restore_view_missing_or_changed"})
            continue
        expected_source = "catalog_fidelity_raw_" + _name(table) if table in RAW else "work_payloads" if table == "works" and _exists(connection, "works") and _exists(connection, "work_payloads") else FULL.get(table) if table in FULL and _exists(connection, FULL[table]) else PARTIAL[table][0] if table in PARTIAL and _exists(connection, PARTIAL[table][0]) else None
        if entry["source_table"] != expected_source:
            errors.append({"table_name": table, "reason": "manifest_source_table_mismatch"})
        expected = _counter(payload.get(table, []))
        try:
            actual = _counter(json.loads(row[0]) for row in _query(connection, f"SELECT payload_json FROM {view}"))
        except (ValueError, TypeError, KeyError, sqlite3.DatabaseError) as exc:
            errors.append({"table_name": table, "reason": "invalid_restored_json", "error_type": type(exc).__name__})
            continue
        missing, extra = sum((expected - actual).values()), sum((actual - expected).values())
        if missing or extra:
            errors.append({"table_name": table, "reason": "record_multiset_mismatch", "missing_records": missing, "unexpected_records": extra})
        if entry["record_count"] != sum(expected.values()) or entry["digest"] != _digest(expected) or entry["digest_method"] != DIGEST_METHOD:
            errors.append({"table_name": table, "reason": "manifest_count_or_digest_mismatch"})
        tables.append({"table_name": table, "restore_view": view, "expected_records": sum(expected.values()), "restored_records": sum(actual.values()),
                       "expected_digest": _digest(expected), "restored_digest": _digest(actual), "missing_records": missing, "unexpected_records": extra})
    return {"status": "failed" if errors else "passed", "tables": tables, "errors": errors}
