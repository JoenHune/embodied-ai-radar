"""Synthetic receipt fixtures only: no network, model, original user cache or writes."""
import copy
import json
import socket
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import editorial_readings as er
from catalog_store import fingerprint
from fulltext_reading_reviews import TEXT_SCOPE, article_text, sha256
import test_fulltext_reading_reviews as source_reading_fixtures


class EditorialReadingsTests(unittest.TestCase):
    def setUp(self):
        self.fixture = source_reading_fixtures.FulltextReadingReviewsTests("test_exact_article_text_keeps_whitespace_repetition_math_context_and_appendix")
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.catalog = copy.deepcopy(self.fixture.payload)
        self.receipt = copy.deepcopy(self.fixture.validate()[0])
        self.observation = copy.deepcopy(self.fixture.obs)
        self.work = {
            **self.catalog["works"][0], "experimental_text_available": True,
            "text_status": "available", "text_version": "v1",
            "text_snapshot_ids": ["text-snapshot:historical-v1"],
            "text_available_at": "2026-06-12", "text_date_precision": "day",
            "evidence_grade": "E0", "strict_peer_reviewed": False,
            "facts": {"deterministic_count": 17},
        }
        self.cutoff = "2026-06-30"
        guard = patch.object(socket, "socket", side_effect=AssertionError("No network"))
        guard.start()
        self.addCleanup(guard.stop)

    def index(self, readings=None, observations=None, as_of="2026-09-15", catalog=None):
        with (patch("fulltext_reading_reviews.private_bytes", side_effect=AssertionError("No raw cache read")),
              patch("fulltext_reading_reviews._material", side_effect=AssertionError("No original HTML parse"))):
            return er.build_reading_index(self.catalog if catalog is None else catalog,
                                          [self.receipt] if readings is None else readings,
                                          [self.observation] if observations is None else observations, as_of)

    def additional_receipt(self, *, version="v3", marker="New source", completed="2026-09-15T02:00:00Z", status="full_text_available"):
        fixture = self.fixture
        raw = fixture.html.replace(b"2407.02648v1", ("2407.02648" + version).encode()).replace(b"ABSTRACT.", marker.encode())
        fixture.raw_path.write_bytes(raw)
        url = fixture.url[:-2] + version
        fixture.obs.update(version=version, source_url=url, effective_url=url, raw_sha256=sha256(raw), status=status)
        text = article_text(raw)
        fixture.record.update(version=version, source_url=url, raw_sha256=sha256(raw),
                              read_completed_at=completed, article_chars=len(text),
                              article_text_sha256=sha256(text.encode()), read_ranges=[{"start": 0, "end": len(text)}])
        return copy.deepcopy(fixture.validate()[0]), copy.deepcopy(fixture.obs)

    def test_delayed_reading_of_v1_annotates_historical_v1_without_backdating(self):
        row = er.annotations_for_work(self.work, self.index(), self.cutoff)[0]
        self.assertEqual(row["version"], "v1")
        self.assertEqual(row["observed_at"], "2026-09-14T01:00:00Z")
        self.assertEqual(row["read_completed_at"], "2026-09-14T02:00:00Z")
        self.assertEqual(row["source_version_available_at"], "2026-06-12")
        self.assertIn("reading_after_historical_cutoff_not_backdated", row["warnings"])
        self.assertEqual(row["findings_zh"], self.receipt["findings_zh"])
        self.assertEqual(row["limitations_zh"], self.receipt["limitations_zh"])
        self.assertFalse(row["verbatim_source_text"])
        self.assertFalse(row["independent_validation"])

    def test_current_data_as_of_filters_future_readings_including_timestamp_boundary(self):
        self.assertEqual(self.index(as_of="2026-09-13"), {})
        self.assertEqual(self.index(as_of="2026-09-14T01:59:59Z"), {})
        self.assertIn(self.fixture.wid, self.index(as_of="2026-09-14T02:00:00Z"))
        future = {**self.receipt, "read_completed_at": "2026-09-16T00:00:00Z"}
        self.assertEqual(self.index([future]), {})

    def test_v3_cannot_replace_v1_and_unrelated_version_does_not_change_annotation(self):
        before = er.annotations_for_work(self.work, self.index(), self.cutoff)
        v3, obs3 = self.additional_receipt()
        combined = self.index([v3, self.receipt], [obs3, self.observation])
        self.assertEqual(er.annotations_for_work(self.work, combined, self.cutoff), before)
        self.assertEqual(er.annotations_for_work(self.work, self.index([v3], [obs3]), self.cutoff), [])
        future_view = {**self.work, "text_version": "v3", "text_available_at": "2026-09-01"}
        self.assertEqual(er.annotations_for_work(future_view, combined, self.cutoff), [])
        self.assertEqual(er.annotations_for_work(future_view, combined, "2026-09-30")[0]["version"], "v3")

    def test_missing_unknown_unversioned_or_blocked_view_never_upgrades_from_reading(self):
        index = self.index()
        mutations = [
            {"experimental_text_available": False}, {"experimental_text_available": 1},
            {"text_status": "available_unversioned"}, {"text_status": "retrospective_only"},
            {"text_status": "conflicting_snapshots"}, {"text_status": "unavailable"},
            {"text_version": None}, {"text_version": "v0"}, {"text_version": "v01"},
            {"text_snapshot_ids": []}, {"text_snapshot_ids": ""}, {"text_snapshot_ids": [" "]},
            {"text_snapshot_ids": ["same", "same"]}, {"text_available_at": None},
            {"text_available_at": "2026-02-30"}, {"text_available_at": "2026-07-01"},
            {"text_date_precision": None}, {"text_date_precision": "unknown"}, {"text_date_precision": "year"},
            {"research_status_blocked": True}, {"validation_eligible": False},
        ]
        for update in mutations:
            with self.subTest(update=update):
                self.assertEqual(er.annotations_for_work({**self.work, **update}, index, self.cutoff), [])

    def test_month_precision_waits_for_month_end_and_seconds_respect_existing_calendar_zone(self):
        index = self.index()
        month = {**self.work, "text_available_at": "2026-06", "text_date_precision": "month"}
        self.assertEqual(er.annotations_for_work(month, index, "2026-06-29"), [])
        self.assertEqual(len(er.annotations_for_work(month, index, "2026-06-30")), 1)
        late = {**self.work, "text_available_at": "2026-06-30T16:01:00Z", "text_date_precision": "second"}
        self.assertEqual(er.annotations_for_work(late, index, "2026-06-30"), [])
        early = {**late, "text_available_at": "2026-06-30T15:59:00Z"}
        self.assertEqual(len(er.annotations_for_work(early, index, "2026-06-30")), 1)

    def test_bad_date_precision_shapes_and_invalid_cutoff_fail_closed(self):
        index = self.index()
        for value, precision in [("2026-06", "day"), ("2026-06-01", "second"),
                                 ("2026-06-01T01:00:00", "second"), ("2026-06-99", "month")]:
            with self.subTest(value=value, precision=precision):
                self.assertEqual(er.annotations_for_work({**self.work, "text_available_at": value,
                                                         "text_date_precision": precision}, index, self.cutoff), [])
        self.assertEqual(er.annotations_for_work(self.work, index, "unknown"), [])

    def test_latest_reading_uses_datetime_not_lexical_string_and_is_order_independent(self):
        self.fixture.packet_declaration()
        packet_receipt = copy.deepcopy(self.fixture.validate()[0])
        raw_receipt = {**self.receipt, "read_completed_at": "2026-09-14T02:00:00.001Z"}
        first = self.index([raw_receipt, packet_receipt])
        second = self.index([packet_receipt, raw_receipt])
        self.assertEqual(first, second)
        chosen = er.annotations_for_work(self.work, first, self.cutoff)[0]
        self.assertEqual(chosen["reading_id"], raw_receipt["reading_id"])

    def test_equal_reading_times_use_deterministic_id_tie_and_keep_packet_normalization(self):
        self.fixture.packet_declaration()
        packet_receipt = copy.deepcopy(self.fixture.validate()[0])
        index = self.index([packet_receipt, self.receipt])
        selected = er.annotations_for_work(self.work, index, self.cutoff)[0]
        self.assertEqual(selected["reading_id"], max(packet_receipt["reading_id"], self.receipt["reading_id"]))
        packet_only = er.annotations_for_work(self.work, self.index([packet_receipt]), self.cutoff)[0]
        self.assertEqual(packet_only["article_normalization"], "reading-packet-blocks-v1")
        self.assertEqual(packet_only["reading_packet_sha256"], packet_receipt["reading_packet_sha256"])

    def test_latest_same_version_changes_annotation_digest(self):
        old = er.annotations_for_work(self.work, self.index(), self.cutoff)[0]
        new, obs = self.additional_receipt(version="v1")
        selected = er.annotations_for_work(self.work, self.index([self.receipt, new],
                                                               [self.observation, obs]), self.cutoff)[0]
        self.assertEqual(selected["reading_id"], new["reading_id"])
        self.assertNotEqual(selected["annotation_digest"], old["annotation_digest"])

    def test_partial_and_legacy_warnings_are_preserved_not_reclassified(self):
        self.fixture.obs["status"] = "partial_text"
        receipt = self.fixture.validate()[0]
        row = er.annotations_for_work(self.work, self.index([receipt], [self.fixture.obs]), self.cutoff)[0]
        self.assertEqual(row["source_availability_status"], "partial_text")
        self.assertEqual(row["transport_verification"], "legacy_unrecorded")
        self.assertIn("partial_source_text_preserved", row["warnings"])
        self.assertIn("legacy_transport_unrecorded", row["warnings"])
        for field in ["human_reviewed", "understanding_verified", "images_inspected", "supplementary_materials_inspected",
                      "tables_exhaustive", "publisher_fulltext_or_media_completeness_verified"]:
            self.assertIs(row[field], False)

    def test_unversioned_observed_url_is_preserved_but_reader_link_is_pinned(self):
        self.fixture.unversioned_source()
        receipt = self.fixture.validate()[0]
        row = er.annotations_for_work(self.work, self.index([receipt], [self.fixture.obs]), self.cutoff)[0]
        self.assertEqual(row["source_url"], self.fixture.url[:-2])
        self.assertEqual(row["reading_source_url"], self.fixture.url)
        self.assertEqual(row["raw_sha256"], receipt["raw_sha256"])
        self.assertIn("observed_url_unversioned_reader_link_pinned_without_new_acquisition", row["warnings"])

    def test_receipt_id_hash_source_or_private_field_tampering_is_rejected(self):
        updates = [
            {"reading_id": "fulltext-reading:" + "a" * 24},
            {"article_text_sha256": "f" * 64},
            {"declaration_sha256": "not-a-hash"},
            {"source_url": "https://arxiv.org/html/2501.99999v1"},
            {"cache_ref": "/private/source.html"},
            {"human_reviewed": True},
        ]
        for update in updates:
            with self.subTest(update=update), self.assertRaises(ValueError):
                self.index([{**self.receipt, **update}])
        forged = {**self.receipt, "raw_sha256": "f" * 64}
        forged["reading_id"] = "fulltext-reading:" + fingerprint([
            forged["work_id"], forged["source_url"], forged["version"], forged["raw_sha256"],
            forged["article_text_sha256"], TEXT_SCOPE, forged["article_normalization"]])[:24]
        with self.assertRaisesRegex(ValueError, "source_observation_mismatch"):
            self.index([forged])
        forged_locator = copy.deepcopy(self.receipt)
        forged_locator["findings_zh"][0]["locator_text_sha256"] = {"wrong": "a" * 64}
        with self.assertRaisesRegex(ValueError, "locator_hash_invalid"):
            self.index([forged_locator])

    def test_wrong_work_mapping_and_duplicate_canonical_work_are_rejected(self):
        wrong = {**self.work, "work_id": "doi:10.1234/other"}
        self.assertEqual(er.annotations_for_work(wrong, {wrong["work_id"]: [self.receipt]}, self.cutoff), [])
        bad_catalog = {"works": self.catalog["works"] * 2}
        with self.assertRaisesRegex(ValueError, "duplicate_canonical_work"):
            self.index(catalog=bad_catalog)

    def test_empty_or_unrelated_index_does_not_create_annotations(self):
        self.assertEqual(self.index([], []), {})
        self.assertEqual(er.annotations_for_work(self.work, {}, self.cutoff), [])
        initial = self.index()
        augmented = {**initial, "arxiv:other": []}
        self.assertEqual(er.annotations_for_work(self.work, initial, self.cutoff),
                         er.annotations_for_work(self.work, augmented, self.cutoff))

    def test_real_unrelated_audited_receipt_does_not_change_selected_annotation(self):
        before = er.annotations_for_work(self.work, self.index(), self.cutoff)
        fixture = self.fixture
        wid, aid = "arxiv:2407.09999", "2407.09999"
        work = {"work_id": wid, "identifiers": {"arxiv": aid}}
        fixture.payload = {"works": [work]}
        raw = fixture.html.replace(b"2407.02648v1", (aid + "v1").encode())
        fixture.raw_path.write_bytes(raw)
        url = "https://arxiv.org/html/" + aid + "v1"
        fixture.obs.update(work_id=wid, source_url=url, effective_url=url, raw_sha256=sha256(raw))
        fixture.record.update(work_id=wid, source_url=url, raw_sha256=sha256(raw))
        extra = fixture.validate()[0]
        index = self.index([extra, self.receipt], [fixture.obs, self.observation],
                           catalog={"works": [*self.catalog["works"], work]})
        self.assertEqual(er.annotations_for_work(self.work, index, self.cutoff), before)

    def test_same_reading_id_with_changed_interpretation_changes_annotation_digest(self):
        before = er.annotations_for_work(self.work, self.index(), self.cutoff)[0]
        self.fixture.record["findings_zh"][0]["text_zh"] = "表中A方法报告88分，未附误差条。"
        updated = self.fixture.validate()[0]
        self.assertEqual(updated["reading_id"], self.receipt["reading_id"])
        after = er.annotations_for_work(self.work, self.index([updated]), self.cutoff)[0]
        self.assertNotEqual(before["annotation_digest"], after["annotation_digest"])
        self.assertEqual(after["findings_zh"], updated["findings_zh"])

    def test_source_binding_mismatch_and_malformed_future_receipt_are_not_hidden(self):
        with self.assertRaisesRegex(ValueError, "source_observation_mismatch"):
            self.index(observations=[{**self.observation, "raw_sha256": "e" * 64}])
        future = {**self.receipt, "read_completed_at": "2027-01-01T00:00:00Z", "reading_id": "fake"}
        with self.assertRaisesRegex(ValueError, "reading_id_mismatch"):
            self.index([future])

    def test_inputs_and_facts_are_unchanged_and_output_has_no_original_text_or_paths(self):
        before = copy.deepcopy((self.catalog, self.receipt, self.observation, self.work))
        index = self.index()
        index_before = copy.deepcopy(index)
        row = er.annotations_for_work(self.work, index, self.cutoff)[0]
        self.assertEqual(row["annotation_digest"], fingerprint({k: v for k, v in row.items() if k != "annotation_digest"}))
        row["findings_zh"][0]["text_zh"] = "修改输出副本"
        row["checked_table_ids"].append("not-source")
        self.assertEqual(index, index_before)
        self.assertEqual((self.catalog, self.receipt, self.observation, self.work), before)
        serialized = json.dumps(er.annotations_for_work(self.work, index, self.cutoff))
        for forbidden in ("cache_ref", "blocks_ref", str(self.fixture.cache), "SECRET_SCRIPT", "RELATED_WORK.", "APPENDIX."):
            self.assertNotIn(forbidden, serialized)

    def test_load_reads_only_explicit_public_metadata_and_preserves_files(self):
        directory = self.fixture.root / "metadata"
        directory.mkdir()
        paths = [directory / "fulltext-readings.jsonl", directory / "source-observations.jsonl"]
        paths[0].write_text(json.dumps(self.receipt) + "\n")
        paths[1].write_text(json.dumps(self.observation) + "\n")
        before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in [*paths, self.fixture.raw_path]}
        with patch("fulltext_reading_reviews.private_bytes", side_effect=AssertionError("No original HTML")):
            index = er.load_reading_index(self.catalog, directory, "2026-09-15")
        self.assertEqual(index, self.index())
        self.assertEqual(before, {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in before})
        with self.assertRaises(ValueError):
            er.load_reading_index(self.catalog, self.fixture.root / "missing", "2026-09-15")

    def test_load_rejects_symlink_metadata_instead_of_following_it(self):
        directory = self.fixture.root / "metadata"
        directory.mkdir()
        (directory / "fulltext-readings.jsonl").symlink_to(self.fixture.raw_path)
        with self.assertRaisesRegex(ValueError, "regular_metadata_file"):
            er.load_reading_index(self.catalog, directory, "2026-09-15")


if __name__ == "__main__":
    unittest.main()
