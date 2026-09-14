"""Explicit research-status imports preserve the complete research history."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.catalog_store import fingerprint
from scripts.ingest_research_status import apply_research_status_additions, ingest_research_status_additions


def fixture():
    work = {"work_id": "arxiv:2606.12345", "title": "Synthetic research title", "first_public_date": "2026-06-01",
            "first_public_date_precision": "day", "identifiers": {"arxiv": "2606.12345", "doi": "10.9999/example"},
            "aliases": ["legacy:work"], "source_record_ids": ["source:old"], "relevance": {"status": "included", "reviewed": True},
            "strict_peer_reviewed": True, "directions": ["D5"], "manual_annotation": {"retain": ["original"]}}
    payload = {"works": [work, {"work_id": "arxiv:2606.54321", "title": "Unrelated work", "source_record_ids": []}],
               "work-aliases": [{"alias": "old:work", "work_id": work["work_id"]}],
               "manifestations": [{"manifestation_id": "v1", "work_id": work["work_id"], "kind": "preprint", "url": "https://arxiv.org/abs/2606.12345v1", "public_at": "2026-06-01"},
                                  {"manifestation_id": "journal", "work_id": work["work_id"], "kind": "journal", "url": "https://doi.org/10.9999/example", "public_at": "2026-07-01"}],
               "source-records": [{"source_record_id": "source:old", "url": "https://arxiv.org/abs/2606.12345v1", "published_at": "2026-06-01"}],
               "evidence-events": [{"event_id": "event:original", "work_id": work["work_id"], "event_type": "published", "published_at": "2026-06-01"}],
               "field-provenance": [{"work_id": work["work_id"], "field": "title", "source_record_id": "source:old"}],
               "unrelated_table": [{"preserve": ["all", "rows"]}]}
    notice = {"notice_id": "notice:fixture:withdrawn", "work_id": work["work_id"], "event_type": "withdrawn", "scope": "work",
              "public_at": "2026-09-05", "date_precision": "day", "source_record_ids": ["source:status"],
              "source_url": "https://arxiv.org/abs/2606.12345v2", "review_status": "verified", "summary_zh": "官方版本声明该研究已撤回。",
              "source_record": {"source_record_id": "source:status", "url": "https://arxiv.org/abs/2606.12345v2",
                                "source_type": "official_arxiv_status_notice", "observed_at": "2026-09-06T10:00:00Z", "published_at": "2026-09-05",
                                "raw": {"title": "Synthetic research title", "status": "withdrawn", "version": "v2", "metadata_sha256": "a" * 64}}}
    return payload, notice


class ResearchStatusImportTests(unittest.TestCase):
    def test_adds_source_notice_event_and_provenance_without_rewriting_old_facts(self):
        payload, notice = fixture()
        before, original_notice = copy.deepcopy(payload), copy.deepcopy(notice)
        result = apply_research_status_additions(payload, [notice])
        self.assertEqual(payload, before)
        self.assertEqual(notice, original_notice)
        self.assertIsNot(result, payload)
        self.assertEqual(len(result["works"]), 2)
        self.assertEqual(result["works"][1], before["works"][1])
        self.assertEqual(result["manifestations"], before["manifestations"])
        self.assertEqual(result["work-aliases"], before["work-aliases"])
        self.assertEqual(result["unrelated_table"], before["unrelated_table"])
        work = result["works"][0]
        for key in ("work_id", "title", "first_public_date", "first_public_date_precision", "identifiers", "aliases", "relevance", "strict_peer_reviewed", "manual_annotation"):
            self.assertEqual(work[key], before["works"][0][key])
        self.assertEqual(work["source_record_ids"], ["source:old", "source:status"])
        stored = work["research_status_notices"][0]
        self.assertEqual(stored, {key: value for key, value in notice.items() if key != "source_record"})
        source = result["source-records"][-1]
        self.assertEqual(source["raw"], notice["source_record"]["raw"])
        self.assertEqual(source["retrieved_at"], notice["source_record"]["observed_at"])
        event = result["evidence-events"][-1]
        self.assertEqual((event["event_type"], event["published_at"], event["date_precision"]), ("withdrawn", "2026-09-05", "day"))
        self.assertEqual(event["research_status_notice_id"], notice["notice_id"])
        self.assertEqual(event["source_record_ids"], ["source:status"])
        provenance = result["field-provenance"][-1]
        self.assertEqual((provenance["field"], provenance["source_record_id"]), ("research_status_notices", "source:status"))
        self.assertEqual(provenance["research_status_notice_id"], notice["notice_id"])

    def test_same_notice_and_batch_duplicates_are_idempotent(self):
        payload, notice = fixture()
        once = apply_research_status_additions(payload, [notice, copy.deepcopy(notice)])
        self.assertEqual(apply_research_status_additions(once, [notice]), once)
        self.assertEqual(len(once["works"][0]["research_status_notices"]), 1)
        self.assertEqual(len(once["evidence-events"]), 2)
        self.assertEqual(len(once["field-provenance"]), 2)

    def test_relevance_enrichment_is_preserved_but_core_event_tampering_fails(self):
        payload, notice = fixture()
        once = apply_research_status_additions(payload, [notice])
        once["evidence-events"][-1].update(research_eligible=True, review_required=False)
        self.assertEqual(apply_research_status_additions(once, [notice]), once)
        self.assertEqual(once["evidence-events"][-1]["observed_at"], notice["source_record"]["observed_at"])
        once["evidence-events"][-1]["published_at"] = "2026-01-01"
        with self.assertRaisesRegex(ValueError, "conflicting_event_id"):
            apply_research_status_additions(once, [notice])

    def test_all_supported_statuses_append_instead_of_erasing_prior_notices(self):
        payload, template = fixture()
        notices = []
        kinds = ("withdrawn", "retracted", "corrected", "expression_of_concern", "reinstated")
        for kind in kinds:
            notice = copy.deepcopy(template)
            notice.update(notice_id="notice:" + kind, event_type=kind)
            notices.append(notice)
        result = apply_research_status_additions(payload, notices)
        self.assertEqual([row["event_type"] for row in result["works"][0]["research_status_notices"]], list(kinds))
        self.assertEqual(len(result["manifestations"]), 2)
        self.assertEqual(len(result["source-records"]), 2)

    def test_failed_late_record_leaves_every_input_table_unchanged(self):
        payload, notice = fixture()
        before = copy.deepcopy(payload)
        bad = copy.deepcopy(notice)
        bad.update(notice_id="notice:bad", work_id="missing:work")
        with self.assertRaises(ValueError):
            apply_research_status_additions(payload, [notice, bad])
        self.assertEqual(payload, before)

    def test_changed_notice_or_source_id_is_rejected_without_overwrite(self):
        payload, notice = fixture()
        original = apply_research_status_additions(payload, [notice])
        for change in (lambda row: row.update(summary_zh="同一ID下改写的状态说明。"),
                       lambda row: row["source_record"]["raw"].update(metadata_sha256="b" * 64)):
            bad, before = copy.deepcopy(notice), copy.deepcopy(original)
            change(bad)
            with self.assertRaisesRegex(ValueError, "research_status_conflicting_"):
                apply_research_status_additions(original, [bad])
            self.assertEqual(original, before)

    def test_conflicting_ids_inside_batch_are_rejected(self):
        payload, notice = fixture()
        bad = copy.deepcopy(notice)
        bad["event_type"] = "retracted"
        with self.assertRaisesRegex(ValueError, "conflicting_notice_id"):
            apply_research_status_additions(payload, [notice, bad])

    def test_existing_event_id_cannot_be_replaced(self):
        payload, notice = fixture()
        event_id = "event:research-status:" + fingerprint(notice["notice_id"])[:24]
        payload["evidence-events"].append({"event_id": event_id, "work_id": notice["work_id"], "event_type": "corrected"})
        before = copy.deepcopy(payload)
        with self.assertRaisesRegex(ValueError, "conflicting_event_id"):
            apply_research_status_additions(payload, [notice])
        self.assertEqual(payload, before)

    def test_unique_legacy_aliases_resolve_without_changing_alias_table(self):
        for alias in ("old:work", "legacy:work"):
            payload, notice = fixture()
            notice["work_id"] = alias
            result = apply_research_status_additions(payload, [notice])
            self.assertEqual(result["works"][0]["research_status_notices"][0]["work_id"], "arxiv:2606.12345")
            self.assertEqual(result["work-aliases"], payload["work-aliases"])
            self.assertEqual(apply_research_status_additions(result, [notice]), result)

    def test_ambiguous_alias_is_not_assigned_to_first_matching_work(self):
        payload, notice = fixture()
        payload["works"][1]["aliases"] = ["old:work"]
        notice["work_id"] = "old:work"
        with self.assertRaisesRegex(ValueError, "unknown_or_ambiguous_work"):
            apply_research_status_additions(payload, [notice])

    def test_arxiv_identity_conflict_is_not_overridden_by_raw_claim(self):
        payload, notice = fixture()
        notice["source_url"] = notice["source_record"]["url"] = "https://arxiv.org/abs/2606.54321v2"
        notice["source_record"]["raw"]["work_id"] = notice["work_id"]
        with self.assertRaisesRegex(ValueError, "source_work_identity_mismatch"):
            apply_research_status_additions(payload, [notice])

    def test_publisher_notice_requires_hard_subject_identity_not_title_similarity(self):
        payload, notice = fixture()
        notice["source_url"] = notice["source_record"]["url"] = "https://publisher.example/notices/withdrawal"
        notice["source_record"]["source_type"] = "official_publisher_status_notice"
        with self.assertRaisesRegex(ValueError, "source_has_no_hard_work_identity"):
            apply_research_status_additions(payload, [notice])
        notice["source_record"]["raw"]["work_identifiers"] = {"doi": "10.9999/EXAMPLE"}
        result = apply_research_status_additions(payload, [notice])
        self.assertEqual(result["works"][0]["research_status_notices"][0]["notice_id"], notice["notice_id"])
        notice["source_record"]["raw"]["work_identifiers"]["doi"] = "10.9999/other"
        with self.assertRaisesRegex(ValueError, "source_work_identity_mismatch"):
            apply_research_status_additions(payload, [notice])

    def test_publication_precision_is_preserved_without_inventing_a_day(self):
        for date, precision in (("2026-08", "month"), ("2026-08-01", "month"), ("2026", "year"),
                                ("2026-01-01", "year"), ("2026-09-05T23:59:00Z", "second")):
            payload, notice = fixture()
            notice.update(public_at=date, date_precision=precision)
            notice["source_record"]["published_at"] = date
            result = apply_research_status_additions(payload, [notice])
            event = result["evidence-events"][-1]
            self.assertEqual((event["public_at"], event["date_precision"]), (date, precision))
            self.assertEqual(result["works"][0]["first_public_date"], "2026-06-01")

    def test_dates_and_observations_must_be_consistent_utc_and_not_future(self):
        changes = (lambda row: row["source_record"].update(observed_at="2026-09-06"),
                   lambda row: row["source_record"].update(observed_at="2026-09-06T18:00:00+08:00"),
                   lambda row: row.update(public_at="2027-01-01"),
                   lambda row: row.update(public_at="2026-02-30"),
                   lambda row: row.update(public_at="2026-08-17", date_precision="month"),
                   lambda row: row["source_record"].update(published_at="2026-06-01"),
                   lambda row: row["source_record"].update(date_precision="year"),
                   lambda row: row["source_record"].update(retrieved_at="2026-09-05T00:00:00Z"))
        for change in changes:
            payload, notice = fixture()
            before = copy.deepcopy(payload)
            change(notice)
            with self.assertRaises(ValueError):
                apply_research_status_additions(payload, [notice])
            self.assertEqual(payload, before)

    def test_source_url_id_ownership_and_type_are_enforced(self):
        changes = (lambda row: row["source_record"].update(url="https://arxiv.org/abs/2606.54321"),
                   lambda row: row.update(source_record_ids=["unknown:source"]),
                   lambda row: row["source_record_ids"].append("unknown:source"),
                   lambda row: row["source_record"].update(source_type="social_post"),
                   lambda row: row.update(review_status="draft"),
                   lambda row: row.update(scope="manifestation"),
                   lambda row: row.update(notice_id=" "))
        for change in changes:
            payload, notice = fixture()
            change(notice)
            with self.assertRaises(ValueError):
                apply_research_status_additions(payload, [notice])

    def test_nonpublic_or_credentialed_urls_are_rejected(self):
        for url in ("file:///tmp/notice", "http://localhost/notice", "http://127.0.0.1/notice", "http://[::1]/notice", "https://user:token@arxiv.org/abs/2606.12345"):
            payload, notice = fixture()
            notice["source_url"] = notice["source_record"]["url"] = url
            with self.assertRaises(ValueError):
                apply_research_status_additions(payload, [notice])

    def test_nonfinite_raw_metadata_is_not_serialized_into_authority(self):
        payload, notice = fixture()
        notice["source_record"]["raw"]["bad"] = float("nan")
        with self.assertRaisesRegex(ValueError, "source_metadata_must_be_json"):
            apply_research_status_additions(payload, [notice])

    def test_changed_canonical_title_does_not_rewrite_the_recorded_event(self):
        payload, notice = fixture()
        once = apply_research_status_additions(payload, [notice])
        once["works"][0]["title"] = "Updated canonical display title"
        self.assertEqual(apply_research_status_additions(once, [notice]), once)

    def test_loader_reads_only_additions_and_leaves_files_unchanged(self):
        payload, notice = fixture()
        with tempfile.TemporaryDirectory(prefix="research-status-fixture-") as directory:
            data = Path(directory)
            path = data / "research-status-additions.jsonl"
            body = json.dumps(notice, ensure_ascii=False) + "\n"
            path.write_text(body)
            result = ingest_research_status_additions(payload, data)
            self.assertEqual(path.read_text(), body)
            self.assertEqual(list(data.iterdir()), [path])
            self.assertEqual(len(result["works"][0]["research_status_notices"]), 1)
            self.assertEqual(ingest_research_status_additions(result, data), result)


if __name__ == "__main__":
    unittest.main()
