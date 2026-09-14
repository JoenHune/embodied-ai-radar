"""Small standard-gzip fixtures only; never build or alter the real index."""
import contextlib
import gzip
import io
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import optimize_pagefind_gzip as optimizer


class PagefindGzipTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name).resolve()
        self.root, self.cache = self.base / "pagefind", self.base / "cache"
        self.root.mkdir()
        (self.root / "pagefind-entry.json").write_text(json.dumps({"version": "1.5.2", "languages": {"zh": {"hash": "zh_abcdef", "page_count": 2}}}))
        self.raw = (b"robot world model repeated observation\x00\xff" * 80)

    def tearDown(self):
        self.temporary.cleanup()

    def asset(self, name="index/zh_abcdef.pf_index", raw=None, level=1):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(gzip.compress(self.raw if raw is None else raw, compresslevel=level, mtime=1234))
        return path

    def test_roundtrip_all_asset_kinds_preserves_filenames_and_nonassets(self):
        paths = [self.asset(), self.asset("pagefind.zh_abcdef.pf_meta"), self.asset("wasm.unknown.pagefind")]
        untouched = {"pagefind.js": b"user javascript", "notes.txt": b"user notes", "user/other.pf_index": b"not a target", "index/user_notes.pf_index": b"not a hashed Pagefind name", "fragment/data.pf_fragment": b"not a target"}
        for name, content in untouched.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        before = {path.relative_to(self.root).as_posix(): path.read_bytes() for path in paths}
        marker = (self.root / "pagefind-entry.json").read_bytes()
        report = optimizer.optimize_directory(self.root, self.cache)
        self.assertEqual(report["asset_count"], 3)
        self.assertTrue(report["all_decoded_bytes_identical"])
        self.assertGreaterEqual(report["saved_bytes"], 0)
        self.assertEqual((self.root / "pagefind-entry.json").read_bytes(), marker)
        for row in report["files"]:
            path = self.root / row["path"]
            self.assertEqual(gzip.decompress(path.read_bytes()), self.raw)
            self.assertLessEqual(len(path.read_bytes()), len(before[row["path"]]))
            self.assertEqual(row["decoded_sha256"], optimizer.sha256(self.raw))
            self.assertEqual(row["after_sha256"], optimizer.sha256(path.read_bytes()))
        for name, content in untouched.items():
            self.assertEqual((self.root / name).read_bytes(), content)

    def test_original_wins_if_new_compressors_are_larger(self):
        path = self.asset(level=9)
        original = path.read_bytes()
        larger_valid_gzip = original + gzip.compress(b"", mtime=0)
        with patch.object(optimizer.gzip, "compress", return_value=larger_valid_gzip), patch.object(optimizer.zopfli.gzip, "compress", return_value=larger_valid_gzip):
            report = optimizer.optimize_directory(self.root, self.cache)
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(report["changed_assets"], 0)
        self.assertEqual(report["files"][0]["algorithm"], "original")

    def test_second_run_uses_validated_cache_and_is_byte_idempotent(self):
        path = self.asset()
        first = optimizer.optimize_directory(self.root, self.cache)
        optimized = path.read_bytes()
        with patch.object(optimizer.zopfli.gzip, "compress", side_effect=AssertionError("cache should avoid recompression")):
            second = optimizer.optimize_directory(self.root, self.cache)
        self.assertEqual(second["cache_hits"], 1)
        self.assertEqual(second["changed_assets"], 0)
        self.assertEqual(second["saved_bytes"], 0)
        self.assertEqual(path.read_bytes(), optimized)
        self.assertEqual(first["files"][0]["cache_key"], second["files"][0]["cache_key"])

    def test_same_decoded_payload_reuses_cache_across_wrapper_timestamps(self):
        path = self.asset()
        first = optimizer.optimize_directory(self.root, self.cache)
        path.write_bytes(gzip.compress(self.raw, compresslevel=1, mtime=5555))
        with patch.object(optimizer.zopfli.gzip, "compress", side_effect=AssertionError("decoded payload cache should be reused")):
            second = optimizer.optimize_directory(self.root, self.cache)
        self.assertEqual(second["cache_hits"], 1)
        self.assertEqual(first["files"][0]["cache_key"], second["files"][0]["cache_key"])
        self.assertEqual(gzip.decompress(path.read_bytes()), self.raw)

    def test_corrupt_cache_is_recomputed_without_changing_decoded_bytes(self):
        path = self.asset()
        first = optimizer.optimize_directory(self.root, self.cache)
        cached = self.cache / (first["files"][0]["cache_key"] + ".gz")
        cached.write_bytes(b"corrupt cache")
        second = optimizer.optimize_directory(self.root, self.cache)
        self.assertEqual(second["invalid_cache_entries"], 1)
        self.assertEqual(second["cache_hits"], 0)
        self.assertEqual(gzip.decompress(cached.read_bytes()), self.raw)
        self.assertEqual(gzip.decompress(path.read_bytes()), self.raw)

    def test_valid_gzip_cache_with_wrong_plaintext_is_rejected(self):
        path = self.asset()
        first = optimizer.optimize_directory(self.root, self.cache)
        key = first["files"][0]["cache_key"]
        wrong = gzip.compress(b"different payload", mtime=0)
        (self.cache / (key + ".gz")).write_bytes(wrong)
        metadata = self.cache / (key + ".json")
        info = json.loads(metadata.read_text())
        info.update(compressed_sha256=optimizer.sha256(wrong), compressed_bytes=len(wrong))
        metadata.write_text(json.dumps(info))
        result = optimizer.optimize_directory(self.root, self.cache)
        self.assertEqual(result["invalid_cache_entries"], 1)
        self.assertEqual(gzip.decompress(path.read_bytes()), self.raw)

    def test_corrupt_cache_metadata_is_recomputed(self):
        self.asset()
        first = optimizer.optimize_directory(self.root, self.cache)
        key = first["files"][0]["cache_key"]
        (self.cache / (key + ".json")).write_text("not json")
        self.assertEqual(optimizer.optimize_directory(self.root, self.cache)["invalid_cache_entries"], 1)

    def test_valid_json_with_wrong_cache_metadata_shape_is_recomputed(self):
        self.asset()
        first = optimizer.optimize_directory(self.root, self.cache)
        key = first["files"][0]["cache_key"]
        (self.cache / (key + ".json")).write_text("[]")
        self.assertEqual(optimizer.optimize_directory(self.root, self.cache)["invalid_cache_entries"], 1)

    def test_non_gzip_asset_fails_preflight_before_any_replacement(self):
        good = self.asset("index/zh_aaaaaa.pf_index")
        original = good.read_bytes()
        bad = self.root / "index/zh_bbbbbb.pf_index"
        bad.write_bytes(b"not gzip")
        with self.assertRaises(ValueError):
            optimizer.optimize_directory(self.root, self.cache)
        self.assertEqual(good.read_bytes(), original)
        self.assertEqual(bad.read_bytes(), b"not gzip")
        self.assertFalse(self.cache.exists())

    def test_bad_gzip_crc_is_rejected(self):
        path = self.asset()
        path.write_bytes(path.read_bytes()[:-3])
        with self.assertRaises(ValueError):
            optimizer.optimize_directory(self.root, self.cache)

    def test_directory_without_real_pagefind_marker_is_rejected(self):
        self.asset()
        (self.root / "pagefind-entry.json").unlink()
        with self.assertRaises(ValueError):
            optimizer.optimize_directory(self.root, self.cache)
        (self.root / "pagefind-entry.json").write_text("{}")
        with self.assertRaises(ValueError):
            optimizer.optimize_directory(self.root, self.cache)

    def test_symlink_root_asset_and_cache_are_rejected(self):
        path = self.asset()
        root_link = self.base / "root-link"
        root_link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            optimizer.optimize_directory(root_link, self.cache)
        linked = self.root / "index/zh_link.pf_index"
        linked.symlink_to(path)
        with self.assertRaises(ValueError):
            optimizer.optimize_directory(self.root, self.cache)
        linked.unlink()
        real_cache = self.base / "actual-cache"
        real_cache.mkdir()
        self.cache.symlink_to(real_cache, target_is_directory=True)
        with self.assertRaises(ValueError):
            optimizer.optimize_directory(self.root, self.cache)

    def test_symlink_user_file_is_not_followed(self):
        self.asset()
        outside = self.base / "outside"
        outside.write_bytes(b"private user data")
        (self.root / "notes.txt").symlink_to(outside)
        with self.assertRaises(ValueError):
            optimizer.optimize_directory(self.root, self.cache)
        self.assertEqual(outside.read_bytes(), b"private user data")

    def test_invalid_compressor_output_never_replaces_asset(self):
        path = self.asset()
        before = path.read_bytes()
        with patch.object(optimizer.zopfli.gzip, "compress", return_value=gzip.compress(b"wrong plaintext", mtime=0)):
            with self.assertRaises(RuntimeError):
                optimizer.optimize_directory(self.root, self.cache)
        self.assertEqual(path.read_bytes(), before)

    def test_atomic_replacement_keeps_mode(self):
        path = self.asset(level=0)
        path.chmod(0o640)
        result = optimizer.optimize_directory(self.root, self.cache)
        self.assertEqual(result["changed_assets"], 1)
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o640)

    def test_atomic_failure_preserves_original_and_cleans_exact_temp(self):
        path = self.asset(level=0)
        before = path.read_bytes()
        original_replace = os.replace
        def fail_asset(source, target):
            if Path(target) == path:
                raise OSError("fixture replacement failure")
            return original_replace(source, target)
        with patch.object(optimizer.os, "replace", side_effect=fail_asset):
            with self.assertRaises(OSError):
                optimizer.optimize_directory(self.root, self.cache)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(list(path.parent.glob("*.tmp")), [])

    def test_cli_requires_explicit_directory_and_emits_only_audit_metadata(self):
        self.asset(raw=b"RAW_SECRET_SENTINEL_DO_NOT_PRINT" * 30)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            optimizer.main([])
        with contextlib.redirect_stdout(io.StringIO()) as output:
            code = optimizer.main(["--directory", str(self.root), "--cache-directory", str(self.cache)])
        self.assertEqual(code, 0)
        report = json.loads(output.getvalue())
        self.assertEqual(report["status"], "ok")
        self.assertNotIn("RAW_SECRET_SENTINEL_DO_NOT_PRINT", output.getvalue())
        self.assertEqual(report["spec"]["zopfli_numiterations"], 12)

    def test_cache_keys_include_algorithm_version_and_parameters(self):
        spec = optimizer.algorithm_spec()
        digest = optimizer.sha256(self.raw)
        base = optimizer.cache_key(digest, spec)
        self.assertNotEqual(base, optimizer.cache_key(digest, {**spec, "zopfli_numiterations": 6}))
        self.assertNotEqual(base, optimizer.cache_key(digest, {**spec, "zopfli_version": "future"}))
        self.assertNotEqual(base, optimizer.cache_key(optimizer.sha256(b"other"), spec))

    def test_cache_cannot_be_written_inside_pagefind(self):
        path = self.asset()
        original = path.read_bytes()
        with self.assertRaises(ValueError):
            optimizer.optimize_directory(self.root, self.root / "cache")
        self.assertEqual(path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
