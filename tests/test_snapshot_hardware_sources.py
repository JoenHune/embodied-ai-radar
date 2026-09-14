"""Offline temporary fixtures only; never read the real acquisition log."""
import json
import io
import os
import socket
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import snapshot_hardware_sources as hs

STAMP = "2026-09-14T10:00:00Z"
SNAPSHOT_AT = "2026-09-15T10:00:00Z"
DICTIONARY = {"schema_version": "1", "version": "1", "entries": [
    {"dictionary_id": "model:franka-panda", "name": "Franka Panda", "category": "robot_arm",
     "identity_level": "model_specified", "aliases": ["Franka Panda"], "hardware_ids": [],
     "source_urls": ["https://example.org/fixture"]}]}


def jsonl(path, rows):
    path.write_text("".join(hs.encode(row) + "\n" for row in rows))


def tree(directory):
    return {str(path.relative_to(directory)): (path.read_bytes(), path.stat().st_mtime_ns)
            for path in directory.rglob("*") if path.is_file()}


class HardwareSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.cache = self.root / "cache"
        (self.cache / "objects").mkdir(parents=True)
        self.observations = self.cache / "observations.jsonl"
        self.observations.touch()
        self.published = self.root / "published"
        self.published.mkdir()
        jsonl(self.published / "source-observations.jsonl", [])
        jsonl(self.published / "source-scans.jsonl", [])
        self.rows = []
        self.canonical_ids = {}
        self.network = patch.object(socket, "socket", side_effect=AssertionError("offline test: no network"))
        self.network.start()
        self.addCleanup(self.network.stop)
        self.collector = patch("collect_hardware_sources.Collector.__init__", side_effect=AssertionError("never instantiate Collector"))
        self.collector.start()
        self.addCleanup(self.collector.stop)
        self.mutator = patch("refresh_hardware_source_scans.prepare_private_cache", side_effect=AssertionError("never mutate cache"))
        self.mutator.start()
        self.addCleanup(self.mutator.stop)

    def seed(self, *, suffix="", aid="2407.02648", stamp=STAMP, **changes):
        raw = ('<html><meta name="citation_arxiv_id" content="' + aid + 'v1">'
               '<article><section id="S1">PRIVATE_RAW_DOCUMENT ' + suffix + '</section></article></html>').encode()
        blocks = [{"section_id": "S1", "section_title": "PRIVATE_SECTION_TITLE",
                   "text": ("PRIVATE_BODY_PREFIX franka panda PRIVATE_BODY_SUFFIX " + suffix) * 40}]
        body = "\n\n".join(block["text"] for block in blocks).encode()
        raw_hash, body_hash = hs.sha256(raw), hs.sha256(body)
        raw_path = self.cache / "objects" / (raw_hash + ".html")
        blocks_path = self.cache / "objects" / (body_hash + ".blocks.json")
        body_path = self.cache / "objects" / (body_hash + ".txt")
        raw_path.write_bytes(raw)
        blocks_path.write_text(json.dumps(blocks))
        body_path.write_bytes(body)
        row = {"work_id": "arxiv:" + aid, "arxiv_id": aid, "version": "v1", "status": "full_text_available",
               "source_url": "https://arxiv.org/html/" + aid + "v1", "effective_url": "https://arxiv.org/html/" + aid + "v1",
               "observed_at": stamp, "parser_version": hs.PARSER_VERSION,
               "raw_sha256": raw_hash, "text_sha256": body_hash, "cache_ref": str(raw_path),
               "blocks_ref": str(blocks_path), "body_cache_ref": str(body_path),
               "observation_id": "hardware-source:" + hs.sha256((aid + stamp + suffix).encode())[:32],
               "transport_complete": True, "body_characters": len(body), "section_count": 1,
               "http_status": 200, "thresholds": {"min_body_characters": 1500, "min_sections": 1},
               "private_nested": {"secret": "PRIVATE_NESTED_SECRET"}, **changes}
        self.rows.append(row)
        self.canonical_ids[row["work_id"]] = aid
        jsonl(self.observations, self.rows)
        return row

    def publish(self, rows, scans=None):
        jsonl(self.published / "source-observations.jsonl", [hs.project(row, self.canonical_ids) for row in rows])
        jsonl(self.published / "source-scans.jsonl", scans or [])

    def stage(self, name="staged", dictionary=DICTIONARY):
        return hs.stage_snapshot(cache=self.cache, observations=self.observations,
                                 published_dir=self.published, dictionary=dictionary,
                                 staging_dir=self.root / name, snapshot_at=SNAPSHOT_AT, canonical_ids=self.canonical_ids)

    def read(self, name):
        return hs.parse_jsonl((self.root / "staged" / name).read_bytes())[0]

    def test_new_sources_keep_published_history_offline_and_never_expose_body(self):
        old = self.seed()
        old_scan = hs.build_scan(old, hs.verify_cache(self.cache, old), DICTIONARY, STAMP, self.canonical_ids)
        self.publish([old], [old_scan])
        current = self.seed(aid="2407.02649", suffix="NEW_BODY")
        private_before, public_before = tree(self.cache), tree(self.published)
        result = self.stage()
        self.assertTrue(result["ready_for_review"])
        self.assertEqual(result["new_observations"], 1)
        self.assertEqual(result["network_requests"], 0)
        self.assertEqual(tree(self.cache), private_before)
        self.assertEqual(tree(self.published), public_before)
        self.assertEqual([row["observation_id"] for row in self.read("source-observations.jsonl")],
                         [old["observation_id"], current["observation_id"]])
        scans = self.read("source-scans.jsonl")
        self.assertEqual(scans[0], old_scan)
        self.assertEqual(scans[1]["matches"][0]["term"], "franka panda")
        self.assertEqual(scans[1]["matches"][0]["section"], "S1")
        for path in (self.root / "staged").iterdir():
            content = path.read_text()
            for secret in ("PRIVATE_", "NEW_BODY", str(self.root), "cache_ref", "blocks_ref", "excerpt"):
                self.assertNotIn(secret, content, (path.name, secret))

    def test_repeat_in_new_directory_is_byte_identical_and_existing_output_refused(self):
        self.seed()
        self.stage()
        original = {path.name: path.read_bytes() for path in (self.root / "staged").iterdir()}
        self.stage("repeat")
        self.assertEqual(original, {path.name: path.read_bytes() for path in (self.root / "repeat").iterdir()})
        with self.assertRaisesRegex(hs.SnapshotError, "must_be_new"):
            self.stage()
        self.assertEqual(original, {path.name: path.read_bytes() for path in (self.root / "staged").iterdir()})

    def test_changed_dictionary_retains_old_scans_then_replay_adds_no_duplicate(self):
        row = self.seed()
        old = hs.build_scan(row, hs.verify_cache(self.cache, row), DICTIONARY, STAMP, self.canonical_ids)
        self.publish([row], [old])
        new_dictionary = {**DICTIONARY, "version": "2"}
        self.stage(dictionary=new_dictionary)
        scans = self.read("source-scans.jsonl")
        self.assertEqual(len(scans), 2)
        self.assertEqual(scans[0], old)
        self.publish([row], scans)
        self.stage("replayed", dictionary=new_dictionary)
        self.assertEqual(hs.parse_jsonl((self.root / "replayed/source-scans.jsonl").read_bytes())[0], scans)

    def test_log_exact_duplicates_deduplicate_but_conflicts_fail(self):
        row = self.seed()
        jsonl(self.observations, [row, row])
        self.assertEqual(self.stage()["observations_after_validation"], 1)
        jsonl(self.observations, [row, {**row, "status": "unavailable"}])
        with self.assertRaisesRegex(hs.SnapshotError, "id_conflict"):
            self.stage("conflicting")
        self.assertFalse((self.root / "conflicting").exists())

    def test_unfinished_final_line_tolerated_but_corrupt_complete_or_internal_line_not(self):
        self.seed()
        original = self.observations.read_bytes()
        for index, suffix in enumerate((b'{"work_id":"arxiv:24', b'{"x":tru', b'{"x":1e', b'{"x":"\xe4\xb8')):
            with self.subTest(suffix=suffix):
                self.observations.write_bytes(original + suffix)
                self.assertTrue(self.stage(f"tail{index}")["incomplete_tail_ignored"])
        for index, suffix in enumerate((b'{"x":\n', b'{"x":nope', b'garbage', b'{"x":1,}\n', b'{"x":\n{}\n')):
            with self.subTest(suffix=suffix):
                self.observations.write_bytes(original + suffix)
                with self.assertRaisesRegex(hs.SnapshotError, "log_corrupt"):
                    self.stage(f"bad{index}")
                self.assertFalse((self.root / f"bad{index}").exists())

    def test_semantic_corruption_is_never_treated_as_incomplete_tail(self):
        for suffix in (b'{"x":1,"x":2}', b'{"x":NaN}', b'[]', b'null'):
            with self.subTest(suffix=suffix):
                self.observations.write_bytes(suffix)
                with self.assertRaises(hs.SnapshotError):
                    self.stage()

    def test_valid_unterminated_last_object_is_accepted(self):
        self.seed()
        self.observations.write_bytes(self.observations.read_bytes().rstrip(b"\n"))
        self.assertFalse(self.stage()["incomplete_tail_ignored"])

    def test_snapshot_reads_log_once_and_does_not_chase_concurrent_append(self):
        first = self.seed()
        original = self.observations.read_bytes()
        newer = {**first, "observation_id": "hardware-source:" + "b" * 32, "observed_at": SNAPSHOT_AT}
        append = (hs.encode(newer) + "\n").encode()
        real_pread, log_reads = os.pread, []
        expected_inode = self.observations.stat().st_ino
        def reading(fd, size, offset):
            if os.fstat(fd).st_ino == expected_inode:
                log_reads.append((size, offset))
                with self.observations.open("ab") as handle:
                    handle.write(append)
            return real_pread(fd, size, offset)
        with patch.object(hs.os, "pread", side_effect=reading):
            result = self.stage()
        self.assertEqual(log_reads, [(len(original), 0)])
        self.assertEqual(result["log_prefix_sha256"], hs.sha256(original))
        self.assertEqual(result["observations_after_validation"], 1)
        self.assertEqual(self.observations.read_bytes(), original + append)

    def test_log_truncation_or_replacement_is_rejected(self):
        self.seed()
        real_pread = os.pread
        expected_inode = self.observations.stat().st_ino
        def reading(fd, size, offset):
            if os.fstat(fd).st_ino == expected_inode:
                self.observations.write_bytes(b"")
            return real_pread(fd, size, offset)
        with patch.object(hs.os, "pread", side_effect=reading), self.assertRaisesRegex(hs.SnapshotError, "replaced_or_truncated"):
            self.stage()
        self.assertFalse((self.root / "staged").exists())

    def test_published_missing_id_binding_mismatch_and_duplicate_fail_before_staging(self):
        row = self.seed()
        original = hs.project(row, self.canonical_ids)
        scenarios = ([], [{**row, "body_characters": 123}], [row])
        for index, log in enumerate(scenarios):
            with self.subTest(index=index):
                jsonl(self.published / "source-observations.jsonl", [original, original] if index == 2 else [original])
                jsonl(self.observations, log)
                with self.assertRaises(hs.SnapshotError):
                    self.stage(f"binding{index}")
                self.assertFalse((self.root / f"binding{index}").exists())

    def test_latest_old_parser_is_pending_without_fallback_or_public_outputs(self):
        older = self.seed()
        self.publish([older])
        self.seed(stamp=SNAPSHOT_AT, suffix="NEWER", parser_version="arxiv-html-body-v1")
        result = self.stage()
        self.assertFalse(result["ready_for_review"])
        self.assertEqual(self.read("pending-refresh.jsonl")[0]["reasons"], ["parser_refresh_required"])
        self.assertEqual({path.name for path in (self.root / "staged").iterdir()},
                         {"snapshot-manifest.json", "pending-refresh.jsonl"})

    def test_full_transport_markers_are_pending_even_with_conflicting_complete_flag(self):
        for index, marker in enumerate(({"transport_complete": False}, {"transport_truncated": True},
                                        {"curl_exit_code": 18}, {"transport_returncode": 28},
                                        {"transport_verification": "incomplete"}, {"truncated": True},
                                        {"error": "curl_transport_error:18 PRIVATE_ERROR_PATH"})):
            with self.subTest(marker=marker):
                self.rows = []
                self.seed(status="full_text_available", **marker)
                result = self.stage(f"transport{index}")
                self.assertFalse(result["ready_for_review"])
                pending = hs.parse_jsonl((self.root / f"transport{index}/pending-refresh.jsonl").read_bytes())[0]
                self.assertIn("transport_reclassification_required", pending[0]["reasons"])

    def test_historical_old_parser_retained_if_superseded_by_valid_latest(self):
        old = self.seed(parser_version="arxiv-html-body-v1")
        self.publish([old])
        current = self.seed(stamp=SNAPSHOT_AT, suffix="NEW")
        self.assertTrue(self.stage()["ready_for_review"])
        self.assertEqual(self.read("source-observations.jsonl")[0]["parser_version"], "arxiv-html-body-v1")
        self.assertEqual(self.read("source-scans.jsonl")[0]["content_hash"], current["text_sha256"])

    def test_same_timestamp_uses_append_order_latest_and_does_not_scan_older(self):
        self.seed(parser_version="arxiv-html-body-v1")
        current = self.seed(suffix="CURRENT")
        self.assertTrue(self.stage()["ready_for_review"])
        self.assertEqual(len(self.read("source-scans.jsonl")), 1)
        self.assertEqual(self.read("source-scans.jsonl")[0]["content_hash"], current["text_sha256"])

    def test_raw_blocks_and_body_file_mismatches_produce_safe_pending_reason(self):
        for index, (key, replacement, reason) in enumerate((
                ("cache_ref", b"PRIVATE_TAMPERED_RAW", "cached_raw_hash_mismatch"),
                ("blocks_ref", b'[{"section_id":"S1","text":"PRIVATE_TAMPERED_BLOCK"}]', "cached_body_hash_mismatch"),
                ("body_cache_ref", b"PRIVATE_TAMPERED_BODY", "cached_body_file_hash_mismatch"))):
            with self.subTest(key=key):
                self.rows = []
                row = self.seed(suffix=str(index))
                Path(row[key]).write_bytes(replacement)
                self.assertFalse(self.stage(f"hash{index}")["ready_for_review"])
                pending = hs.parse_jsonl((self.root / f"hash{index}/pending-refresh.jsonl").read_bytes())[0]
                self.assertIn(reason, pending[0]["reasons"])
                self.assertNotIn("PRIVATE_", hs.encode(pending))

    def test_external_final_and_parent_symlinks_are_not_read(self):
        row = self.seed()
        outside = self.root / "outside.txt"
        outside.write_bytes(b"PRIVATE_OUTSIDE")
        inside_link = self.cache / "objects/inside-link"
        inside_link.symlink_to(row["cache_ref"])
        outside_link = self.cache / "objects/outside-link"
        outside_link.symlink_to(outside)
        broken_link = self.cache / "objects/broken-link"
        broken_link.symlink_to(self.root / "absent")
        real_dir = self.cache / "objects/real"
        real_dir.mkdir()
        (real_dir / "raw").write_bytes(b"PRIVATE_SYMLINK_PARENT")
        parent_link = self.cache / "objects/parent-link"
        parent_link.symlink_to(real_dir, target_is_directory=True)
        for path in (outside, inside_link, outside_link, broken_link, parent_link / "raw"):
            with self.subTest(path=path.name), self.assertRaises(hs.SnapshotError):
                hs.read_object(self.cache, str(path))

    def test_missing_body_cache_is_pending_not_silently_scanned(self):
        self.seed(body_cache_ref=None)
        self.assertFalse(self.stage()["ready_for_review"])
        self.assertEqual(self.read("pending-refresh.jsonl")[0]["reasons"], ["cached_object_reference_missing"])

    def test_new_unavailable_record_without_cache_is_metadata_only_and_does_not_retry(self):
        self.seed(status="unavailable", raw_sha256=None, text_sha256=None, cache_ref=None,
                  blocks_ref=None, body_cache_ref=None, error="PRIVATE_ERROR_PATH", http_status=503,
                  parser_version="arxiv-html-body-v1", transport_complete=False)
        self.assertTrue(self.stage()["ready_for_review"])
        self.assertEqual(self.read("source-scans.jsonl"), [])
        self.assertEqual(self.read("source-observations.jsonl")[0]["error"], "http_503")

    def test_nested_metadata_and_typed_field_injection_fail_without_output(self):
        for index, changes in enumerate(({"thresholds": {"private": "PRIVATE_TEXT"}},
                                         {"excluded_sections": ["PRIVATE_TEXT"]},
                                         {"body_characters": "PRIVATE_TEXT"},
                                         {"source_url": "https://arxiv.org/html/2407.02648v1?secret=PRIVATE_TEXT"},
                                         {"parser_version": "PRIVATE_TEXT"},
                                         {"transport_complete": "false"})):
            self.rows = []
            self.seed(**changes)
            with self.subTest(changes=changes), self.assertRaises(hs.SnapshotError):
                self.stage(f"invalid{index}")
            self.assertFalse((self.root / f"invalid{index}").exists())

    def test_existing_scan_excerpt_or_conflicting_duplicate_rejected(self):
        row = self.seed()
        scan = hs.build_scan(row, hs.verify_cache(self.cache, row), DICTIONARY, STAMP, self.canonical_ids)
        bad = {**scan, "matches": [{**scan["matches"][0], "excerpt": "PRIVATE_TEXT"}]}
        self.publish([row], [bad])
        with self.assertRaisesRegex(hs.SnapshotError, "not_allowlisted"):
            self.stage()
        self.publish([row], [scan, {**scan, "matches": []}])
        with self.assertRaisesRegex(hs.SnapshotError, "key_conflict"):
            self.stage()

    def test_output_must_be_new_private_and_not_overlap_sources(self):
        self.seed()
        for path in (self.cache / "nested", self.published / "nested", hs.ROOT / "data/hardware-review/not-created-by-test",
                     hs.ROOT / "scripts/not-created-by-test", Path("relative-stage")):
            with self.subTest(path=path), self.assertRaises(hs.SnapshotError):
                hs.stage_snapshot(cache=self.cache, observations=self.observations, published_dir=self.published,
                                  dictionary=DICTIONARY, staging_dir=path, snapshot_at=SNAPSHOT_AT, canonical_ids=self.canonical_ids)

    def test_cache_file_changed_during_read_is_rejected(self):
        row = self.seed()
        target = Path(row["cache_ref"])
        expected_inode = target.stat().st_ino
        real_pread = os.pread
        def reading(fd, size, offset):
            result = real_pread(fd, size, offset)
            if os.fstat(fd).st_ino == expected_inode:
                target.write_bytes(b"PRIVATE_REPLACEMENT_WITH_CHANGED_SIZE")
            return result
        with patch.object(hs.os, "pread", side_effect=reading), self.assertRaisesRegex(hs.SnapshotError, "changed_during_read"):
            hs.read_object(self.cache, str(target))

    def test_scan_history_without_published_source_binding_is_rejected(self):
        row = self.seed()
        scan = hs.build_scan(row, hs.verify_cache(self.cache, row), DICTIONARY, STAMP, self.canonical_ids)
        self.publish([], [scan])
        with self.assertRaisesRegex(hs.SnapshotError, "source_binding_missing"):
            self.stage()

    def test_baseline_changed_during_validation_aborts_without_output(self):
        self.seed()
        real_verify = hs.verify_cache
        def verify(cache, row):
            (self.published / "source-scans.jsonl").write_bytes(b"\n")
            return real_verify(cache, row)
        with patch.object(hs, "verify_cache", side_effect=verify), self.assertRaisesRegex(hs.SnapshotError, "baseline_changed"):
            self.stage()
        self.assertFalse((self.root / "staged").exists())

    def test_doi_canonical_work_can_keep_arxiv_source_and_scan(self):
        row = self.seed(work_id="doi:10.1109/lra.2026.3726328", aid="2608.29080")
        self.publish([row])
        self.assertTrue(self.stage()["ready_for_review"])
        self.assertEqual(self.read("source-scans.jsonl")[0]["work_id"], "doi:10.1109/lra.2026.3726328")
        self.assertEqual(self.read("source-observations.jsonl")[0]["arxiv_id"], "2608.29080")

    def test_unknown_work_or_wrong_canonical_arxiv_mapping_is_rejected(self):
        row = self.seed(work_id="doi:10.1109/iros60139.2025.11245841", aid="2505.01396")
        for mapping in ({}, {row["work_id"]: "2608.29080"}):
            with self.subTest(mapping=mapping), self.assertRaisesRegex(hs.SnapshotError, "canonical"):
                hs.stage_snapshot(cache=self.cache, observations=self.observations, published_dir=self.published,
                                  dictionary=DICTIONARY, staging_dir=self.root / "staged", snapshot_at=SNAPSHOT_AT,
                                  canonical_ids=mapping)
            self.assertFalse((self.root / "staged").exists())

    def test_source_and_effective_urls_must_bind_canonical_identity_and_version(self):
        for key, value in (("source_url", "https://arxiv.org/html/2608.29080v1"),
                           ("effective_url", "https://arxiv.org/html/2608.29080v1"),
                           ("source_url", "https://arxiv.org/html/2407.02648v2"),
                           ("effective_url", "https://arxiv.org/html/2407.02648v2"),
                           ("arxiv_id", "2608.29080")):
            self.rows = []
            self.seed(**{key: value})
            with self.subTest(key=key, value=value), self.assertRaisesRegex(hs.SnapshotError, "identity_mismatch|version_binding_mismatch"):
                self.stage()
            self.assertFalse((self.root / "staged").exists())

    def test_explicit_identity_failure_preserves_wrong_effective_url_as_failed_evidence(self):
        self.seed(status="identity_mismatch", effective_url="https://arxiv.org/html/2608.29080v1",
                  text_sha256=None, blocks_ref=None, body_cache_ref=None)
        self.assertTrue(self.stage()["ready_for_review"])
        self.assertEqual(self.read("source-observations.jsonl")[0]["status"], "identity_mismatch")
        self.assertEqual(self.read("source-scans.jsonl"), [])

    def test_scan_literal_span_and_original_section_id_preserved(self):
        row = self.seed()
        blocks = [{"section_id": "S2.SS1", "section_title": "PRIVATE_TITLE",
                   "text": "PRIVATE_PROLOGUE franka panda PRIVATE_EPILOGUE"}]
        body = blocks[0]["text"]
        scan = hs.build_scan(row, blocks, DICTIONARY, SNAPSHOT_AT, self.canonical_ids)
        match = scan["matches"][0]
        self.assertEqual(match["term"], body[match["start"]:match["end"]])
        self.assertEqual(match["section"], "S2.SS1")
        self.assertNotIn("PRIVATE_", hs.encode(scan))

    def test_snapshot_time_never_precedes_sources_fetches_or_scan_history(self):
        row = self.seed(stamp="2026-09-16T00:00:00Z")
        with self.assertRaisesRegex(hs.SnapshotError, "time_precedes_source"):
            self.stage()
        self.rows = []
        row = self.seed(fetched_at="2026-09-16T00:00:00Z")
        with self.assertRaisesRegex(hs.SnapshotError, "time_precedes_source"):
            self.stage()
        self.rows = []
        row = self.seed()
        scan = hs.build_scan(row, hs.verify_cache(self.cache, row), DICTIONARY, "2026-09-16T00:00:00Z", self.canonical_ids)
        self.publish([row], [scan])
        with self.assertRaisesRegex(hs.SnapshotError, "time_precedes_scan"):
            self.stage()
        self.assertFalse((self.root / "staged").exists())

    def test_fifo_is_rejected_without_blocking(self):
        fifo = self.cache / "objects/fifo"
        os.mkfifo(fifo)
        with self.assertRaisesRegex(hs.SnapshotError, "not_bounded_regular_file"):
            hs.read_object(self.cache, str(fifo))

    def test_canonical_map_loaded_only_from_explicit_fixture_catalog(self):
        catalog = self.root / "catalog"
        (catalog / "works").mkdir(parents=True)
        jsonl(catalog / "works/00.jsonl", [{"work_id": "doi:10.1109/lra.2026.3726328", "identifiers": {"arxiv": "2608.29080v1"}}])
        self.assertEqual(hs.load_canonical_map(catalog), {"doi:10.1109/lra.2026.3726328": "2608.29080"})
        jsonl(catalog / "works/01.jsonl", [{"work_id": "doi:10.1109/lra.2026.3726328", "identifiers": {"arxiv": "2608.29080"}}])
        with self.assertRaisesRegex(hs.SnapshotError, "missing_or_duplicate"):
            hs.load_canonical_map(catalog)

    def test_already_partial_incomplete_transport_is_scanned_without_promotion(self):
        self.seed(status="partial_text", transport_complete=False, transport_returncode=18,
                  transport_verification="incomplete")
        result = self.stage()
        self.assertTrue(result["ready_for_review"])
        self.assertEqual(self.read("source-observations.jsonl")[0]["status"], "partial_text")
        self.assertEqual(self.read("source-observations.jsonl")[0]["transport_verification"], "incomplete")
        self.assertEqual(len(self.read("source-scans.jsonl")), 1)
        self.assertEqual(self.read("pending-refresh.jsonl"), [])

    def test_raw_page_identity_checked_even_when_all_hashes_match(self):
        row = self.seed()
        raw = b'<html><meta name="citation_arxiv_id" content="2608.29080v1"><article>PRIVATE_WRONG_PAPER</article></html>'
        Path(row["cache_ref"]).write_bytes(raw)
        row["raw_sha256"] = hs.sha256(raw)
        jsonl(self.observations, [row])
        self.assertFalse(self.stage()["ready_for_review"])
        self.assertEqual(self.read("pending-refresh.jsonl")[0]["reasons"], ["cached_page_identity_validation_failed"])

    def test_no_raw_identity_proof_is_pending_not_completed_reading(self):
        row = self.seed()
        raw = b'<html><article>PRIVATE_BODY_NO_PAGE_IDENTITY</article></html>'
        Path(row["cache_ref"]).write_bytes(raw)
        row["raw_sha256"] = hs.sha256(raw)
        jsonl(self.observations, [row])
        result = self.stage()
        self.assertFalse(result["ready_for_review"])
        self.assertIn("not_completed_reading", result["verification_scope"])

    def test_cli_status_codes_and_manifest_for_fixture_only(self):
        row = self.seed()
        catalog = self.root / "catalog"
        catalog.mkdir()
        jsonl(catalog / "works.jsonl", [{"work_id": row["work_id"], "identifiers": {"arxiv": row["arxiv_id"]}}])
        dictionary_path = self.root / "dictionary.json"
        dictionary_path.write_text(hs.encode(DICTIONARY))
        args = ["snapshot_hardware_sources.py", "--cache", str(self.cache), "--observations", str(self.observations),
                "--published-dir", str(self.published), "--dictionary", str(dictionary_path), "--catalog", str(catalog),
                "--snapshot-at", SNAPSHOT_AT, "--staging-dir", str(self.root / "staged")]
        with patch.object(sys, "argv", args), patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(hs.main(), 0)
            self.assertFalse(json.loads(output.getvalue())["deployment_authorized"])
        with patch.object(sys, "argv", args), patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(hs.main(), 2)
            self.assertEqual(json.loads(output.getvalue())["error"], "staging_directory_must_be_new")
        row["transport_complete"] = False
        jsonl(self.observations, [row])
        args[-1] = str(self.root / "pending")
        with patch.object(sys, "argv", args), patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(hs.main(), 3)
            self.assertFalse(json.loads(output.getvalue())["ready_for_review"])

    def test_unresolved_identity_attempt_is_pending_until_public_schema_policy_exists(self):
        row = self.seed(work_id="doi:10.1234/noarxiv", arxiv_id=None, source_url=None, effective_url=None, version=None,
                        status="unavailable", raw_sha256=None, text_sha256=None, cache_ref=None, blocks_ref=None,
                        body_cache_ref=None, error="no_canonical_arxiv_identity")
        self.canonical_ids[row["work_id"]] = None
        self.assertFalse(self.stage()["ready_for_review"])
        self.assertEqual(self.read("pending-refresh.jsonl")[0]["reasons"], ["source_url_missing_requires_schema_policy"])
        self.assertFalse((self.root / "staged/source-observations.jsonl").exists())

    def test_failed_scan_history_preserves_later_failure_and_never_restores_old_success(self):
        row = self.seed()
        scanned = hs.build_scan(row, hs.verify_cache(self.cache, row), DICTIONARY, STAMP, self.canonical_ids)
        failed = {key: value for key, value in scanned.items() if key != "matches"}
        failed.update(status="failed", observed_at="2026-09-14T11:00:00Z")
        self.publish([row], [scanned, failed])
        self.assertTrue(self.stage()["ready_for_review"])
        self.assertEqual(self.read("source-scans.jsonl"), [scanned, failed])

    def test_correct_hashes_do_not_override_impossible_full_text_metadata(self):
        for index, changes in enumerate(({"body_characters": 50}, {"section_count": 99},
                                         {"thresholds": {"min_body_characters": 100_000, "min_sections": 1}},
                                         {"thresholds": {"min_body_characters": 1500, "min_sections": 4}},
                                         {"structured_document": False}, {"conversion_error_markers": 5})):
            self.rows = []
            self.seed(**changes)
            with self.subTest(changes=changes):
                self.assertFalse(self.stage(f"metadata{index}")["ready_for_review"])
                pending = hs.parse_jsonl((self.root / f"metadata{index}/pending-refresh.jsonl").read_bytes())[0]
                self.assertIn(pending[0]["reasons"][0], {"cached_body_metadata_count_mismatch", "cached_available_thresholds_inconsistent"})

    def test_unchanged_published_current_scan_reuses_without_opening_any_cache(self):
        row = self.seed()
        scan = hs.build_scan(row, hs.verify_cache(self.cache, row), DICTIONARY, STAMP, self.canonical_ids)
        self.publish([row], [scan])
        with (patch.object(hs, "read_object", side_effect=AssertionError("old cache must not open")),
              patch.object(hs, "verify_cache", side_effect=AssertionError("old cache must not be revalidated")),
              patch.object(hs, "build_scan", side_effect=AssertionError("old scan must not be rerun"))):
            result = self.stage()
        self.assertTrue(result["ready_for_review"])
        self.assertEqual((result["cache_verified"], result["new_scanned"], result["reused"], result["new_scans_added"]), (0, 0, 1, 0))
        self.assertEqual(self.read("source-scans.jsonl"), [scan])
        self.assertEqual(self.read("source-observations.jsonl"), [hs.project(row, self.canonical_ids)])
        self.assertIn("without_opening_or_revalidating_old_cache", result["verification_scope"]["reused"])

    def test_reused_source_metadata_binding_is_still_checked_before_any_cache_access(self):
        row = self.seed()
        scan = hs.build_scan(row, hs.verify_cache(self.cache, row), DICTIONARY, STAMP, self.canonical_ids)
        self.publish([row], [scan])
        jsonl(self.observations, [{**row, "body_characters": row["body_characters"] + 1}])
        with patch.object(hs, "read_object", side_effect=AssertionError("no cache before binding")):
            with self.assertRaisesRegex(hs.SnapshotError, "published_private_binding_mismatch"):
                self.stage()
        self.assertFalse((self.root / "staged").exists())

    def test_current_dictionary_missing_requires_cache_validation_and_rescan(self):
        row = self.seed()
        scan = hs.build_scan(row, hs.verify_cache(self.cache, row), DICTIONARY, STAMP, self.canonical_ids)
        self.publish([row], [scan])
        with (patch.object(hs, "verify_cache", wraps=hs.verify_cache) as verify,
              patch.object(hs, "build_scan", wraps=hs.build_scan) as build):
            result = self.stage(dictionary={**DICTIONARY, "version": "2"})
        self.assertEqual(verify.call_count, 1)
        self.assertEqual(build.call_count, 1)
        self.assertEqual((result["cache_verified"], result["new_scanned"], result["reused"], result["new_scans_added"]), (1, 1, 0, 1))
        self.assertEqual(self.read("source-scans.jsonl")[0], scan)
        self.assertEqual(len(self.read("source-scans.jsonl")), 2)

    def test_new_observation_with_existing_body_scan_still_verifies_own_cache(self):
        old = self.seed()
        scan = hs.build_scan(old, hs.verify_cache(self.cache, old), DICTIONARY, STAMP, self.canonical_ids)
        self.publish([old], [scan])
        current = self.seed(stamp=SNAPSHOT_AT)
        self.assertEqual(current["text_sha256"], old["text_sha256"])
        self.assertNotEqual(current["observation_id"], old["observation_id"])
        with patch.object(hs, "verify_cache", wraps=hs.verify_cache) as verify:
            result = self.stage()
        self.assertEqual(verify.call_count, 1)
        self.assertEqual(verify.call_args.args[1]["observation_id"], current["observation_id"])
        self.assertEqual((result["cache_verified"], result["new_scanned"], result["reused"], result["new_scans_added"]), (1, 1, 0, 0))
        self.assertEqual(self.read("source-scans.jsonl"), [scan])
        Path(current["cache_ref"]).write_bytes(b"PRIVATE_TAMPERED_NEW_RAW")
        with patch.object(hs, "verify_cache", wraps=hs.verify_cache) as verify:
            rejected = self.stage("tampered-new")
        self.assertEqual(verify.call_count, 1)
        self.assertFalse(rejected["ready_for_review"])
        self.assertEqual((rejected["cache_verification_attempted"], rejected["cache_verified"], rejected["reused"]), (1, 0, 0))
        pending = hs.parse_jsonl((self.root / "tampered-new/pending-refresh.jsonl").read_bytes())[0]
        self.assertEqual(pending[0]["reasons"], ["cached_raw_hash_mismatch"])

    def test_later_failed_history_is_reused_without_cache_open_or_new_success(self):
        row = self.seed()
        scanned = hs.build_scan(row, hs.verify_cache(self.cache, row), DICTIONARY, STAMP, self.canonical_ids)
        failed = {key: value for key, value in scanned.items() if key != "matches"}
        failed.update(status="failed", observed_at="2026-09-14T11:00:00Z")
        self.publish([row], [scanned, failed])
        with (patch.object(hs, "read_object", side_effect=AssertionError("failed history must not reopen cache")),
              patch.object(hs, "build_scan", side_effect=AssertionError("failed history must not be hidden by a retry"))):
            result = self.stage()
        self.assertEqual((result["cache_verified"], result["new_scanned"], result["reused"]), (0, 0, 1))
        self.assertEqual(self.read("source-scans.jsonl"), [scanned, failed])

    def test_new_observation_does_not_override_existing_failed_same_body_history(self):
        old = self.seed()
        failed = hs.build_scan(old, hs.verify_cache(self.cache, old), DICTIONARY, STAMP, self.canonical_ids)
        failed.update(status="failed", matches=[])
        self.publish([old], [failed])
        self.seed(stamp=SNAPSHOT_AT)
        result = self.stage()
        self.assertTrue(result["ready_for_review"])
        self.assertEqual((result["cache_verified"], result["new_scanned"], result["new_scans_added"], result["reused"]), (1, 1, 0, 0))
        self.assertEqual(self.read("source-scans.jsonl"), [failed])

    def test_indexed_history_binding_accepts_legacy_no_raw_hash_and_rejects_wrong_raw(self):
        row = self.seed()
        scan = hs.build_scan(row, hs.verify_cache(self.cache, row), DICTIONARY, STAMP, self.canonical_ids)
        legacy_scan = {key: value for key, value in scan.items() if key != "source_observation_hash"}
        self.publish([row], [legacy_scan])
        with patch.object(hs, "read_object", side_effect=AssertionError("legacy bound scan can reuse")):
            self.assertEqual(self.stage()["reused"], 1)
        self.publish([row], [{**scan, "source_observation_hash": "b" * 64}])
        with patch.object(hs, "read_object", side_effect=AssertionError("wrong raw binding must fail before cache")):
            with self.assertRaisesRegex(hs.SnapshotError, "scan_history_source_binding_missing"):
                self.stage("wrong-raw-binding")

    def test_automatic_timestamp_is_taken_after_fixed_read_and_does_not_chase_append(self):
        row = self.seed()
        original = self.observations.read_bytes()
        events = []
        real_read = hs.read_active_log_once
        appended = {**row, "observation_id": "hardware-source:" + "b" * 32, "observed_at": "2026-09-16T00:00:00Z"}
        def read(path):
            result = real_read(path)
            events.append("fixed_read_done")
            with path.open("ab") as handle:
                handle.write((hs.encode(appended) + "\n").encode())
            return result
        def utc():
            self.assertEqual(events, ["fixed_read_done"])
            events.append("utc_now")
            return SNAPSHOT_AT
        with (patch.object(hs, "read_active_log_once", side_effect=read) as reading,
              patch.object(hs, "utc_snapshot_time", side_effect=utc) as clock):
            result = hs.stage_snapshot(cache=self.cache, observations=self.observations, published_dir=self.published,
                                       dictionary=DICTIONARY, staging_dir=self.root / "staged", canonical_ids=self.canonical_ids)
        self.assertEqual((reading.call_count, clock.call_count), (1, 1))
        self.assertEqual(result["snapshot_at"], SNAPSHOT_AT)
        self.assertEqual(result["snapshot_time_basis"], "utc_after_fixed_log_prefix_read")
        self.assertEqual(result["log_prefix_sha256"], hs.sha256(original))
        self.assertEqual(result["observations_after_validation"], 1)

    def test_explicit_snapshot_time_never_reads_the_clock(self):
        self.seed()
        with patch.object(hs, "utc_snapshot_time", side_effect=AssertionError("explicit batch time must be stable")):
            result = self.stage()
        self.assertEqual(result["snapshot_at"], SNAPSHOT_AT)
        self.assertEqual(result["snapshot_time_basis"], "explicit")

    def test_cli_can_omit_snapshot_at_and_uses_post_read_utc(self):
        row = self.seed()
        catalog = self.root / "catalog"
        catalog.mkdir()
        jsonl(catalog / "works.jsonl", [{"work_id": row["work_id"], "identifiers": {"arxiv": row["arxiv_id"]}}])
        dictionary_path = self.root / "dictionary.json"
        dictionary_path.write_text(hs.encode(DICTIONARY))
        args = ["snapshot_hardware_sources.py", "--cache", str(self.cache), "--observations", str(self.observations),
                "--published-dir", str(self.published), "--dictionary", str(dictionary_path), "--catalog", str(catalog),
                "--staging-dir", str(self.root / "staged")]
        with (patch.object(sys, "argv", args), patch("sys.stdout", new_callable=io.StringIO) as output,
              patch.object(hs, "utc_snapshot_time", return_value=SNAPSHOT_AT)):
            self.assertEqual(hs.main(), 0)
        result = json.loads(output.getvalue())
        self.assertEqual(result["snapshot_at"], SNAPSHOT_AT)
        self.assertEqual(result["snapshot_time_basis"], "utc_after_fixed_log_prefix_read")


if __name__ == "__main__":
    unittest.main(verbosity=2)
