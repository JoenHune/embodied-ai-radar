"""No project authority is written: every migration uses temporary catalogues."""
import contextlib
import copy
import io
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import migrate_source_records as migration
import source_record_store as store
import run_weekly_v3 as weekly
from catalog_store import TABLES, encode, fingerprint, load_catalog, read_table, save_catalog, table_output_paths, write_table
from sqlite_catalog_fidelity import build_catalog_fidelity, audit_catalog_fidelity


def files(root):
    return {str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()}


def fixture(root):
    catalog = root / "data/catalog"
    catalog.mkdir(parents=True)
    rows = [
        {"source_record_id": "source:a", "unknown": {"big": 123456789012345678901234567890, "null": None,
             "values": [True, False, 1, "中\u2028文"]}, "payload_hash": "old-evidence", "lineage": ["older:a", "older:b"]},
        {"source_record_id": "source:b", "classification_review": {"before": {"questions": []},
             "after": {"questions": ["Q0"]}, "proof": {"raw_sha256": "a" * 64}}, "url": "https://example.org/paper"},
        {"source_record_id": "source:c", "published_at": None, "reviewed_at": "2026-09-15T01:00:00Z", "text": "原文证据"},
    ]
    # Deliberately noncanonical spacing/key order and mixed line endings.
    raw = b"".join(json.dumps(row, ensure_ascii=False).encode() + (b"\r\n" if index == 1 else b"\n")
                   for index, row in enumerate(rows))
    (catalog / store.LEGACY).write_bytes(raw)
    payload = {name: rows if name == store.TABLE else [] for name in TABLES}
    hashes = {name: fingerprint(sorted(values, key=encode)) for name, values in payload.items()}
    metadata = {"schema_version": "3.1", "table_hashes": hashes, "catalog_hash": fingerprint(hashes),
                "ingested_at": "2026-09-15T00:00:00Z", "data_through": "2026-09-14", "unknown_metadata": [1, None]}
    (catalog / "manifest.json").write_text(encode(metadata) + "\n", encoding="utf-8")
    return catalog, rows, raw, metadata


class SourceRecordMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.catalog, self.rows, self.raw, self.metadata = fixture(self.root)
        self.stage, self.backup = self.root / "stage", self.root / "backup"

    def migrate(self, **kwargs):
        return migration.migrate(self.catalog, stage_dir=self.stage, backup_dir=self.backup, apply=True, **kwargs)

    def test_dryrun_is_read_only_and_reports_exact_manifest_hash(self):
        before = files(self.root)
        report = migration.migrate(self.catalog, stage_dir=self.stage, backup_dir=self.backup)
        self.assertFalse(report["applied"])
        self.assertEqual(report["source_record_count"], 3)
        self.assertEqual(report["source_table_hash"], self.metadata["table_hashes"][store.TABLE])
        self.assertEqual(sum(value["bytes"] for value in report["shards"].values()), len(self.raw))
        self.assertEqual(files(self.root), before)
        self.assertFalse(self.stage.exists())
        self.assertFalse(self.backup.exists())

    def test_explicit_apply_preserves_every_id_field_line_and_manifest(self):
        manifest = (self.catalog / "manifest.json").read_bytes()
        before = migration.snapshot(self.catalog)["by_id"]
        with patch.object(weekly, "ROOT", self.root):
            research_before = weekly.content_hash(weekly.research_state())
        result = self.migrate()
        self.assertTrue(result["applied"])
        self.assertFalse(result["cross_file_power_loss_atomic"])
        self.assertFalse((self.catalog / store.LEGACY).exists())
        self.assertEqual({p.name for p in (self.catalog / store.TABLE).iterdir()}, set(store.SHARD_NAMES))
        after = migration.entries_from_directory(self.catalog / store.TABLE)
        migration.compare_entries(before, after)
        self.assertEqual(b"".join(after[key][1] for key in sorted(after)), self.raw)
        self.assertEqual(read_table(self.catalog, store.TABLE), self.rows)
        self.assertEqual((self.backup / store.LEGACY).read_bytes(), self.raw)
        self.assertEqual((self.backup / "manifest.json").read_bytes(), manifest)
        self.assertEqual((self.catalog / "manifest.json").read_bytes(), manifest)
        with patch.object(weekly, "ROOT", self.root):
            self.assertEqual(weekly.content_hash(weekly.research_state()), research_before)

    def test_repeated_apply_and_noop_save_do_not_rewrite_lines_or_metadata(self):
        self.migrate()
        before = files(self.root)
        self.assertEqual(self.migrate()["status"], "already_sharded")
        self.assertEqual(files(self.root), before)
        payload, metadata = load_catalog(self.catalog)
        result = save_catalog(self.catalog, payload, metadata)
        self.assertEqual(result, self.metadata)
        self.assertEqual((self.catalog / "manifest.json").read_bytes(), before["data/catalog/manifest.json"])
        for name in store.SHARD_NAMES:
            self.assertEqual((self.catalog / store.TABLE / name).read_bytes(), before[f"data/catalog/{store.TABLE}/{name}"])

    def test_normal_writes_follow_existing_layout_never_implicitly_migrate(self):
        write_table(self.catalog, store.TABLE, self.rows)
        self.assertTrue((self.catalog / store.LEGACY).exists())
        self.assertFalse((self.catalog / store.TABLE).exists())
        self.migrate()
        old = files(self.catalog / store.TABLE)
        new = {"source_record_id": "source:new", "lineage": ["source:a"], "unknown": {"nested": [None, False]}}
        write_table(self.catalog, store.TABLE, [*self.rows, new])
        self.assertFalse((self.catalog / store.LEGACY).exists())
        self.assertEqual(read_table(self.catalog, store.TABLE), sorted([*self.rows, new], key=lambda r: r[store.ID]))
        changed = [name for name, value in files(self.catalog / store.TABLE).items() if old[name] != value]
        self.assertEqual(changed, [store.shard_name(new[store.ID])])

    def test_unknown_fields_big_integers_and_lineage_survive_sqlite_fidelity(self):
        self.migrate()
        payload, _ = load_catalog(self.catalog)
        with sqlite3.connect(":memory:") as connection:
            connection.execute("CREATE TABLE source_records (source_record_id TEXT PRIMARY KEY, payload_json TEXT NOT NULL)")
            connection.executemany("INSERT INTO source_records VALUES (?,?)", [(r[store.ID], encode(r)) for r in payload[store.TABLE]])
            build_catalog_fidelity(connection, payload)
            self.assertEqual(audit_catalog_fidelity(connection, payload)["status"], "passed")
            restored = [json.loads(row[0]) for row in connection.execute("SELECT payload_json FROM catalog_restore_source_records ORDER BY ordinal")]
            self.assertEqual(sorted(restored, key=encode), sorted(self.rows, key=encode))

    def test_legacy_and_shards_cannot_silently_shadow_each_other(self):
        (self.catalog / store.TABLE).mkdir()
        before = files(self.root)
        for action in [lambda: read_table(self.catalog, store.TABLE), lambda: self.migrate(),
                       lambda: save_catalog(self.catalog, {store.TABLE: self.rows}, self.metadata)]:
            with self.assertRaisesRegex(ValueError, "mixed_legacy"):
                action()
        self.assertEqual(files(self.root), before)

    def test_missing_entire_nonempty_source_table_cannot_be_read_or_recreated(self):
        for layout in ("legacy", "sharded"):
            with self.subTest(layout=layout):
                if layout == "sharded": self.migrate()
                source = self.catalog / (store.LEGACY if layout == "legacy" else store.TABLE)
                moved = self.root / f"removed-{layout}"
                source.rename(moved)
                before = files(self.catalog)
                for action in [lambda: read_table(self.catalog, store.TABLE),
                               lambda: write_table(self.catalog, store.TABLE, []),
                               lambda: save_catalog(self.catalog, {}, self.metadata)]:
                    with self.assertRaisesRegex(ValueError, "nonempty_source_table_missing"): action()
                self.assertEqual(files(self.catalog), before)
                moved.rename(source)

    def test_absent_initial_and_explicit_empty_sources_remain_supported(self):
        initial = self.root / "initial"
        initial.mkdir()
        self.assertEqual(read_table(initial, store.TABLE), [])
        write_table(initial, store.TABLE, self.rows)
        self.assertEqual(read_table(initial, store.TABLE), self.rows)
        metadata = copy.deepcopy(self.metadata)
        metadata["table_hashes"][store.TABLE] = fingerprint([])
        metadata["catalog_hash"] = fingerprint(metadata["table_hashes"])
        (self.catalog / "manifest.json").write_text(encode(metadata) + "\n")
        (self.catalog / store.LEGACY).unlink()
        self.assertEqual(read_table(self.catalog, store.TABLE), [])
        write_table(self.catalog, store.TABLE, [])
        self.assertEqual((self.catalog / store.LEGACY).read_bytes(), b"")

    def test_missing_extra_nonregular_and_misplaced_shards_are_rejected(self):
        self.migrate()
        directory = self.catalog / store.TABLE
        for case in ["missing", "extra", "directory", "symlink", "misplaced"]:
            with self.subTest(case=case):
                name = store.shard_name("source:a")
                target = directory / name
                raw = target.read_bytes()
                extra = directory / "extra.jsonl"
                other = directory / next(n for n in store.SHARD_NAMES if n != name and not (directory / n).read_bytes())
                if case == "missing": target.unlink()
                elif case == "extra": extra.write_text("")
                elif case == "directory": target.unlink(); target.mkdir()
                elif case == "symlink": target.unlink(); target.symlink_to(self.backup / store.LEGACY)
                else: target.write_bytes(b""); other.write_bytes(raw)
                with self.assertRaises(ValueError): read_table(self.catalog, store.TABLE)
                if case == "extra": extra.unlink()
                elif case == "directory": target.rmdir()
                elif case == "symlink": target.unlink()
                elif case == "misplaced": other.write_bytes(b"")
                target.write_bytes(raw)

    def test_duplicate_ids_keys_missing_ids_and_nonfinite_values_rejected(self):
        path = self.catalog / store.LEGACY
        for bad in [self.raw + self.raw.splitlines(keepends=True)[0], b'{"source_record_id":"x","source_record_id":"y"}\n',
                    b'{"name":"missing id"}\n', b'{"source_record_id":"x","value":NaN}\n']:
            with self.subTest(bad=bad[:50]):
                path.write_bytes(bad)
                with self.assertRaises((ValueError, json.JSONDecodeError)): migration.migrate(self.catalog)
                self.assertFalse(self.stage.exists())

    def test_manifest_hash_mismatch_and_unterminated_or_unsorted_legacy_refuse(self):
        path = self.catalog / store.LEGACY
        for bad in [self.raw.replace(b'old-evidence', b'bad-evidence'), self.raw.rstrip(b"\n"),
                    b"".join(reversed(self.raw.splitlines(keepends=True))), b"\n" + self.raw]:
            with self.subTest(bad=bad[:50]):
                path.write_bytes(bad)
                with self.assertRaises(ValueError): self.migrate()
                self.assertFalse(self.stage.exists())

    def test_stage_tampering_fails_before_authority_switch(self):
        original = migration.entries_from_directory
        def tamper(directory):
            target = directory / store.shard_name("source:a")
            target.write_bytes(target.read_bytes().replace(b'old-evidence', b'bad-evidence'))
            return original(directory)
        before = files(self.catalog)
        with patch.object(migration, "entries_from_directory", side_effect=tamper):
            with self.assertRaisesRegex(ValueError, "fields_changed"): self.migrate()
        self.assertEqual(files(self.catalog), before)

    def test_stage_whitespace_rewrite_is_detected_even_when_fields_match(self):
        original = migration.entries_from_directory
        def reformat(directory):
            target = directory / store.shard_name("source:a")
            entries = store.parse_lines(target.read_bytes())
            target.write_bytes(b"".join((encode(row) + "\n").encode() for row, _ in entries))
            return original(directory)
        with patch.object(migration, "entries_from_directory", side_effect=reformat):
            with self.assertRaisesRegex(ValueError, "original_line_bytes_changed"): self.migrate()
        self.assertEqual((self.catalog / store.LEGACY).read_bytes(), self.raw)

    def test_shard_changed_after_its_read_is_rejected_at_snapshot_end(self):
        self.migrate()
        original = store.read_bytes
        target = self.catalog / store.TABLE / store.shard_name("source:a")
        def change(path):
            result = original(path)
            if path.name == "ff.jsonl":
                target.write_bytes(target.read_bytes().replace(b'old-evidence', b'user-change'))
            return result
        with patch.object(store, "read_bytes", side_effect=change):
            with self.assertRaisesRegex(ValueError, "changed_while_reading"): read_table(self.catalog, store.TABLE)

    def test_concurrent_legacy_edit_during_staging_is_not_overwritten(self):
        original = migration.compare_entries
        edited = self.raw.replace(b'old-evidence', b'user-edit')
        def change(*args):
            original(*args)
            (self.catalog / store.LEGACY).write_bytes(edited)
        with patch.object(migration, "compare_entries", side_effect=change):
            with self.assertRaisesRegex(ValueError, "source_changed_before_switch"): self.migrate()
        self.assertEqual((self.catalog / store.LEGACY).read_bytes(), edited)
        self.assertFalse((self.catalog / store.MIGRATION_MARKER).exists())

    def test_switch_failure_restores_original_and_keeps_archive(self):
        original = os.rename
        def fault(source, destination):
            if Path(source) == self.stage / store.TABLE: raise OSError("injected")
            return original(source, destination)
        with patch.object(migration.os, "rename", side_effect=fault):
            with self.assertRaisesRegex(RuntimeError, "legacy_restored"): self.migrate()
        self.assertEqual((self.catalog / store.LEGACY).read_bytes(), self.raw)
        self.assertEqual((self.backup / store.LEGACY).read_bytes(), self.raw)
        self.assertFalse((self.catalog / store.MIGRATION_MARKER).exists())
        self.assertEqual(read_table(self.catalog, store.TABLE), self.rows)

    def test_abrupt_interruption_leaves_recoverable_archive_and_fail_closed_marker(self):
        original = os.rename
        def interrupt(source, destination):
            if Path(source) == self.stage / store.TABLE: raise KeyboardInterrupt()
            return original(source, destination)
        with patch.object(migration.os, "rename", side_effect=interrupt):
            with self.assertRaises(KeyboardInterrupt): self.migrate()
        self.assertEqual((self.backup / store.LEGACY).read_bytes(), self.raw)
        self.assertTrue((self.stage / store.TABLE).is_dir())
        with self.assertRaisesRegex(ValueError, "recovery_required"): read_table(self.catalog, store.TABLE)
        before = files(self.catalog)
        with self.assertRaisesRegex(ValueError, "recovery_required"): save_catalog(self.catalog, {}, self.metadata)
        self.assertEqual(files(self.catalog), before)

    def test_post_switch_user_edit_is_preserved_when_rollback_refuses(self):
        original = migration.entries_from_directory
        def change(directory):
            if directory == self.catalog / store.TABLE:
                target = directory / store.shard_name("source:a")
                target.write_bytes(target.read_bytes().replace(b'old-evidence', b'user-edit'))
            return original(directory)
        with patch.object(migration, "entries_from_directory", side_effect=change):
            with self.assertRaisesRegex(RuntimeError, "explicit_recovery_required"): self.migrate()
        self.assertEqual((self.backup / store.LEGACY).read_bytes(), self.raw)
        self.assertIn(b'user-edit', (self.catalog / store.TABLE / store.shard_name("source:a")).read_bytes())
        with self.assertRaisesRegex(ValueError, "recovery_required"): read_table(self.catalog, store.TABLE)

    def test_cli_default_dryrun_needs_explicit_apply_and_fresh_outputs(self):
        before = files(self.root)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(migration.main(["--catalog", str(self.catalog)]), 0)
        self.assertEqual(files(self.root), before)
        with self.assertRaisesRegex(ValueError, "requires_stage_and_backup"):
            migration.migrate(self.catalog, apply=True)
        self.stage.mkdir()
        with self.assertRaisesRegex(ValueError, "already_exists"): self.migrate()

    def test_editorial_readers_have_identical_order_and_fail_closed(self):
        from generate_v3_editorial import read_table as editorial_read
        from import_legacy_editorial import read_table as legacy_read
        self.migrate()
        for reader in (editorial_read, legacy_read):
            self.assertEqual(reader(self.catalog, store.TABLE), self.rows)
        (self.catalog / store.LEGACY).write_bytes(self.raw)
        for reader in (editorial_read, legacy_read):
            with self.assertRaisesRegex(ValueError, "mixed_legacy"): reader(self.catalog, store.TABLE)

    def test_weekly_exact_paths_backup_rollback_and_user_edit_guard(self):
        self.migrate()
        with patch.object(weekly, "ROOT", self.root):
            planned = weekly.planned_generated_paths({"week": "2026-W38"})
            source_paths = [p for p in planned if p.startswith("data/catalog/source-records")]
            self.assertEqual(set(source_paths), {f"data/catalog/source-records/{name}" for name in store.SHARD_NAMES})
            checkpoint = weekly.checkpoint_generated(source_paths, self.root / "weekly-backup")
            target = self.catalog / store.TABLE / store.shard_name("source:a")
            original = target.read_bytes()
            target.write_bytes(original.replace(b'old-evidence', b'new-evidence'))
            after = weekly.generated_hashes(checkpoint)
            weekly.restore_generated(checkpoint, after)
            self.assertEqual(target.read_bytes(), original)
            target.write_bytes(original.replace(b'old-evidence', b'new-evidence'))
            after = weekly.generated_hashes(checkpoint)
            target.write_bytes(original.replace(b'old-evidence', b'user-edit'))
            with self.assertRaisesRegex(RuntimeError, "changed after verification"):
                weekly.restore_generated(checkpoint, after)
            self.assertIn(b'user-edit', target.read_bytes())


if __name__ == "__main__":
    unittest.main()
