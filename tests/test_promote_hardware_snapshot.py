"""Offline disposable public-metadata fixtures; never run on real data/cache."""
import copy
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
import promote_hardware_snapshot as promotion
import snapshot_hardware_sources as snapshot

STAMP = "2026-09-14T10:00:00Z"
LATER = "2026-09-14T11:00:00Z"
SNAPSHOT_AT = "2026-09-15T10:00:00Z"
DICTIONARY = {"schema_version": "1", "version": "1", "entries": [
    {"dictionary_id": "model:franka-panda", "name": "Franka Panda", "category": "robot_arm",
     "identity_level": "model_specified", "aliases": ["Franka Panda"], "hardware_ids": [],
     "source_urls": ["https://example.org/fixture"]}]}


def jsonl(rows):
    return "".join(promotion.encode(row) + "\n" for row in rows).encode()


def tree(directory):
    return {str(path.relative_to(directory)): (path.is_dir(), path.stat().st_mtime_ns,
                                             path.stat().st_mode, None if path.is_dir() else path.read_bytes())
            for path in [directory, *directory.rglob("*")]}


class PromoteHardwareSnapshotTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.stage = self.root / "private-stage"
        self.target = self.root / "hardware-review"
        self.catalog = self.root / "canonical"
        self.dictionary = self.root / "dictionary.json"
        self.stage.mkdir(mode=0o700)
        self.target.mkdir()
        self.catalog.mkdir()
        self.dictionary.write_text(promotion.encode(DICTIONARY))
        self.old = self.observation("2407.02648")
        self.new = self.observation("2407.02649")
        self.canonical = {row["work_id"]: row["arxiv_id"] for row in (self.old, self.new)}
        (self.catalog / "works.jsonl").write_bytes(jsonl(
            [{"work_id": work_id, "identifiers": {"arxiv": aid}} for work_id, aid in self.canonical.items()]))
        self.old_scan = self.scan(self.old)
        self.new_scan = self.scan(self.new)
        self.old_rows = [copy.deepcopy(self.old)]
        self.old_scans = [copy.deepcopy(self.old_scan)]
        self.rows = [copy.deepcopy(self.old), copy.deepcopy(self.new)]
        self.scans = [copy.deepcopy(self.old_scan), copy.deepcopy(self.new_scan)]
        self.write_target()
        self.write_stage()
        # Unrelated public ledgers and canonical catalog bytes must not change.
        (self.target / "section-reviews.jsonl").write_bytes(b"SENTINEL REVIEW LEDGER\n")
        (self.root / "private-cache-sentinel.html").write_bytes(b"PRIVATE UNREAD DOCUMENT")
        for target in ((socket, "socket"), (snapshot, "verify_cache"), (snapshot, "read_active_log_once")):
            guard = patch.object(*target, side_effect=AssertionError("offline public-metadata-only test"))
            guard.start()
            self.addCleanup(guard.stop)
        collector = patch("collect_hardware_sources.Collector.__init__", side_effect=AssertionError("never instantiate collector"))
        collector.start()
        self.addCleanup(collector.stop)

    def observation(self, aid, **changes):
        return {"work_id": "arxiv:" + aid, "arxiv_id": aid, "version": "v1",
                "source_url": "https://arxiv.org/html/" + aid + "v1",
                "effective_url": "https://arxiv.org/html/" + aid + "v1",
                "observation_id": "hardware-source:" + promotion.sha256(aid.encode())[:32],
                "observed_at": STAMP, "status": "full_text_available", "scope": "body",
                "parser_version": snapshot.PARSER_VERSION,
                "raw_sha256": promotion.sha256((aid + ":raw").encode()),
                "text_sha256": promotion.sha256((aid + ":body").encode()),
                "transport_complete": True, "transport_verification": "complete", "manual_reviewed": False,
                **changes}

    def scan(self, source, **changes):
        return {"work_id": source["work_id"], "source_url": source["source_url"],
                "observed_at": STAMP, "scope": "body", "status": "scanned",
                "dictionary_hash": promotion.dictionary_hash(DICTIONARY), "content_hash": source["text_sha256"],
                "source_observation_hash": source["raw_sha256"], "parser_version": snapshot.PARSER_VERSION,
                "matches": [{"dictionary_id": "model:franka-panda", "term": "Franka Panda", "start": 0, "end": 12,
                             "section": "S1"}], "review_status": "unverified_machine_mentions", **changes}

    def write_target(self):
        (self.target / "source-observations.jsonl").write_bytes(jsonl(self.old_rows))
        (self.target / "source-scans.jsonl").write_bytes(jsonl(self.old_scans))

    def write_stage(self):
        for name, rows in (("source-observations.jsonl", self.rows), ("source-scans.jsonl", self.scans),
                           ("pending-refresh.jsonl", [])):
            (self.stage / name).write_bytes(jsonl(rows))
        distinct = list({promotion.encode(row): row for row in self.old_scans}.values())
        self.manifest = {"schema_version": "1", "kind": "hardware_source_snapshot", "prototype_only": False,
                         "deployment_authorized": False, "ready_for_review": True, "pending_refresh_count": 0,
                         "snapshot_at": SNAPSHOT_AT, "parser_version": snapshot.PARSER_VERSION,
                         "dictionary_hash": promotion.dictionary_hash(DICTIONARY),
                         "canonical_mapping_sha256": promotion.sha256(promotion.encode(self.canonical).encode()),
                         "published_observations_sha256": promotion.sha256((self.target / "source-observations.jsonl").read_bytes()),
                         "published_scans_sha256": promotion.sha256((self.target / "source-scans.jsonl").read_bytes()
                                                                    if (self.target / "source-scans.jsonl").exists() else b""),
                         "published_observations_retained": len(self.old_rows), "observations_after_validation": len(self.rows),
                         "new_observations": len(self.rows) - len(self.old_rows),
                         "scan_history_input_records": len(self.old_scans), "scan_history_retained": len(distinct),
                         "new_scans_added": len(self.scans) - len(distinct), "total_scans": len(self.scans)}
        self.rehash()

    def rehash(self):
        self.manifest["output_sha256"] = {name: promotion.sha256((self.stage / name).read_bytes())
                                            for name in promotion.OUTPUT_NAMES}
        (self.stage / promotion.MANIFEST_NAME).write_text(promotion.encode(self.manifest) + "\n")

    def run_promotion(self, *, apply=False, **changes):
        return promotion.promote_snapshot(**{"stage_dir": self.stage, "target_dir": self.target,
                                             "dictionary": self.dictionary, "catalog": self.catalog,
                                             "apply": apply, **changes})

    def reject_without_writes(self, reason, **kwargs):
        before = tree(self.root)
        with self.assertRaisesRegex(snapshot.SnapshotError, reason):
            self.run_promotion(apply=True, **kwargs)
        self.assertEqual(tree(self.root), before)

    def test_default_dry_run_is_completely_read_only(self):
        before = tree(self.root)
        result = self.run_promotion()
        self.assertFalse(result["applied"])
        self.assertTrue(result["dry_run"])
        self.assertTrue(result["validated"])
        self.assertEqual(tree(self.root), before)

    def test_apply_writes_only_two_targets_and_saves_private_recoverable_baseline(self):
        before = tree(self.root)
        result = self.run_promotion(apply=True)
        self.assertTrue(result["applied"])
        self.assertFalse(result["cross_file_atomic"])
        self.assertFalse(result["power_loss_safe"])
        self.assertEqual((self.target / "source-observations.jsonl").read_bytes(), jsonl(self.rows))
        self.assertEqual((self.target / "source-scans.jsonl").read_bytes(), jsonl(self.scans))
        backup = self.stage / result["backup_relative_path"]
        self.assertEqual((backup / "source-observations.jsonl").read_bytes(), jsonl(self.old_rows))
        self.assertEqual((backup / "source-scans.jsonl").read_bytes(), jsonl(self.old_scans))
        self.assertEqual(backup.stat().st_mode & 0o777, 0o700)
        self.assertEqual((backup / "source-observations.jsonl").stat().st_mode & 0o777, 0o600)
        after = tree(self.root)
        for path in ("dictionary.json", "canonical/works.jsonl", "hardware-review/section-reviews.jsonl",
                     "private-cache-sentinel.html", *["private-stage/" + name for name in (*promotion.OUTPUT_NAMES, promotion.MANIFEST_NAME)]):
            self.assertEqual(after[path], before[path], path)

    def test_same_snapshot_apply_is_idempotent_without_new_backup_or_file_mtime(self):
        self.run_promotion(apply=True)
        before = tree(self.root)
        result = self.run_promotion(apply=True)
        self.assertTrue(result["already_applied"])
        self.assertFalse(result["applied"])
        self.assertEqual(tree(self.root), before)

    def test_existing_exact_output_is_read_only_noop_even_without_backup(self):
        for name in promotion.TARGET_NAMES:
            (self.target / name).write_bytes((self.stage / name).read_bytes())
        before = tree(self.root)
        self.assertTrue(self.run_promotion(apply=True)["already_applied"])
        self.assertEqual(tree(self.root), before)

    def test_tampered_each_output_rejected_before_any_writes(self):
        for name in sorted(promotion.OUTPUT_NAMES):
            with self.subTest(name=name):
                path = self.stage / name
                original = path.read_bytes()
                path.write_bytes(original + b"\n")
                self.reject_without_writes("staged_output_hash_mismatch")
                path.write_bytes(original)

    def test_missing_or_traversing_output_manifest_entry_rejected(self):
        self.manifest["output_sha256"]["../private-cache-sentinel.html"] = "0" * 64
        (self.stage / promotion.MANIFEST_NAME).write_text(promotion.encode(self.manifest))
        self.reject_without_writes("snapshot_output_set_invalid")

    def test_target_observation_baseline_changed_rejected(self):
        (self.target / "source-observations.jsonl").write_bytes(jsonl(self.old_rows) + b"\n")
        self.reject_without_writes("target_baseline_hash_mismatch")

    def test_target_scan_baseline_late_failed_event_changed_rejected(self):
        self.old_scans.append(self.scan(self.old, observed_at=LATER, status="failed", matches=[]))
        self.write_target()
        self.reject_without_writes("target_baseline_hash_mismatch")

    def test_original_observation_id_or_field_cannot_be_dropped(self):
        for change in ("drop", "remove-field", "modify-field", "reorder"):
            with self.subTest(change=change):
                self.rows = [copy.deepcopy(self.old), copy.deepcopy(self.new)]
                if change == "drop":
                    self.rows.pop(0)
                elif change == "remove-field":
                    self.rows[0].pop("manual_reviewed")
                elif change == "modify-field":
                    self.rows[0]["manual_reviewed"] = True
                else:
                    self.rows.reverse()
                self.write_stage()
                self.reject_without_writes("published_observation_history_not_preserved|scan_source_binding_missing")

    def test_later_failed_scan_event_and_original_order_are_preserved(self):
        failed = self.scan(self.old, observed_at=LATER, status="failed", matches=[])
        self.old_scans.append(failed)
        self.scans.insert(1, failed)
        self.write_target()
        self.write_stage()
        self.run_promotion(apply=True)
        self.assertEqual(snapshot.parse_jsonl((self.target / "source-scans.jsonl").read_bytes())[0][:2], self.old_scans)

    def test_missing_or_reordered_late_failed_event_rejected_even_rehashed(self):
        failed = self.scan(self.old, observed_at=LATER, status="failed", matches=[])
        self.old_scans.append(failed)
        self.write_target()
        for scans in ([self.old_scan, self.new_scan], [failed, self.old_scan, self.new_scan]):
            self.scans = scans
            self.write_stage()
            self.reject_without_writes("published_scan_history_not_preserved")

    def test_exact_duplicate_old_scan_event_can_deduplicate_in_first_seen_order(self):
        self.old_scans = [self.old_scan, self.old_scan]
        self.write_target()
        self.write_stage()
        self.assertTrue(self.run_promotion(apply=True)["applied"])
        self.assertEqual(len(snapshot.parse_jsonl((self.target / "source-scans.jsonl").read_bytes())[0]), 2)

    def test_later_success_for_existing_failed_history_key_is_not_added(self):
        self.old_scans = [self.scan(self.old, status="failed", matches=[])]
        self.scans = [*self.old_scans, self.scan(self.old, observed_at=LATER), self.new_scan]
        self.write_target()
        self.write_stage()
        self.reject_without_writes("new_scan_replaces_existing_history_key")

    def test_pending_count_or_nonempty_pending_output_rejected(self):
        self.manifest["pending_refresh_count"] = 1
        self.rehash()
        self.reject_without_writes("snapshot_has_pending_refresh")
        self.manifest["pending_refresh_count"] = 0
        (self.stage / "pending-refresh.jsonl").write_bytes(jsonl([{"work_id": self.old["work_id"]}]))
        self.rehash()
        self.reject_without_writes("snapshot_has_pending_refresh")

    def test_prototype_wrong_kind_or_not_ready_rejected(self):
        for key, value in (("schema_version", "prototype-1"), ("kind", "other"),
                           ("prototype_only", True), ("ready_for_review", False)):
            with self.subTest(key=key):
                self.write_stage()
                self.manifest[key] = value
                self.rehash()
                self.reject_without_writes("unsupported_snapshot_manifest|snapshot_has_pending_refresh")

    def test_dictionary_and_canonical_mapping_changes_rejected(self):
        self.dictionary.write_text(promotion.encode({**DICTIONARY, "version": "2"}))
        self.reject_without_writes("dictionary_hash_mismatch")
        self.dictionary.write_text(promotion.encode(DICTIONARY))
        (self.catalog / "works.jsonl").write_bytes(jsonl([
            {"work_id": self.old["work_id"], "identifiers": {"arxiv": self.old["arxiv_id"]}}]))
        self.reject_without_writes("canonical_mapping_hash_mismatch")

    def test_catalog_sharded_canonical_projection_matches_staging_loader(self):
        works = self.catalog / "works"
        works.mkdir()
        (works / "one.jsonl").write_bytes((self.catalog / "works.jsonl").read_bytes())
        self.assertEqual(promotion._canonical_mapping(self.catalog), snapshot.load_canonical_map(self.catalog))
        self.assertTrue(self.run_promotion()["validated"])

    def test_registered_opaque_legacy_work_survives_promotion_validation_without_renaming(self):
        legacy = "doi:0.1109/isparo66239.2025.11436888"
        self.new = self.observation("2512.03736", work_id=legacy)
        self.new_scan = self.scan(self.new)
        self.canonical = {row["work_id"]: row["arxiv_id"] for row in (self.old, self.new)}
        (self.catalog / "works.jsonl").write_bytes(jsonl(
            [{"work_id": wid, "identifiers": {"arxiv": aid}} for wid, aid in self.canonical.items()]))
        self.rows = [self.old, self.new]
        self.scans = [self.old_scan, self.new_scan]
        self.write_stage()
        before = tree(self.root)
        self.assertTrue(self.run_promotion()["validated"])
        self.assertEqual(tree(self.root), before)
        self.assertEqual(snapshot.load_canonical_map(self.catalog), promotion._canonical_mapping(self.catalog))
        self.assertEqual(self.rows[1]["work_id"], legacy)
        self.assertEqual(self.scans[1]["work_id"], legacy)
        self.rows[1] = {**self.new, "source_url": "https://arxiv.org/html/2512.03737v1"}
        self.write_stage()
        self.reject_without_writes("source_url_canonical_identity_mismatch")

    def test_public_private_fields_or_unsafe_urls_rejected_even_with_new_hashes(self):
        for key, value in (("cache_ref", "/secret/cache.html"), ("blocks_ref", "private.json"),
                           ("raw_html", "PRIVATE BODY"), ("source_url", "https://evil.example/collect"),
                           ("effective_url", "https://arxiv.org/html/2407.02649v1?token=secret")):
            with self.subTest(key=key):
                self.rows = [copy.deepcopy(self.old), {**self.new, key: value}]
                self.write_stage()
                self.reject_without_writes("public_fields_not_allowlisted|invalid_public_metadata")

    def test_scan_private_field_or_mismatched_reference_rejected(self):
        for change in ({"raw_html": "PRIVATE"}, {"content_hash": "0" * 64}, {"source_observation_hash": "0" * 64}):
            self.scans = [copy.deepcopy(self.old_scan), {**self.new_scan, **change}]
            self.write_stage()
            self.reject_without_writes("scan_history_schema_invalid|scan_source_binding_missing")

    def test_current_dictionary_match_must_be_literal_dictionary_hit(self):
        self.scans[1]["matches"][0]["term"] = "PRIVATE BODY LEAK"
        self.scans[1]["matches"][0]["end"] = len("PRIVATE BODY LEAK")
        self.write_stage()
        self.reject_without_writes("new_scan_dictionary_match_invalid")

    def test_new_scan_span_must_equal_the_literal_term_length(self):
        for start, end in ((0, 11), (0, 13), (100, 113)):
            with self.subTest(start=start, end=end):
                self.scans[1]["matches"][0].update(start=start, end=end)
                self.write_stage()
                self.reject_without_writes("new_scan_match_span_invalid")

    def test_new_scan_section_id_is_required_and_cannot_contain_body_text(self):
        for section in (None, "", "Experimental Setup", "PRIVATE BODY EXCERPT", "S1/path", "a" * 257):
            with self.subTest(section=section):
                match = self.scans[1]["matches"][0]
                if section is None:
                    match.pop("section", None)
                else:
                    match["section"] = section
                self.write_stage()
                self.reject_without_writes("new_scan_section_id_invalid")

    def test_new_scan_valid_section_id_and_legacy_history_title_are_preserved(self):
        self.old_scans[0]["matches"][0]["section"] = "Experimental Setup"
        self.scans[0] = copy.deepcopy(self.old_scans[0])
        self.scans[1]["matches"][0]["section"] = "S1.sub-section:2_foo"
        self.write_target()
        self.write_stage()
        self.assertTrue(self.run_promotion()["validated"])

    def test_scan_cannot_predate_its_earliest_fully_matching_source(self):
        self.scans[1]["observed_at"] = "2026-09-14T09:59:59Z"
        self.write_stage()
        self.reject_without_writes("scan_time_precedes_bound_source_observation")

    def test_scan_timestamp_binding_includes_raw_hash_when_present(self):
        newer = {**self.new, "observation_id": "hardware-source:" + "a" * 32,
                 "observed_at": LATER, "raw_sha256": "f" * 64}
        self.rows.append(newer)
        # The body existed at STAMP, but these exact raw bytes only at LATER.
        self.scans[1] = self.scan(newer, observed_at=STAMP)
        self.write_stage()
        self.reject_without_writes("scan_time_precedes_bound_source_observation")

    def test_older_scan_can_be_reused_for_newer_same_body_observation(self):
        self.rows.append({**self.old, "observation_id": "hardware-source:" + "a" * 32,
                          "observed_at": LATER, "raw_sha256": "f" * 64})
        self.write_stage()
        self.assertTrue(self.run_promotion()["validated"])

    def test_legacy_scan_without_raw_hash_uses_earliest_same_body_observation(self):
        self.old_scans[0].pop("source_observation_hash")
        self.scans[0] = copy.deepcopy(self.old_scans[0])
        self.rows.append({**self.old, "observation_id": "hardware-source:" + "a" * 32,
                          "observed_at": LATER, "raw_sha256": "f" * 64})
        self.write_target()
        self.write_stage()
        self.assertTrue(self.run_promotion()["validated"])
        self.old_scans[0]["observed_at"] = "2026-09-14T09:59:59Z"
        self.scans[0] = copy.deepcopy(self.old_scans[0])
        self.write_target()
        self.write_stage()
        self.reject_without_writes("scan_time_precedes_bound_source_observation")

    def test_latest_available_source_cannot_reuse_old_scan_without_raw_hash(self):
        for status in ("full_text_available", "partial_text"):
            for missing in (True, False):
                with self.subTest(status=status, missing=missing):
                    latest = {**self.old, "status": status, "observation_id": "hardware-source:" + "a" * 32,
                              "observed_at": LATER, "raw_sha256": None}
                    if missing:
                        latest.pop("raw_sha256")
                    self.rows = [copy.deepcopy(self.old), copy.deepcopy(self.new), latest]
                    self.write_stage()
                    self.reject_without_writes("available_source_hash_required:raw_sha256")

    def test_latest_available_source_requires_body_hash(self):
        for status in ("full_text_available", "partial_text"):
            with self.subTest(status=status):
                self.rows.append({**self.old, "status": status, "observation_id": "hardware-source:" + "a" * 32,
                                  "observed_at": LATER, "text_sha256": None})
                self.write_stage()
                self.reject_without_writes("available_source_hash_required:text_sha256")
                self.rows.pop()

    def test_new_nonlatest_available_observation_still_requires_both_hashes(self):
        for status in ("full_text_available", "partial_text"):
            for key in ("raw_sha256", "text_sha256"):
                with self.subTest(status=status, key=key):
                    earlier = {**self.old, "status": status, "observation_id": "hardware-source:" + "a" * 32,
                               "observed_at": "2026-09-14T09:00:00Z", key: None}
                    self.rows = [copy.deepcopy(self.old), copy.deepcopy(self.new), earlier]
                    self.write_stage()
                    self.reject_without_writes("available_source_hash_required:" + key)

    def test_context_gated_g1_hit_verifies_finite_literal_without_rereading_context(self):
        dictionary = copy.deepcopy(DICTIONARY)
        dictionary["entries"].append({"dictionary_id": "model:unitree-g1", "name": "Unitree G1",
                                       "category": "robot_platform", "identity_level": "model_specified",
                                       "aliases": ["G1"], "context_terms": ["Unitree", "humanoid"]})
        body = "The humanoid robot G1 performed the task."
        hits = promotion.detect_mentions(body, dictionary, section="S1")
        self.assertEqual([hit["term"] for hit in hits], ["G1"])
        self.assertEqual(promotion.detect_mentions("G1", dictionary), [])
        self.dictionary.write_text(promotion.encode(dictionary))
        self.scans[1]["dictionary_hash"] = promotion.dictionary_hash(dictionary)
        self.scans[1]["matches"] = [{key: value for key, value in hits[0].items() if key != "excerpt"}]
        # The changed dictionary also requires a new current scan for old body.
        self.scans.append(self.scan(self.old, observed_at=LATER, dictionary_hash=promotion.dictionary_hash(dictionary)))
        self.write_stage()
        self.manifest["dictionary_hash"] = promotion.dictionary_hash(dictionary)
        self.rehash()
        self.assertTrue(self.run_promotion()["validated"])

    def test_missing_latest_current_dictionary_scan_rejected(self):
        self.scans = [self.old_scan]
        self.write_stage()
        self.reject_without_writes("latest_source_current_dictionary_scan_missing")

    def test_missing_parent_observation_reference_rejected(self):
        self.rows[1]["parent_observation_id"] = "hardware-source:" + "0" * 32
        self.write_stage()
        self.reject_without_writes("observation_parent_binding_invalid")

    def test_target_and_stage_overlap_rejected(self):
        self.reject_without_writes("stage_target_overlap", target_dir=self.stage)
        self.reject_without_writes("stage_target_overlap", target_dir=self.root)

    def test_stage_target_and_ancestor_symlinks_rejected(self):
        for key, destination in (("stage_dir", self.stage), ("target_dir", self.target)):
            link = self.root / (key + "-link")
            link.symlink_to(destination, target_is_directory=True)
            with self.assertRaisesRegex(snapshot.SnapshotError, "symlink"):
                self.run_promotion(**{key: link})
        ancestor = self.root / "ancestor-link"
        ancestor.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(snapshot.SnapshotError, "symlink"):
            self.run_promotion(stage_dir=ancestor / self.stage.name)

    def test_stage_file_target_file_dictionary_and_catalog_symlinks_rejected(self):
        for path in (self.stage / "source-scans.jsonl", self.target / "source-scans.jsonl",
                     self.dictionary, self.catalog / "works.jsonl"):
            with self.subTest(path=path.name):
                moved = path.with_name(path.name + ".original")
                path.rename(moved)
                path.symlink_to(moved)
                with self.assertRaisesRegex(snapshot.SnapshotError, "symlink"):
                    self.run_promotion()
                path.unlink()
                moved.rename(path)

    def test_second_replace_failure_rolls_back_first_and_keeps_backup(self):
        before = {name: (self.target / name).read_bytes() for name in promotion.TARGET_NAMES}
        actual = promotion._atomic_replace
        calls = []

        def failure(directory, name, raw, mode):
            calls.append(name)
            if len(calls) == 2:
                raise OSError("simulated second replace failure")
            return actual(directory, name, raw, mode)

        with patch.object(promotion, "_atomic_replace", side_effect=failure):
            with self.assertRaisesRegex(promotion.PromotionError, "changes_rolled_back"):
                self.run_promotion(apply=True)
        self.assertEqual({name: (self.target / name).read_bytes() for name in promotion.TARGET_NAMES}, before)
        self.assertEqual(calls, ["source-observations.jsonl", "source-scans.jsonl", "source-observations.jsonl"])
        self.assertEqual(len(list((self.stage / promotion.BACKUP_ROOT).iterdir())), 1)
        self.assertFalse(any("promotion-" in path.name for path in self.target.iterdir()))
        self.assertTrue(self.run_promotion(apply=True)["applied"])
        self.assertEqual(len(list((self.stage / promotion.BACKUP_ROOT).iterdir())), 1)

    def test_rollback_failure_reports_recovery_required_and_preserves_original_backup(self):
        actual = promotion._atomic_replace
        calls = []

        def failure(directory, name, raw, mode):
            calls.append(name)
            if len(calls) > 1:
                raise OSError("simulated replacement and rollback failure")
            return actual(directory, name, raw, mode)

        with patch.object(promotion, "_atomic_replace", side_effect=failure):
            with self.assertRaisesRegex(promotion.PromotionError, "rollback_incomplete_restore_private_backup"):
                self.run_promotion(apply=True)
        backups = list((self.stage / promotion.BACKUP_ROOT).iterdir())
        self.assertEqual((backups[0] / "source-observations.jsonl").read_bytes(), jsonl(self.old_rows))

    def test_exception_after_successful_replace_still_rolls_back_both_possible_files(self):
        for fail_at in (1, 2):
            with self.subTest(fail_at=fail_at):
                before = {name: (self.target / name).read_bytes() for name in promotion.TARGET_NAMES}
                actual = promotion._atomic_replace
                calls = []

                def failure(directory, name, raw, mode):
                    calls.append(name)
                    actual(directory, name, raw, mode)
                    if len(calls) == fail_at:
                        raise OSError("simulated exception after successful atomic rename")

                with patch.object(promotion, "_atomic_replace", side_effect=failure):
                    with self.assertRaisesRegex(promotion.PromotionError, "changes_rolled_back"):
                        self.run_promotion(apply=True)
                self.assertEqual({name: (self.target / name).read_bytes() for name in promotion.TARGET_NAMES}, before)

    def test_baseline_change_after_backup_is_not_overwritten(self):
        actual = promotion._backup
        changed = jsonl([self.old, self.new]) + b"\n"

        def concurrent_change(*args):
            result = actual(*args)
            (self.target / "source-observations.jsonl").write_bytes(changed)
            return result

        with patch.object(promotion, "_backup", side_effect=concurrent_change):
            with self.assertRaisesRegex(promotion.PromotionError, "target_baseline_changed_during_promotion"):
                self.run_promotion(apply=True)
        self.assertEqual((self.target / "source-observations.jsonl").read_bytes(), changed)
        self.assertEqual((self.target / "source-scans.jsonl").read_bytes(), jsonl(self.old_scans))

    def test_missing_original_scan_file_records_absence_in_backup(self):
        (self.target / "source-scans.jsonl").unlink()
        self.old_scans = []
        self.write_stage()
        result = self.run_promotion(apply=True)
        backup = self.stage / result["backup_relative_path"]
        metadata = snapshot.strict_json((backup / "backup-manifest.json").read_bytes())
        self.assertFalse(metadata["files"]["source-scans.jsonl"]["existed"])
        self.assertFalse((backup / "source-scans.jsonl").exists())

    def test_cli_requires_explicit_apply_and_defaults_to_read_only(self):
        before = tree(self.root)
        args = ["--stage-dir", str(self.stage), "--target-dir", str(self.target),
                "--dictionary", str(self.dictionary), "--catalog", str(self.catalog)]
        with patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(promotion.main(args), 0)
        self.assertTrue(snapshot.strict_json(output.getvalue())["dry_run"])
        self.assertEqual(tree(self.root), before)


if __name__ == "__main__":
    unittest.main()
