"""Only temporary SQLite fixtures; never package the real research database."""
import copy
import gzip
import hashlib
import json
import os
import sqlite3
import sys
import tempfile
import unittest
import zipfile
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import sqlite_download as module
from sqlite_download import local_sqlite_path, sqlite_export, verify_archive


class SQLiteDownloadTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="sqlite-download-fixture-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.downloads = self.root / "docs/public/downloads"
        self.manifest_path = self.root / "docs/public/api/v1/catalog-manifest.json"
        self.manifest = {"dataset_version": "fixture", "counts": {"works": 2},
                         "downloads": {"migration_report": "/api/v1/migration-report.json"}}
        self.raw = local_sqlite_path(self.root)
        self.archive = self.downloads / "radar.sqlite.zip"

    def export(self, marker="original"):
        with sqlite_export(self.root, self.downloads, self.manifest_path, self.manifest) as connection:
            connection.execute("CREATE TABLE works(work_id TEXT PRIMARY KEY, title TEXT, payload TEXT)")
            connection.executemany("INSERT INTO works VALUES(?,?,?)", [
                ("arxiv:fixture", "π0 世界模型", json.dumps({"marker": marker, "authors": ["O’Neil", "王 强"], "nullable": None}, ensure_ascii=False)),
                ("doi:fixture", "灵巧操作", "Full text retained.\n" * 60000),
            ])
            connection.execute("CREATE VIEW restored AS SELECT * FROM works")
            connection.execute("CREATE VIRTUAL TABLE works_fts USING fts5(title)")
            connection.execute("INSERT INTO works_fts SELECT title FROM works")
        return json.loads(self.manifest_path.read_text())["downloads"]["sqlite_integrity"]

    def final_bytes(self):
        return {p: p.read_bytes() for p in (self.raw, self.archive, self.manifest_path) if p.exists()}

    def recompressed_metadata(self, data):
        return {"encoding": "zip", "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data), "archive_sha256": hashlib.sha256(self.archive.read_bytes()).hexdigest(),
                "archive_bytes": self.archive.stat().st_size}

    def assert_no_temporary_files(self):
        self.assertFalse(list(self.raw.parent.glob(".sqlite-export-*")))
        self.assertFalse(list(self.downloads.glob(".radar.sqlite.zip-*")))
        self.assertFalse(list(self.manifest_path.parent.glob(".catalog-manifest-*")))

    def test_complete_roundtrip_keeps_tables_views_fts_unicode_and_full_text(self):
        original_manifest = copy.deepcopy(self.manifest)
        integrity = self.export()
        with zipfile.ZipFile(self.archive) as archive:
            restored = archive.read("radar.sqlite")
        self.assertEqual(restored, self.raw.read_bytes())
        self.assertEqual(integrity["sha256"], hashlib.sha256(restored).hexdigest())
        self.assertEqual(verify_archive(self.archive, integrity, raw_path=self.raw)["status"], "passed")
        with closing(sqlite3.connect(":memory:")) as database:
            database.deserialize(restored)
            self.assertEqual(database.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(database.execute("SELECT count(*) FROM works").fetchone()[0], 2)
            self.assertEqual(database.execute("SELECT title FROM restored WHERE work_id='arxiv:fixture'").fetchone()[0], "π0 世界模型")
            self.assertEqual(database.execute("SELECT length(payload) FROM works WHERE work_id='doi:fixture'").fetchone()[0], len("Full text retained.\n" * 60000))
            self.assertEqual(database.execute("SELECT count(*) FROM works_fts WHERE works_fts MATCH '\"世界模型\"'").fetchone()[0], 1)
        self.assertEqual(self.manifest, original_manifest)
        self.assertEqual(json.loads(self.manifest_path.read_text())["downloads"]["sqlite"], "/downloads/radar.sqlite.zip")
        self.assertFalse(self.raw.is_relative_to(self.root / "docs/public"))
        self.assertFalse((self.downloads / "radar.sqlite").exists())
        self.assertFalse((self.downloads / "radar.sqlite.gz").exists())
        self.assertEqual(list(self.downloads.iterdir()), [self.archive])
        self.assert_no_temporary_files()

    def test_compression_is_deterministic_without_mtime_or_source_filename(self):
        first = self.export()
        first_bytes = self.final_bytes()
        second = self.export()
        self.assertEqual(first, second)
        self.assertEqual(first_bytes, self.final_bytes())
        self.assertEqual(self.archive.read_bytes()[:4], b"PK\x03\x04")
        with zipfile.ZipFile(self.archive) as archive:
            self.assertEqual(archive.namelist(), ["radar.sqlite"])
            entry = archive.getinfo("radar.sqlite")
            self.assertEqual(entry.date_time, (1980, 1, 1, 0, 0, 0))
            self.assertEqual(entry.external_attr >> 16, 0o100644)
            self.assertEqual(entry.create_system, 3)
            self.assertEqual(entry.compress_type, zipfile.ZIP_DEFLATED)
            self.assertEqual(entry.flag_bits & 0x41, 0)

    def test_old_public_derived_copy_is_removed_only_after_verified_replacement(self):
        self.export("old")
        legacy = self.downloads / "radar.sqlite"
        legacy.write_bytes(self.raw.read_bytes())
        legacy_gzip = self.downloads / "radar.sqlite.gz"
        legacy_gzip.write_bytes(gzip.compress(self.raw.read_bytes(), mtime=0))
        neighbor = self.downloads / "other.sqlite"
        neighbor.write_bytes(b"user-managed-neighbor")
        self.export("new")
        self.assertFalse(legacy.exists())
        self.assertFalse(legacy_gzip.exists())
        self.assertEqual(neighbor.read_bytes(), b"user-managed-neighbor")
        with closing(sqlite3.connect(f"file:{self.raw}?mode=ro", uri=True)) as connection:
            self.assertEqual(json.loads(connection.execute("SELECT payload FROM works WHERE work_id='arxiv:fixture'").fetchone()[0])["marker"], "new")

    def test_sql_build_failure_preserves_all_final_outputs(self):
        self.export()
        before = self.final_bytes()
        with self.assertRaisesRegex(RuntimeError, "fixture-failure"):
            with sqlite_export(self.root, self.downloads, self.manifest_path, self.manifest) as connection:
                connection.execute("CREATE TABLE unfinished(value)")
                raise RuntimeError("fixture-failure")
        self.assertEqual(before, self.final_bytes())
        self.assert_no_temporary_files()

    def test_compression_or_verification_failure_does_not_publish_or_remove_legacy(self):
        self.export()
        legacy = self.downloads / "radar.sqlite"
        legacy.write_bytes(self.raw.read_bytes())
        legacy_gzip = self.downloads / "radar.sqlite.gz"
        gzip_before = gzip.compress(self.raw.read_bytes(), mtime=0)
        legacy_gzip.write_bytes(gzip_before)
        before, legacy_before = self.final_bytes(), legacy.read_bytes()
        for target in ("_compress", "verify_archive"):
            with self.subTest(target=target), patch.object(module, target, side_effect=ValueError("fixture-invalid-archive")):
                with self.assertRaises(ValueError):
                    self.export("new")
            self.assertEqual(before, self.final_bytes())
            self.assertEqual(legacy.read_bytes(), legacy_before)
            self.assertEqual(legacy_gzip.read_bytes(), gzip_before)
            self.assert_no_temporary_files()

    def test_replacement_failure_before_or_after_rename_rolls_back_exact_old_bytes(self):
        self.export()
        legacy = self.downloads / "radar.sqlite"
        legacy.write_bytes(self.raw.read_bytes())
        before, legacy_before = self.final_bytes(), legacy.read_bytes()
        real_replace = os.replace
        for after in (False, True):
            failed = False
            def replace(source, target):
                nonlocal failed
                if Path(target) == self.archive and not failed:
                    failed = True
                    if after:
                        real_replace(source, target)
                    raise OSError("fixture-publication-failure")
                return real_replace(source, target)
            with self.subTest(after=after), patch.object(module.os, "replace", side_effect=replace):
                with self.assertRaises(OSError):
                    self.export("new")
            self.assertEqual(before, self.final_bytes())
            self.assertEqual(legacy.read_bytes(), legacy_before)
            self.assert_no_temporary_files()

    def test_hardlink_unavailable_falls_back_to_safe_backup_copy(self):
        self.export()
        with patch.object(module.os, "link", side_effect=OSError("unsupported")):
            integrity = self.export("new")
        self.assertEqual(verify_archive(self.archive, integrity, raw_path=self.raw)["status"], "passed")
        self.assert_no_temporary_files()

    def test_failed_rollback_keeps_recovery_backup_and_reports_failure(self):
        self.export("old")
        before = self.raw.read_bytes()
        real_replace = os.replace
        failed = False
        def replace(source, target):
            nonlocal failed
            if Path(target) == self.archive and not failed:
                failed = True
                raise OSError("fixture-publish-failure")
            if Path(source).name == "0":
                raise OSError("fixture-cannot-restore-raw")
            return real_replace(source, target)
        with patch.object(module.os, "replace", side_effect=replace):
            with self.assertRaisesRegex(module.PublicationRollbackError, "backups_preserved"):
                self.export("new")
        backups = list(self.raw.parent.glob(".sqlite-export-*/0"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), before)

    def test_crc_or_truncated_stream_rejected_even_if_compressed_hash_is_updated(self):
        integrity = self.export()
        original = self.archive.read_bytes()
        central_crc = original.index(b"PK\x01\x02") + 16
        crc_damage = original[:central_crc] + bytes([original[central_crc] ^ 0xff]) + original[central_crc + 1:]
        for damaged in (original[:-5], crc_damage):
            self.archive.write_bytes(damaged)
            metadata = {**integrity, "archive_bytes":len(damaged), "archive_sha256":hashlib.sha256(damaged).hexdigest()}
            with self.assertRaisesRegex(ValueError, "invalid_zip_stream"):
                verify_archive(self.archive, metadata)

    def test_integrity_requires_matching_compressed_raw_sizes_and_digests(self):
        integrity = self.export()
        for field, value in (("archive_sha256", "0"*64), ("sha256", "0"*64),
                             ("archive_bytes", integrity["archive_bytes"]+1), ("bytes", integrity["bytes"]-1),
                             ("bytes", integrity["bytes"]+1)):
            with self.subTest(field=field,value=value), self.assertRaises(ValueError):
                verify_archive(self.archive, {**integrity,field:value})
        changed = self.raw.parent / "changed.sqlite"
        changed.write_bytes(self.raw.read_bytes() + b"changed")
        with self.assertRaisesRegex(ValueError,"local_raw_mismatch"):
            verify_archive(self.archive, integrity, raw_path=changed)

    def test_zip_requires_one_exact_flat_entry_and_deflate(self):
        self.export()
        raw = self.raw.read_bytes()
        cases = [([],zipfile.ZIP_DEFLATED), (["other.sqlite"],zipfile.ZIP_DEFLATED),
                 (["../radar.sqlite"],zipfile.ZIP_DEFLATED), (["folder/radar.sqlite"],zipfile.ZIP_DEFLATED),
                 (["/radar.sqlite"],zipfile.ZIP_DEFLATED), (["radar.sqlite/"],zipfile.ZIP_DEFLATED),
                 (["radar.sqlite","extra.txt"],zipfile.ZIP_DEFLATED), (["radar.sqlite"],zipfile.ZIP_STORED)]
        for names,compression in cases:
            with self.subTest(names=names,compression=compression):
                with zipfile.ZipFile(self.archive,"w",compression=compression) as archive:
                    for name in names:
                        archive.writestr(name,raw)
                with self.assertRaisesRegex(ValueError,"single_entry_required|invalid_zip_entry"):
                    verify_archive(self.archive,self.recompressed_metadata(raw))

    def test_zip_symlink_and_encrypted_entries_are_rejected_before_read(self):
        self.export()
        raw = self.raw.read_bytes()
        entry = zipfile.ZipInfo("radar.sqlite")
        entry.create_system = 3
        entry.external_attr = 0o120777 << 16
        entry.compress_type = zipfile.ZIP_DEFLATED
        with zipfile.ZipFile(self.archive,"w") as archive:
            archive.writestr(entry,raw)
        with self.assertRaisesRegex(ValueError,"invalid_zip_entry"):
            verify_archive(self.archive,self.recompressed_metadata(raw))
        self.export()
        value = bytearray(self.archive.read_bytes())
        central = value.index(b"PK\x01\x02")
        value[6] |= 1
        value[central + 8] |= 1
        self.archive.write_bytes(value)
        with self.assertRaisesRegex(ValueError,"invalid_zip_entry"):
            verify_archive(self.archive,self.recompressed_metadata(raw))

    def test_failure_removing_old_gzip_restores_both_superseded_derivatives(self):
        self.export("old")
        legacy = self.downloads / "radar.sqlite"
        legacy_gzip = self.downloads / "radar.sqlite.gz"
        legacy.write_bytes(self.raw.read_bytes())
        legacy_gzip.write_bytes(gzip.compress(self.raw.read_bytes(),mtime=0))
        before = {**self.final_bytes(),legacy:legacy.read_bytes(),legacy_gzip:legacy_gzip.read_bytes()}
        original_unlink = Path.unlink
        failed = False
        def unlink(path,*args,**kwargs):
            nonlocal failed
            if path == legacy_gzip and not failed:
                failed = True
                raise OSError("fixture-cannot-remove-old-gzip")
            return original_unlink(path,*args,**kwargs)
        with patch.object(Path,"unlink",unlink), self.assertRaises(OSError):
            self.export("new")
        self.assertEqual(before,{path:path.read_bytes() for path in before})
        self.assert_no_temporary_files()

    def test_unrecognized_old_gzip_is_not_deleted(self):
        self.downloads.mkdir(parents=True)
        old = self.downloads / "radar.sqlite.gz"
        old.write_bytes(gzip.compress(b"not a derived database",mtime=0))
        before = old.read_bytes()
        with self.assertRaisesRegex(ValueError,"legacy_gzip_not_sqlite"):
            self.export()
        self.assertEqual(old.read_bytes(),before)
        self.assertFalse(self.archive.exists())

    def test_non_sqlite_compressed_content_cannot_pass_matching_hashes(self):
        self.downloads.mkdir(parents=True)
        value = b"not a database" * 200
        with zipfile.ZipFile(self.archive,"w",compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("radar.sqlite",value)
        with self.assertRaisesRegex(ValueError,"invalid_sqlite_header"):
            verify_archive(self.archive,self.recompressed_metadata(value))

    def test_contract_rejects_missing_unknown_negative_bool_or_wrong_encoding_fields(self):
        integrity = self.export()
        for extra in ({"encoding":"gzip"},{"bytes":True},{"archive_bytes":-1},{"sha256":"not-hash"},{"filename":"untrusted"}):
            with self.subTest(extra=extra), self.assertRaisesRegex(ValueError,"integrity_contract_invalid"):
                verify_archive(self.archive,{**integrity,**extra})
        incomplete = dict(integrity);incomplete.pop("bytes")
        with self.assertRaises(ValueError):verify_archive(self.archive,incomplete)

    def test_unknown_or_symlink_legacy_target_is_never_removed(self):
        self.downloads.mkdir(parents=True)
        legacy = self.downloads / "radar.sqlite"
        legacy.write_bytes(b"not a derived sqlite export")
        with self.assertRaisesRegex(ValueError,"legacy_target_not_sqlite"):
            self.export()
        self.assertEqual(legacy.read_bytes(),b"not a derived sqlite export")
        legacy.unlink()
        original = self.root / "outside-user-file"
        original.write_bytes(b"untouched")
        legacy.symlink_to(original)
        with self.assertRaisesRegex(ValueError,"symlink"):
            self.export()
        self.assertEqual(original.read_bytes(),b"untouched")

    def test_nonpublic_raw_is_derived_from_caller_root_and_unsafe_paths_fail_closed(self):
        self.assertEqual(self.raw,self.root / ".research/derived/radar.sqlite")
        with self.assertRaisesRegex(ValueError,"paths_overlap"):
            with sqlite_export(self.root,self.raw.parent,self.manifest_path,self.manifest):pass
        with self.assertRaisesRegex(ValueError,"outside_root"):
            with sqlite_export(self.root,self.root.parent / "foreign-downloads",self.manifest_path,self.manifest):pass
        research = self.root / ".research"
        research.symlink_to(self.root / "other")
        with self.assertRaisesRegex(ValueError,"symlink"):
            self.export()

    def test_verify_archive_is_read_only_and_needs_no_raw_copy(self):
        integrity = self.export()
        before = self.final_bytes()
        verify_archive(self.archive,integrity)
        verify_archive(self.archive,integrity,raw_path=self.raw)
        self.assertEqual(before,self.final_bytes())
        self.assert_no_temporary_files()


if __name__ == "__main__":
    unittest.main()
