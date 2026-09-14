"""Lossless restore uses only standard SQL on in-memory SQLite fixtures."""
import copy
import json
import sqlite3
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from sqlite_catalog_fidelity import TABLES, FULL, PARTIAL, build_catalog_fidelity, audit_catalog_fidelity


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fixture():
    payload = {name: [] for name in TABLES}
    payload["works"] = [
        {"work_id": "work:1", "title": "Original π0.5 title", "abstract": "UNIQUE ORIGINAL ABSTRACT NEVER DUPLICATED", "title_zh": "原始中译", "summary_zh": None,
         "_managed_field_hashes": {"title": "ab" * 32, 'odd"field': "01" * 32}, "absent_in_display": [False, None, 3]},
        {"work_id": "work:2", "title": "Second", "abstract": "Second abstract", "_managed_field_hashes": {"title": None, "nonstandard": [1, True, "UPPERCASE"]}},
        {"work_id": "work:3", "title": "Missing hashes", "abstract": "Third abstract"},
        {"work_id": "work:4", "title": "Empty hashes", "abstract": "Fourth abstract", "_managed_field_hashes": {}},
        {"work_id": "work:5", "title": "Null hashes", "abstract": "Fifth abstract", "_managed_field_hashes": None},
    ]
    payload["manifestations"] = [{"manifestation_id": "m:1", "work_id": "work:1", "kind": "technical_report", "url": "https://example.test/report",
                                   "published_at": "2026-08-01", "date_precision": "month", "date_history": [{"previous_date": "2026-08-15", "previous_precision": "day"}],
                                   "peer_reviewed": False, "publication_status": "first_party", "unknown_future_field": {"flag": True, "value": None}}]
    payload["organizations"] = [{"organization_id": "org:1", "display_name": "Lab", "parent_relations": [{"parent_id": "org:root", "evidence_url": "https://example.test/parent"}],
                                  "leaders": [{"name": "Fixture PI", "valid_from": None}], "official_urls": {"home": "https://example.test/"}, "null_field": None}]
    link = {"work_id": "work:1", "organization_id": "org:1", "evidence_url": "https://example.test/member", "evidence_grade": "G2",
            "membership_evidence": {"valid_from": "2025-01-01", "valid_to": None, "author": "Fixture Author"}}
    payload["work-organization-links"] = [link, copy.deepcopy(link), {**copy.deepcopy(link), "membership_evidence": {"valid_from": "2024-01-01", "valid_to": "2024-12-31"}}]
    provenance = {"work_id": "work:1", "field": "abstract", "source_record_id": "source:1", "observed_at": "2026-09-06T00:00:00Z", "basis": "source-content-check",
                  'quote".key': None, "huge_integer": 123456789012345678901234567890, "real": 1.0, "review_id": "review:1"}
    payload["field-provenance"] = [provenance, copy.deepcopy(provenance)]
    tax = {"work_id": "work:1", "axis": "direction", "code": "D3", "is_primary": True, "confidence": "accepted", "classifier_version": "3.0", "future_review": {"status": "pending"}}
    payload["taxonomy-assignments"] = [tax, copy.deepcopy(tax)]
    payload["source-health"] = [{"source_id": "health:1", "known_links": [{"url": "https://example.test/report"}], "error": None}]
    payload["organization-candidates"] = [{"candidate_id": "candidate:1", "ambiguity_flags": ["same_name"], "unknown": {"empty": []}}]
    for table in FULL:
        payload[table] = [{"fixture_table": table, "unknown": {"null": None, "booleans": [True, False], "order": [3, 1, 2]}}]
    return payload


def database(payload):
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE works(work_id TEXT PRIMARY KEY,title TEXT,abstract TEXT)")
    con.execute("CREATE TABLE work_extra_payloads(work_id TEXT PRIMARY KEY,payload_json TEXT)")
    con.execute("CREATE VIEW work_payloads AS SELECT w.work_id,json_set(e.payload_json,'$.work_id',w.work_id,'$.title',w.title,'$.abstract',w.abstract) payload_json FROM works w JOIN work_extra_payloads e USING(work_id)")
    for row in payload["works"]:
        con.execute("INSERT INTO works VALUES(?,?,?)", (row["work_id"], row["title"], row["abstract"]))
        display = {key: value for key, value in row.items() if key not in {"_managed_field_hashes", "title", "abstract", "absent_in_display"}}
        display.update(title_zh="最新展示中译", summary_zh="最新展示摘要", display_only=True)
        con.execute("INSERT INTO work_extra_payloads VALUES(?,?)", (row["work_id"], encode(display)))
    for table, (source, mapping, _) in PARTIAL.items():
        columns = list(dict.fromkeys(mapping.values()))
        numeric = {"is_primary", "peer_reviewed", "year"}
        con.execute(f"CREATE TABLE {source}(" + ",".join('"' + col + '" ' + ("INTEGER" if col in numeric else "TEXT") for col in columns) + ")")
        inserted = set()
        for row in payload[table]:
            # Simulate work_organizations INSERT OR IGNORE collapsing equal
            # projected rows; the restore layer must preserve all originals.
            values = tuple(row.get(key) for key in mapping)
            if table == "work-organization-links" and values in inserted:
                continue
            inserted.add(values)
            con.execute(f"INSERT INTO {source} VALUES(" + ",".join("?" for _ in columns) + ")", values)
    for table, source in FULL.items():
        con.execute(f"CREATE TABLE {source}(payload_json TEXT)")
        con.executemany(f"INSERT INTO {source} VALUES(?)", [(encode(row),) for row in payload[table]])
    con.execute("CREATE TABLE editorial_claims(claim_id TEXT,text TEXT)")
    con.execute("INSERT INTO editorial_claims VALUES('derived:claim','Not the authority editorial table')")
    return con


def restored(con, table):
    return [json.loads(row[0]) for row in con.execute("SELECT payload_json FROM catalog_restore_" + table.replace("-", "_"))]


class SQLiteCatalogFidelityTests(unittest.TestCase):
    def setUp(self):
        self.payload = fixture()
        self.con = database(self.payload)

    def tearDown(self):
        self.con.close()

    def test_every_table_full_field_and_multiset_restore(self):
        before = copy.deepcopy(self.payload)
        manifest = build_catalog_fidelity(self.con, self.payload)
        self.assertEqual(manifest["status"], "passed")
        self.assertEqual({row["table_name"] for row in manifest["tables"]}, set(TABLES))
        for table in TABLES:
            with self.subTest(table=table):
                self.assertEqual(Counter(map(encode, restored(self.con, table))), Counter(map(encode, self.payload[table])))
        self.assertEqual(self.payload, before)
        self.assertEqual(audit_catalog_fidelity(self.con, self.payload)["status"], "passed")

    def test_complete_payloads_reused_without_duplicate_body_storage(self):
        manifest = build_catalog_fidelity(self.con, self.payload)
        entries = {entry["table_name"]: entry for entry in manifest["tables"]}
        for table in FULL:
            self.assertEqual(entries[table]["storage_mode"], "reused_complete_payload")
            self.assertEqual(entries[table]["source_table"], FULL[table])
        patches = "\n".join(row[0] for row in self.con.execute("SELECT set_json FROM catalog_fidelity_patches"))
        self.assertNotIn(self.payload["works"][0]["abstract"], patches)
        self.assertNotIn(self.payload["works"][0]["title"], patches)

    def test_binary_managed_hashes_and_nonstandard_fallback(self):
        manifest = build_catalog_fidelity(self.con, self.payload)
        self.assertEqual(manifest["storage"]["managed_hash_entries"], 2)
        self.assertEqual(manifest["storage"]["managed_hash_fields"], 2)
        self.assertEqual(self.con.execute("SELECT count(*) FROM catalog_fidelity_work_hashes WHERE length(hash_bytes)=32 AND typeof(hash_bytes)='blob'").fetchone()[0], 2)
        rows = {row["work_id"]: row for row in restored(self.con, "works")}
        for original in self.payload["works"]:
            self.assertEqual(encode(rows[original["work_id"]]), encode(original))
        self.assertNotIn("_managed_field_hashes", rows["work:3"])
        self.assertEqual(rows["work:4"]["_managed_field_hashes"], {})
        self.assertIsNone(rows["work:5"]["_managed_field_hashes"])

    def test_display_chinese_and_authority_chinese_are_separate(self):
        build_catalog_fidelity(self.con, self.payload)
        original = next(row for row in restored(self.con, "works") if row["work_id"] == "work:1")
        display = json.loads(self.con.execute("SELECT payload_json FROM work_payloads WHERE work_id='work:1'").fetchone()[0])
        self.assertEqual(original["title_zh"], "原始中译")
        self.assertIsNone(original["summary_zh"])
        self.assertEqual(display["title_zh"], "最新展示中译")
        self.assertEqual(display["summary_zh"], "最新展示摘要")
        self.assertNotIn("display_only", original)

    def test_explicit_null_absence_huge_numbers_and_escaped_keys(self):
        build_catalog_fidelity(self.con, self.payload)
        row = restored(self.con, "field-provenance")[0]
        self.assertIn('quote".key', row)
        self.assertIsNone(row['quote".key'])
        self.assertIsInstance(row["huge_integer"], int)
        self.assertEqual(row["huge_integer"], self.payload["field-provenance"][0]["huge_integer"])
        self.assertIsInstance(row["real"], float)
        manifestation = restored(self.con, "manifestations")[0]
        self.assertNotIn("venue", manifestation)
        self.assertEqual(manifestation["date_precision"], "month")

    def test_g2_membership_provenance_and_duplicate_collapsed_projection_restored(self):
        self.assertEqual(self.con.execute("SELECT count(*) FROM work_organizations").fetchone()[0], 1)
        build_catalog_fidelity(self.con, self.payload)
        rows = restored(self.con, "work-organization-links")
        self.assertEqual(len(rows), 3)
        self.assertEqual(Counter(map(encode, rows)), Counter(map(encode, self.payload["work-organization-links"])))
        self.assertEqual(Counter(map(encode, restored(self.con, "taxonomy-assignments"))), Counter(map(encode, self.payload["taxonomy-assignments"])))

    def test_empty_authority_editorial_not_confused_with_derived_claims(self):
        build_catalog_fidelity(self.con, self.payload)
        self.assertEqual(restored(self.con, "editorial-claims"), [])
        self.assertEqual(self.con.execute("SELECT count(*) FROM editorial_claims").fetchone()[0], 1)
        self.payload["editorial-claims"] = [{"claim_id": "authority:1", "nested": {"review": None}}]
        build_catalog_fidelity(self.con, self.payload)
        self.assertEqual(restored(self.con, "editorial-claims"), self.payload["editorial-claims"])

    def test_rebuild_is_idempotent_and_never_commits_callers_transaction(self):
        self.con.execute("CREATE TABLE caller_state(value TEXT)")
        self.con.execute("INSERT INTO caller_state VALUES('pending')")
        before = self.con.total_changes
        first = build_catalog_fidelity(self.con, self.payload)
        second = build_catalog_fidelity(self.con, self.payload)
        self.assertEqual(first, second)
        self.assertTrue(self.con.in_transaction)
        self.assertGreater(self.con.total_changes, before)
        self.con.rollback()
        self.assertFalse(self.con.execute("SELECT 1 FROM sqlite_master WHERE name='catalog_fidelity_manifest'").fetchone())

    def test_success_without_outer_transaction_still_leaves_commit_to_caller(self):
        self.con.commit()
        self.assertFalse(self.con.in_transaction)
        build_catalog_fidelity(self.con, self.payload)
        self.assertTrue(self.con.in_transaction)
        self.con.rollback()
        self.assertFalse(self.con.execute("SELECT 1 FROM sqlite_master WHERE name='catalog_fidelity_manifest'").fetchone())

    def test_failed_rebuild_rolls_back_only_its_own_storage(self):
        build_catalog_fidelity(self.con, self.payload)
        original = restored(self.con, "manifestations")
        self.con.execute("CREATE TABLE caller_state(value TEXT)")
        self.con.execute("INSERT INTO caller_state VALUES('preserve')")
        invalid = copy.deepcopy(self.payload)
        invalid["works"][0]["abstract"] = "Changed canonical body must trigger reexport, not duplication"
        with self.assertRaisesRegex(ValueError, "canonical_work_text_base_mismatch"):
            build_catalog_fidelity(self.con, invalid)
        self.assertEqual(restored(self.con, "manifestations"), original)
        self.assertEqual(self.con.execute("SELECT value FROM caller_state").fetchone()[0], "preserve")
        self.assertEqual(audit_catalog_fidelity(self.con, self.payload)["status"], "passed")

    def test_audit_catches_same_count_value_tampering_and_manifest_changes(self):
        build_catalog_fidelity(self.con, self.payload)
        self.con.execute("UPDATE manifestations SET kind='demo'")
        report = audit_catalog_fidelity(self.con, self.payload)
        self.assertEqual(report["status"], "failed")
        self.assertTrue(any(error.get("table_name") == "manifestations" and error["reason"] == "record_multiset_mismatch" for error in report["errors"]))
        self.con.execute("UPDATE catalog_fidelity_manifest SET digest='wrong' WHERE table_name='works'")
        self.assertTrue(any(error["reason"] == "manifest_count_or_digest_mismatch" for error in audit_catalog_fidelity(self.con, self.payload)["errors"]))

    def test_reused_payload_missing_extra_or_duplicate_rows_are_exactly_mapped(self):
        self.payload["source-records"].append(copy.deepcopy(self.payload["source-records"][0]))
        self.payload["source-records"].append({"new_source": True, "unseen": None})
        self.con.execute("INSERT INTO source_records VALUES(?)", (encode({"extra_not_authority": True}),))
        manifest = build_catalog_fidelity(self.con, self.payload)
        self.assertEqual(Counter(map(encode, restored(self.con, "source-records"))), Counter(map(encode, self.payload["source-records"])))
        self.assertNotEqual(next(entry for entry in manifest["tables"] if entry["table_name"] == "source-records")["storage_mode"], "reused_complete_payload")

    def test_plain_new_connection_can_query_every_view_without_python_udfs(self):
        build_catalog_fidelity(self.con, self.payload)
        copy_connection = sqlite3.connect(":memory:")
        copy_connection.deserialize(self.con.serialize())
        try:
            self.assertEqual(audit_catalog_fidelity(copy_connection, self.payload)["status"], "passed")
        finally:
            copy_connection.close()

    def test_vacuum_and_physical_rowid_reordering_cannot_break_restore_bindings(self):
        # Force a full-payload exceptional binding path as well as ordinary
        # partial/works binding paths. Full direct reuse needs no stable order.
        self.payload["source-records"].append(copy.deepcopy(self.payload["source-records"][0]))
        for table in ["works", "manifestations", "organizations", "work_organizations", "field_provenance", "taxonomy_assignments", "source_records"]:
            self.con.execute(f"UPDATE {table} SET rowid=rowid*10")
        build_catalog_fidelity(self.con, self.payload)
        before = {table: Counter(map(encode, restored(self.con, table))) for table in TABLES}
        self.con.commit()
        self.con.execute("VACUUM")
        self.assertEqual(audit_catalog_fidelity(self.con, self.payload)["status"], "passed")
        for table in TABLES:
            self.assertEqual(Counter(map(encode, restored(self.con, table))), before[table], table)
        # Reorder physical records even on builds where VACUUM happens to keep
        # contiguous rowids: logical baseline ordering must remain authoritative.
        self.con.execute("UPDATE works SET rowid=-rowid")
        self.con.execute("UPDATE field_provenance SET rowid=-rowid")
        self.con.execute("UPDATE source_records SET rowid=-rowid")
        self.assertEqual(audit_catalog_fidelity(self.con, self.payload)["status"], "passed")

    def test_full_payload_reuse_does_not_sort_long_payloads_for_unused_ordinals(self):
        build_catalog_fidelity(self.con, self.payload)
        sql = self.con.execute("SELECT sql FROM sqlite_master WHERE name='catalog_fidelity_base_source_records'").fetchone()[0]
        self.assertNotIn("row_number", sql.lower())
        self.assertNotIn("order by", sql.lower())

    def test_partial_restore_materializes_baseline_once_then_uses_join_index(self):
        build_catalog_fidelity(self.con, self.payload)
        plan = [row[3] for row in self.con.execute("EXPLAIN QUERY PLAN SELECT payload_json FROM catalog_restore_field_provenance")]
        self.assertEqual(sum("MATERIALIZE catalog_fidelity_base_field_provenance" in row for row in plan), 1)
        self.assertTrue(any("SEARCH b USING AUTOMATIC" in row for row in plan), plan)

    def test_missing_business_tables_use_lossless_fallback_not_fake_records(self):
        con = sqlite3.connect(":memory:")
        try:
            payload = {"organizations": [{"organization_id": "org:1", "arbitrary": None}], "works": []}
            manifest = build_catalog_fidelity(con, payload)
            self.assertEqual(restored(con, "organizations"), payload["organizations"])
            self.assertEqual(restored(con, "works"), [])
            self.assertEqual(len(manifest["tables"]), 16)
        finally:
            con.close()


if __name__ == "__main__":
    unittest.main()
