"""Synthetic lineage fixtures only; never read user caches or call providers."""
import copy
import json
import socket
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import source_content_conflicts as conflicts
import test_fulltext_reading_reviews as reading_fixtures
import test_v3_editorial as editorial_fixtures
import test_temporal_trends as trend_fixtures
from catalog_store import fingerprint
from editorial_readings import build_reading_index
from fulltext_reading_reviews import article_text, public_audit, sha256
from versioned_text import digest, snapshot_from_payload
from trend_signals import reviewed_signal_evidence


class SourceContentConflictsTests(unittest.TestCase):
    def setUp(self):
        self.fixture = reading_fixtures.FulltextReadingReviewsTests(
            "test_exact_article_text_keeps_whitespace_repetition_math_context_and_appendix")
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.catalog = copy.deepcopy(self.fixture.payload)
        self.work = self.catalog["works"][0]
        self.work["source_record_ids"] = []
        self.catalog["source-records"] = []
        self.catalog["text-snapshots"] = []
        self.snapshot = self.add_snapshot()
        self.receipt = copy.deepcopy(self.fixture.validate()[0])
        self.observation = copy.deepcopy(self.fixture.obs)
        self.readings = [self.receipt]
        self.observations = [self.observation]
        self.row = self.make_row()
        guard = patch.object(socket, "socket", side_effect=AssertionError("No network or provider calls"))
        guard.start()
        self.addCleanup(guard.stop)

    def add_snapshot(self, *, work=None, version="v1", marker="original"):
        work = self.work if work is None else work
        aid = work["identifiers"]["arxiv"]
        sid = "source:synthetic-" + aid + "-" + version + "-" + marker
        source = {"source_record_id": sid, "url": "https://arxiv.org/abs/" + aid + version,
                  "published_at": "2026-07-01T00:00:00Z", "version": version,
                  "date_precision": "second", "source_type": "official_arxiv_version_metadata"}
        work.setdefault("source_record_ids", []).append(sid)
        payload = {"arxiv_id": aid, "version": version,
                   "title": "Synthetic title " + marker, "abstract": "Metadata abstract " + marker,
                   "authors": ["Fixture Author"], "submitted_at": "2026-07-01T00:00:00Z",
                   "updated_at": "2026-07-01T00:00:00Z"}
        snapshot = snapshot_from_payload(work, source, payload)
        source["payload_hash"] = digest(snapshot)
        source["text_content_digest"] = digest({key: snapshot[key] for key in ("title", "abstract")})
        self.catalog["source-records"].append(source)
        self.catalog["text-snapshots"].append(snapshot)
        return snapshot

    def make_row(self, *, snapshot=None, receipt=None, **updates):
        snapshot = self.snapshot if snapshot is None else snapshot
        receipt = self.receipt if receipt is None else receipt
        row = {"schema_version": "1", "work_id": receipt["work_id"], "version": receipt["version"],
               "detected_at": "2026-09-14T03:00:00Z", "reviewer_kind": "AI",
               "issue_types": ["abstract_body_divergence"],
               "summary_zh": "合成元数据与合成正文存在待核差异。",
               "limitations_zh": ["仅为来源对照，不代表撤稿或独立实验验证。"],
               "metadata_sources": [{"snapshot_id": snapshot["snapshot_id"], "content_digest": snapshot["content_digest"]}],
               "reading_sources": [{"reading_id": receipt["reading_id"], "reading_digest": fingerprint(receipt)}],
               "status": "open", "resolution": None}
        row.update(updates)
        row["conflict_id"] = conflicts.conflict_id_for(row)
        return row

    def build(self, records=None, *, as_of="2026-09-15", catalog=None, readings=None, observations=None):
        with (patch("fulltext_reading_reviews.private_bytes", side_effect=AssertionError("No original HTML access")),
              patch("fulltext_reading_reviews._material", side_effect=AssertionError("No original HTML parse"))):
            return conflicts.build_source_conflicts(
                [self.row] if records is None else records,
                self.catalog if catalog is None else catalog,
                self.readings if readings is None else readings,
                self.observations if observations is None else observations, as_of)

    def resolved(self, **updates):
        row = copy.deepcopy(self.row)
        row["status"] = "resolved"
        row["resolution"] = {"reviewed_at": "2026-09-16T04:00:00Z", "reviewer_kind": "human",
                             "note_zh": "已根据明确来源完成对照处理。",
                             "source_record_ids": [self.snapshot["source_record_id"]],
                             "reading_ids": [self.receipt["reading_id"]]}
        row["resolution"].update(updates)
        return row

    def additional_receipt(self, *, work=None, version="v2", marker="Later synthetic body"):
        work = self.work if work is None else work
        fixture = self.fixture
        aid = work["identifiers"]["arxiv"]
        raw = fixture.html.replace(b"2407.02648v1", (aid + version).encode()).replace(b"ABSTRACT.", marker.encode())
        fixture.raw_path.write_bytes(raw)
        url = "https://arxiv.org/html/" + aid + version
        fixture.payload = {"works": [work]}
        fixture.obs.update(work_id=work["work_id"], version=version, source_url=url, effective_url=url, raw_sha256=sha256(raw))
        text = article_text(raw)
        fixture.record.update(work_id=work["work_id"], version=version, source_url=url, raw_sha256=sha256(raw),
                              article_chars=len(text), article_text_sha256=sha256(text.encode()),
                              read_ranges=[{"start": 0, "end": len(text)}])
        receipt = copy.deepcopy(fixture.validate()[0])
        obs = copy.deepcopy(fixture.obs)
        self.readings.append(receipt)
        self.observations.append(obs)
        return receipt, obs

    def test_valid_notice_is_source_comparison_not_publication_or_independent_validation(self):
        notice = self.build()[0]
        self.assertEqual(notice["status"], "open")
        self.assertEqual(notice["experimental_use"], "hold")
        self.assertEqual(notice["assurance"], "source_comparison_review_not_publication_status_or_independent_validation")
        self.assertEqual(notice["reading_sources"][0]["raw_sha256"], self.receipt["raw_sha256"])
        self.assertEqual(notice["metadata_sources"][0]["source_record_id"], self.snapshot["source_record_id"])
        self.assertEqual(notice["source_urls"], sorted([self.snapshot["source_url"], self.receipt["source_url"]]))
        for forbidden in ("cache_ref", "blocks_ref", str(self.fixture.root), "SECRET_SCRIPT", "ABSTRACT."):
            self.assertNotIn(forbidden, json.dumps(notice))

    def test_notice_does_not_mutate_metadata_receipts_observations_or_cache(self):
        inputs = (self.row, self.catalog, self.readings, self.observations)
        before = copy.deepcopy(inputs)
        source_bytes = self.fixture.raw_path.read_bytes()
        counts = public_audit(self.readings, self.catalog, self.observations, "2026-09-15")["counts"]
        notice = self.build()[0]
        notice["metadata_sources"][0]["source_url"] = "changed"
        notice["reading_sources"][0]["raw_sha256"] = "changed"
        notice["limitations_zh"].append("仅修改输出副本")
        self.assertEqual(inputs, before)
        self.assertEqual(source_bytes, self.fixture.raw_path.read_bytes())
        self.assertEqual(public_audit(self.readings, self.catalog, self.observations, "2026-09-15")["counts"], counts)

    def test_unknown_and_wrong_known_work_are_rejected(self):
        other = {"work_id": "arxiv:2407.09999", "identifiers": {"arxiv": "2407.09999"}}
        self.catalog["works"].append(other)
        for wid in ("missing:work", other["work_id"]):
            with self.subTest(wid=wid):
                row = self.make_row(work_id=wid)
                with self.assertRaises(ValueError): self.build([row])

    def test_wrong_version_cannot_borrow_v1_sources(self):
        row = self.make_row(version="v2")
        with self.assertRaisesRegex(ValueError, "metadata_identity_mismatch"):
            self.build([row])

    def test_missing_or_wrong_metadata_reference_and_digest_are_rejected(self):
        for update in ({"snapshot_id": "missing:snapshot"}, {"content_digest": "f" * 64}):
            with self.subTest(update=update):
                row = copy.deepcopy(self.row)
                row["metadata_sources"][0].update(update)
                row["conflict_id"] = conflicts.conflict_id_for(row)
                with self.assertRaises(ValueError): self.build([row])

    def test_snapshot_text_hash_source_hash_url_and_ownership_are_all_bound(self):
        for mutation in ("text", "source_hash", "source_url", "missing_source", "not_owned"):
            with self.subTest(mutation=mutation):
                catalog = copy.deepcopy(self.catalog)
                if mutation == "text": catalog["text-snapshots"][0]["abstract"] += " tampered"
                elif mutation == "source_hash": catalog["source-records"][0]["payload_hash"] = "e" * 64
                elif mutation == "source_url": catalog["source-records"][0]["url"] = "https://arxiv.org/abs/2407.09999v1"
                elif mutation == "missing_source": catalog["source-records"] = []
                else: catalog["works"][0]["source_record_ids"] = []
                with self.assertRaisesRegex(ValueError, "metadata_snapshot_invalid"):
                    self.build(catalog=catalog)

    def test_reading_reference_requires_matching_receipt_and_complete_digest(self):
        for update in ({"reading_id": "missing:reading"}, {"reading_digest": "f" * 64}):
            with self.subTest(update=update):
                row = copy.deepcopy(self.row)
                row["reading_sources"][0].update(update)
                row["conflict_id"] = conflicts.conflict_id_for(row)
                with self.assertRaises(ValueError): self.build([row])

    def test_same_receipt_id_with_changed_judgment_cannot_reuse_old_digest(self):
        altered = copy.deepcopy(self.receipt)
        altered["findings_zh"][0]["text_zh"] = "另一项合成判断，原引用摘要不再适用。"
        with self.assertRaisesRegex(ValueError, "reading_digest_mismatch"):
            self.build(readings=[altered])

    def test_wrong_receipt_raw_article_hash_source_and_id_are_rejected(self):
        for update in ({"raw_sha256": "f" * 64}, {"article_text_sha256": "f" * 64},
                       {"source_url": "https://arxiv.org/html/2407.09999v1"},
                       {"reading_id": "fulltext-reading:" + "a" * 24}):
            with self.subTest(update=update):
                bad = {**self.receipt, **update}
                with self.assertRaises(ValueError): self.build(readings=[bad])

    def test_receipt_must_have_matching_public_observation(self):
        with self.assertRaisesRegex(ValueError, "source_observation_mismatch"):
            self.build(observations=[{**self.observation, "raw_sha256": "f" * 64}])

    def test_valid_other_version_receipt_cannot_bind_v1_notice(self):
        receipt, _ = self.additional_receipt()
        row = self.make_row(receipt=receipt, version="v1")
        with self.assertRaisesRegex(ValueError, "reading_identity_mismatch"):
            self.build([row])

    def test_valid_other_work_receipt_cannot_bind_notice_or_resolution(self):
        other = {"work_id": "arxiv:2407.09999", "identifiers": {"arxiv": "2407.09999"}, "source_record_ids": []}
        self.catalog["works"].append(other)
        receipt, _ = self.additional_receipt(work=other, version="v1")
        row = self.make_row(receipt=receipt, work_id=self.work["work_id"])
        with self.assertRaisesRegex(ValueError, "reading_identity_mismatch"):
            self.build([row])
        with self.assertRaisesRegex(ValueError, "resolution_reading_not_owned"):
            self.build([self.resolved(reading_ids=[receipt["reading_id"]])], as_of="2026-09-17")

    def test_detection_clock_does_not_backdate_hold_to_paper_publication(self):
        self.assertEqual(self.build(as_of="2026-07-31"), [])
        self.assertEqual(self.build(as_of="2026-09-14T02:59:59Z"), [])
        self.assertEqual(len(self.build(as_of="2026-09-14T03:00:00Z")), 1)
        self.assertEqual(len(self.build(as_of="2026-09-14")), 1)

    def test_future_resolution_does_not_release_or_disclose_it_early(self):
        row = self.resolved()
        before = copy.deepcopy(row)
        for cutoff in ("2026-09-15", "2026-09-16T03:59:59Z"):
            notice = self.build([row], as_of=cutoff)[0]
            self.assertEqual((notice["status"], notice["experimental_use"], notice["resolution"]), ("open", "hold", None))
        notice = self.build([row], as_of="2026-09-16T04:00:00Z")[0]
        self.assertEqual((notice["status"], notice["experimental_use"]), ("resolved", "released"))
        notice["resolution"]["source_record_ids"].clear()
        self.assertEqual(row, before)

    def test_new_edition_cannot_retroactively_release_old_disputed_text(self):
        later, _ = self.additional_receipt(version="v2")
        with self.assertRaisesRegex(ValueError, "resolution_reading_version_mismatch"):
            self.build([self.resolved(reading_ids=[later["reading_id"]])], as_of="2026-09-17")
        snapshot = self.add_snapshot(version="v2")
        with self.assertRaisesRegex(ValueError, "resolution_source_version_mismatch"):
            self.build([self.resolved(source_record_ids=[snapshot["source_record_id"]])], as_of="2026-09-17")
    def test_future_detected_notice_still_validates_lineage(self):
        row = self.make_row(detected_at="2027-01-01T00:00:00Z")
        self.assertEqual(self.build([row]), [])
        row["metadata_sources"][0]["content_digest"] = "f" * 64
        row["conflict_id"] = conflicts.conflict_id_for(row)
        with self.assertRaisesRegex(ValueError, "metadata_digest_mismatch"):
            self.build([row])

    def test_future_malformed_resolution_is_not_hidden_by_cutoff(self):
        with self.assertRaisesRegex(ValueError, "resolution_source_not_owned"):
            self.build([self.resolved(source_record_ids=["missing:source"])], as_of="2026-09-14")

    def test_detection_cannot_precede_referenced_reading(self):
        row = self.make_row(detected_at="2026-09-14T01:59:59Z")
        with self.assertRaisesRegex(ValueError, "reading_after_detection"):
            self.build([row])

    def test_resolution_must_be_strictly_later_than_detection(self):
        for when in ("2026-09-14T02:59:59Z", self.row["detected_at"]):
            with self.subTest(when=when), self.assertRaisesRegex(ValueError, "resolution_not_later"):
                self.build([self.resolved(reviewed_at=when)])

    def test_resolution_cannot_precede_its_additional_reading(self):
        later, _ = self.additional_receipt()
        later["read_completed_at"] = "2026-09-17T05:00:00Z"
        with self.assertRaisesRegex(ValueError, "resolution_before_reading"):
            self.build([self.resolved(reading_ids=[later["reading_id"]])], as_of="2026-09-18")

    def test_resolution_requires_nonempty_source_and_reading_proof_not_a_toggle(self):
        rows = [self.make_row(status="resolved"), {**self.row, "resolution": self.resolved()["resolution"]}]
        rows += [self.resolved(**update) for update in (
            {"source_record_ids": []}, {"reading_ids": []}, {"source_record_ids": ["missing:source"]},
            {"reading_ids": ["missing:reading"]})]
        for row in rows:
            with self.subTest(row=row), self.assertRaises(ValueError): self.build([row])

    def test_resolution_existing_foreign_source_is_rejected(self):
        self.catalog["source-records"].append({"source_record_id": "source:foreign", "url": "https://example.test/other"})
        with self.assertRaisesRegex(ValueError, "resolution_source_not_owned"):
            self.build([self.resolved(source_record_ids=["source:foreign"])])

    def test_private_paths_and_control_characters_are_rejected_in_review_text(self):
        for text in ("文件 /Users/example/private.txt", "文件 /home/example/key", "文件 /private/tmp/cache",
                     "文件 .research/source.html", "文件 file:///tmp/source", "文件 C:\\private\\source", "坏\x00文本", "坏\x1b文本"):
            for field in ("summary_zh", "limitations_zh", "resolution"):
                with self.subTest(text=text, field=field):
                    row = self.resolved() if field == "resolution" else copy.deepcopy(self.row)
                    if field == "resolution": row[field]["note_zh"] = text
                    elif field == "limitations_zh": row[field] = [text]
                    else: row[field] = text
                    with self.assertRaisesRegex(ValueError, "private_or_control_text"):
                        self.build([row])

    def test_schema_rejects_unknown_fields_types_empty_proofs_and_issue_codes(self):
        updates = [{"extra": "not permitted"}, {"schema_version": 1}, {"schema_version": "2"},
                   {"reviewer_kind": "automated"}, {"version": "v01"}, {"summary_zh": ""},
                   {"summary_zh": 42}, {"limitations_zh": "not a list"}, {"issue_types": []},
                   {"issue_types": ["unrecognized"]}, {"metadata_sources": []}, {"reading_sources": []},
                   {"status": "ignored"}]
        for update in updates:
            with self.subTest(update=update), self.assertRaisesRegex(ValueError, "schema_invalid"):
                self.build([{**self.row, **update}])
        row = copy.deepcopy(self.row)
        row["reading_sources"][0]["cache_ref"] = "private"
        with self.assertRaisesRegex(ValueError, "schema_invalid"): self.build([row])

    def test_missing_top_level_fields_and_nonobject_record_fail_with_value_error(self):
        for key in self.row:
            with self.subTest(missing=key):
                row = copy.deepcopy(self.row)
                del row[key]
                with self.assertRaises(ValueError): self.build([row])
        for row in (None, [], "bad", 1):
            with self.subTest(row=row), self.assertRaises(ValueError): self.build([row])

    def test_invalid_utc_dates_and_cutoff_are_rejected(self):
        for value in ("badZ", "2026-02-30T00:00:00Z", "2026-09-14T03:00:00+00:00"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.build([{**self.row, "detected_at": value}])
        with self.assertRaises(ValueError): self.build(as_of="not-a-date")

    def test_duplicate_ledger_catalog_and_reference_keys_are_rejected(self):
        with self.assertRaises(ValueError): self.build([self.row, copy.deepcopy(self.row)])
        for table in ("works", "text-snapshots", "source-records"):
            with self.subTest(table=table):
                catalog = copy.deepcopy(self.catalog)
                catalog[table].append(copy.deepcopy(catalog[table][0]))
                with self.assertRaises(ValueError): self.build(catalog=catalog)
        for field in ("metadata_sources", "reading_sources", "issue_types"):
            with self.subTest(field=field):
                row = copy.deepcopy(self.row)
                row[field].append(copy.deepcopy(row[field][0]))
                row["conflict_id"] = conflicts.conflict_id_for(row)
                with self.assertRaises(ValueError): self.build([row])

    def test_conflict_id_is_order_independent_but_binds_all_evidence(self):
        second_snapshot = self.add_snapshot(marker="changed")
        second_receipt, _ = self.additional_receipt(version="v1")
        row = self.make_row()
        row["issue_types"].append("version_date_disagreement")
        row["metadata_sources"].append({"snapshot_id": second_snapshot["snapshot_id"], "content_digest": second_snapshot["content_digest"]})
        row["reading_sources"].append({"reading_id": second_receipt["reading_id"], "reading_digest": fingerprint(second_receipt)})
        identifier = conflicts.conflict_id_for(row)
        reversed_row = copy.deepcopy(row)
        for field in ("issue_types", "metadata_sources", "reading_sources"): reversed_row[field].reverse()
        self.assertEqual(conflicts.conflict_id_for(reversed_row), identifier)
        row["conflict_id"] = identifier
        self.assertEqual(self.build([row])[0]["conflict_id"], identifier)
        for field in ("work_id", "version", "metadata_sources", "reading_sources", "issue_types"):
            changed = copy.deepcopy(row)
            if isinstance(changed[field], list): changed[field].pop()
            else: changed[field] += "different"
            self.assertNotEqual(conflicts.conflict_id_for(changed), identifier)

    def test_id_is_stable_across_review_prose_and_resolution_not_an_unbound_random_id(self):
        row = self.resolved()
        row.update(summary_zh="更新说明仍对应同组来源。", detected_at="2026-09-14T04:00:00Z")
        self.assertEqual(conflicts.conflict_id_for(row), self.row["conflict_id"])
        bad = {**self.row, "conflict_id": "source-conflict:" + "f" * 24}
        with self.assertRaisesRegex(ValueError, "id_mismatch"): self.build([bad])

    def test_distinct_version_notices_and_gate_do_not_cross_block_versions(self):
        snapshot_v2 = self.add_snapshot(version="v2")
        receipt_v2, _ = self.additional_receipt()
        v2row = self.make_row(snapshot=snapshot_v2, receipt=receipt_v2)
        notices = self.build([v2row, self.row])
        self.assertEqual([x["version"] for x in notices], ["v1", "v2"])
        self.assertEqual(len(conflicts.conflicts_for_work(notices, self.work["work_id"], "v2")), 1)
        view = {**self.work, "text_version": "v2", "experimental_text_available": True, "text_status": "available"}
        self.assertEqual(conflicts.gate_editorial_work(view, self.build()), view)
        for version in (None, "v3"):
            view["text_version"] = version
            self.assertEqual(conflicts.gate_editorial_work(view, notices), view)

    def test_gate_preserves_work_count_relevance_grade_peer_and_sampling_text(self):
        work = {**self.work, "title": "Synthetic title", "abstract": "Stable priority text",
                "text_version": "v1", "text_status": "available", "experimental_text_available": True,
                "relevance": {"status": "included", "score": 0.8}, "evidence_grade": "E2",
                "strict_peer_reviewed": True, "first_public_date": "2026-07-01", "count": 17,
                "evidence_flags": {"real_robot": True}, "directions": ["D1"], "questions": ["Q0"]}
        before = copy.deepcopy(work)
        held = conflicts.gate_editorial_work(work, self.build())
        self.assertFalse(held["experimental_text_available"])
        self.assertEqual(held["text_status"], "source_content_conflict")
        changed = {key for key in before if before[key] != held[key]}
        self.assertEqual(changed, {"experimental_text_available", "text_status"})
        self.assertEqual(set(held) - set(before), {"source_conflicts"})
        held["relevance"]["status"] = "changed only in output"
        self.assertEqual(work, before)

    def test_resolved_notice_remains_visible_without_experimental_hold(self):
        notices = self.build([self.resolved()], as_of="2026-09-17")
        self.assertEqual(conflicts.conflicts_for_work(notices, self.work["work_id"], active_only=True), [])
        self.assertEqual(len(conflicts.conflicts_for_work(notices, self.work["work_id"])), 1)
        work = {**self.work, "text_version": "v1", "experimental_text_available": True}
        self.assertEqual(conflicts.gate_editorial_work(work, notices), work)

    def test_load_reads_only_fixture_metadata_files_and_never_rewrites_them(self):
        root = self.fixture.root / "data"
        (root / "editorial").mkdir(parents=True)
        (root / "hardware-review").mkdir()
        paths = {root / "editorial/source-content-conflicts.jsonl": self.row,
                 root / "hardware-review/fulltext-readings.jsonl": self.receipt,
                 root / "hardware-review/source-observations.jsonl": self.observation}
        for path, row in paths.items(): path.write_text(json.dumps(row) + "\n")
        before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in paths}
        with patch("fulltext_reading_reviews.private_bytes", side_effect=AssertionError("No source cache")):
            result = conflicts.load_source_conflicts(self.catalog, root, "2026-09-15")
        self.assertEqual(result, self.build())
        self.assertEqual(before, {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in paths})

    def test_absent_optional_ledger_does_not_create_files(self):
        path = self.fixture.root / "not-created"
        self.assertEqual(conflicts.load_source_conflicts(self.catalog, path, "2026-09-15"), [])
        self.assertFalse(path.exists())

    def test_symlink_conflict_ledger_is_rejected(self):
        root = self.fixture.root / "data"
        (root / "editorial").mkdir(parents=True)
        ledger = root / "editorial/source-content-conflicts.jsonl"
        ledger.symlink_to(self.fixture.root / "missing-target")
        with self.assertRaises(ValueError): conflicts.load_source_conflicts(self.catalog, root, "2026-09-15")

    def test_consistently_rehashed_foreign_or_private_metadata_source_is_rejected(self):
        for url in ("https://arxiv.org/abs/2407.09999v1", "file:///private/source.html", "/Users/example/metadata.json"):
            with self.subTest(url=url):
                catalog = copy.deepcopy(self.catalog)
                snapshot, source = catalog["text-snapshots"][0], catalog["source-records"][0]
                snapshot["source_url"] = source["url"] = url
                source["payload_hash"] = digest(snapshot)
                with self.assertRaises(ValueError): self.build(catalog=catalog)

    def test_packet_keeps_selected_ids_and_facts_but_blocks_prose_translation_signal_and_annotation(self):
        editor = editorial_fixtures.editor
        month, catalog = editorial_fixtures.version_fixture()
        work = catalog["works"][0]
        # Fully validated synthetic receipt, with the same identity as the
        # version fixture; notice eligibility itself is covered above.
        receipt, observation = self.additional_receipt(work=work, version="v1")
        index = build_reading_index(catalog, [receipt], [observation], "2026-09-15")
        notice = {**self.build(readings=[self.receipt], observations=[self.observation])[0],
                  "work_id": work["work_id"], "version": "v1"}
        original_catalog, original_month, original_index = copy.deepcopy(catalog), copy.deepcopy(month), copy.deepcopy(index)
        before = editor.build_evidence_packet(month, catalog, reading_index=index)
        baseline_card = next(card for card in before["evidence_cards"] if card["work_id"] == work["work_id"])
        self.assertTrue(baseline_card.get("reading_annotations"))
        self.assertTrue(baseline_card["localization_required"])
        self.assertIn(work["work_id"], {eid for ids in before["signal_candidate_cards"].values() for eid in ids})
        original_localization_check = editor.valid_work_localization
        def previously_accepted_localization(localized, candidate):
            if localized and localized.get("work_id") == work["work_id"]:
                return True
            return original_localization_check(localized, candidate)
        with patch.object(editor, "valid_work_localization", side_effect=previously_accepted_localization):
            # Even a formerly accepted translation must not seed a held card.
            catalog["work-localizations"] = [{"work_id": work["work_id"], "title_zh": "旧译名", "summary_zh": "旧实验摘要", "keywords_zh": ["合成"]}]
            held = editor.build_evidence_packet(month, catalog, reading_index=index, source_conflicts=[notice])
        catalog.pop("work-localizations")
        self.assertEqual(catalog, original_catalog)
        self.assertEqual(month, original_month)
        self.assertEqual(index, original_index)
        for key in ("facts", "sampling", "coverage", "evidence_lanes", "evidence_grades", "directions", "questions"):
            self.assertEqual(held[key], before[key], key)
        self.assertEqual([c["evidence_id"] for c in held["evidence_cards"]], [c["evidence_id"] for c in before["evidence_cards"]])
        card = next(card for card in held["evidence_cards"] if card["work_id"] == work["work_id"])
        self.assertEqual(card["abstract"], "")
        self.assertEqual(card["summary_zh"], "")
        self.assertIsNone(card["title_zh"])
        self.assertFalse(card["experimental_text_available"])
        self.assertFalse(card["localization_required"])
        self.assertNotIn("translation_context", card)
        self.assertNotIn("reading_annotations", card)
        self.assertNotIn(work["work_id"], held["required_localization_ids"])
        self.assertNotIn(work["work_id"], {eid for ids in held["signal_candidate_cards"].values() for eid in ids})
        self.assertEqual(card["source_text_ranges"]["abstract"], {"start": 0, "end": 0})
        for key in ("title", "authors", "source_record_ids", "text_snapshot_ids", "text_version", "evidence_grade", "strict_peer_reviewed", "evidence_cluster_id", "directions", "questions"):
            self.assertEqual(card[key], baseline_card[key], key)
        self.assertEqual(sum(map(len, index.values())), 1)
        self.assertTrue(any("待核差异" in text and "不代表论文撤回" in text for text in held["known_limitations"]))

    def test_packet_hold_cannot_change_tight_cluster_sampling_priority(self):
        editor = editorial_fixtures.editor
        month, catalog = editorial_fixtures.version_fixture()
        first, second = catalog["works"][:2]
        first["curated"] = False
        first["strict_peer_reviewed"] = False
        second["directions"] = first["directions"] = ["D1"]
        second["questions"] = first["questions"] = ["Q0"]
        notice = {**self.build()[0], "work_id": first["work_id"], "version": "v1"}
        baseline = editor.build_evidence_packet(month, catalog, per_direction=1, per_question=1)
        held = editor.build_evidence_packet(month, catalog, per_direction=1, per_question=1, source_conflicts=[notice])
        chosen = lambda packet: [card["work_id"] for card in packet["evidence_cards"] if card["kind"] == "work"]
        self.assertEqual(chosen(baseline), [first["work_id"]])
        self.assertEqual(chosen(held), chosen(baseline))
        self.assertEqual(held["sampling"], baseline["sampling"])
        self.assertEqual(held["facts"], baseline["facts"])

    def signal_fixture(self, *, version="v1", source_version=None, resolved=False):
        notice = self.build([self.resolved()], as_of="2026-09-17")[0] if resolved else self.build()[0]
        sid = "source:signal-fixture"
        url = "https://arxiv.org/abs/2407.02648" + (version or "")
        source = {"source_record_id": sid, "url": url, "published_at": "2026-07-01", "date_precision": "day"}
        if source_version is not None: source["version"] = source_version
        work = {**copy.deepcopy(self.work), "source_record_ids": [sid], "source_conflicts": [notice],
                "title": "Synthetic robot policy", "abstract": "Policy motion result", "relevance": {"status": "included"},
                "first_public_date": "2026-07-01", "first_public_date_precision": "day"}
        record = {"record_id": "signal-proof:fixture", "signal_id": "S1", "work_id": work["work_id"],
                  "review_status": "verified", "research_scope": "in_scope", "stance": "supports",
                  "statement": "Synthetic source-bound robot policy finding.",
                  "experiment": {"setting": None, "baseline": None, "metric": None, "limitations": []},
                  "source_url": url, "source_record_ids": [sid], "public_at": "2026-07-01", "public_at_precision": "day"}
        work["signal_evidence"] = [record]
        return work, record, {sid: source}

    def test_signal_gate_blocks_same_and_unknown_version_but_allows_explicit_other_version(self):
        for version, source_version, held in (("v1", None, True), ("v2", None, False),
                                              (None, None, True), (None, "v1", True),
                                              (None, "v2", False), (None, "v01", True)):
            with self.subTest(version=version, source_version=source_version):
                work, record, sources = self.signal_fixture(version=version, source_version=source_version)
                before = copy.deepcopy((work, record, sources))
                self.assertIs(conflicts.signal_record_is_held(work, record, sources), held)
                self.assertEqual(reviewed_signal_evidence(work, "S1", "2026-09-15", sources), [] if held else [record])
                self.assertEqual((work, record, sources), before)

    def test_signal_gate_without_a_hold_leaves_old_proof_eligibility_unchanged(self):
        for resolved in (False, True):
            work, record, sources = self.signal_fixture(resolved=resolved)
            if not resolved: work.pop("source_conflicts")
            before = copy.deepcopy((work, record, sources))
            self.assertFalse(conflicts.signal_record_is_held(work, record, sources))
            self.assertEqual(reviewed_signal_evidence(work, "S1", "2026-09-17", sources), [record])
            self.assertEqual((work, record, sources), before)

    def test_future_resolution_still_blocks_signal_until_current_review_clock_releases(self):
        work, record, sources = self.signal_fixture()
        work["source_conflicts"] = self.build([self.resolved()], as_of="2026-09-15")
        self.assertEqual(reviewed_signal_evidence(work, "S1", "2026-09-15", sources), [])
        work["source_conflicts"] = self.build([self.resolved()], as_of="2026-09-17")
        self.assertEqual(reviewed_signal_evidence(work, "S1", "2026-09-17", sources), [record])

    def test_mixed_signal_source_versions_cannot_evade_held_version(self):
        work, record, sources = self.signal_fixture(version="v2")
        sources["source:older"] = {"source_record_id": "source:older", "version": "v1", "url": "https://arxiv.org/abs/2407.02648v1"}
        record["source_record_ids"].append("source:older")
        work["source_record_ids"].append("source:older")
        self.assertTrue(conflicts.signal_record_is_held(work, record, sources))
        self.assertEqual(reviewed_signal_evidence(work, "S1", "2026-09-15", sources), [])

    def test_signal_support_counterevidence_and_neutral_are_all_withheld_not_rewritten(self):
        for stance in ("supports", "contradicts", "neutral"):
            with self.subTest(stance=stance):
                work, record, sources = self.signal_fixture()
                record["stance"] = stance
                before = copy.deepcopy((work, record, sources))
                self.assertEqual(reviewed_signal_evidence(work, "S1", "2026-09-15", sources), [])
                self.assertEqual((work, record, sources), before)
                self.assertEqual(len(work["signal_evidence"]), 1)

    def test_allowed_other_version_still_needs_existing_signal_review_source_and_date_checks(self):
        mutations = ({"review_status": "draft"}, {"research_scope": "out_of_scope"},
                     {"source_record_ids": ["not-owned"]}, {"public_at": "2027-01-01"})
        for update in mutations:
            with self.subTest(update=update):
                work, record, sources = self.signal_fixture(version="v2")
                record.update(update)
                self.assertFalse(conflicts.signal_record_is_held(work, record, sources))
                self.assertEqual(reviewed_signal_evidence(work, "S1", "2026-09-15", sources), [])

    def test_trend_hold_preserves_topic_work_counts_but_cannot_upgrade_capability(self):
        rows = [trend_fixtures.work(str(i), reviewed=True) for i in range(3)]
        before = trend_fixtures.assess(rows, evidence_cutoff="2026-09-15")
        self.assertEqual(before["lifecycle"], "emerging")
        for work in rows:
            work["source_conflicts"] = [{**self.build()[0], "work_id": work["work_id"]}]
        records_before = copy.deepcopy(rows)
        held = trend_fixtures.assess(rows, evidence_cutoff="2026-09-15")
        self.assertEqual(held["lifecycle"], "candidate")
        self.assertEqual(held["supporting_work_ids"], [])
        self.assertEqual(held["supporting_evidence_ids"], [])
        self.assertEqual(held["reviewed_support_count"], 0)
        self.assertEqual(held["assessment_status"], "retrieval_only")
        for key in ("counts", "shares", "candidate_work_ids", "rolling_two_month_works", "independent_clusters", "organization_count", "topic_momentum"):
            self.assertEqual(held[key], before[key], key)
        self.assertEqual(rows, records_before)


if __name__ == "__main__":
    unittest.main()
