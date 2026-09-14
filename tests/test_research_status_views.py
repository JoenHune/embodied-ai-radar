import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from research_status_views import status_work_views, status_changes, editorial_status_dependencies, latest_status_observation
import test_research_status_temporal as temporal_fixture
from test_v3_editorial import version_fixture, valid_editorial, editor


class ResearchStatusViewTests(unittest.TestCase):
    def setUp(self):
        fixture = temporal_fixture.ResearchStatusTemporalTests()
        fixture.setUp()
        self.work, self.sources, self.versions = fixture.work, fixture.sources, fixture.versions
        self.work["title"] = "Synthetic whole-body control paper"

    def test_current_notice_is_separate_from_empty_earlier_view(self):
        self.assertEqual(status_work_views([self.work], "2026-07-31", self.sources), [])
        current = status_work_views([self.work], "2026-08-31", self.sources)
        self.assertEqual(current[0]["status"], "withdrawn")
        self.assertEqual(status_changes(current, month="2026-07"), [])
        self.assertEqual(len(status_changes(current, month="2026-08")), 1)

    def test_dependency_queue_does_not_rewrite_history_or_invent_organization(self):
        editorial = {"claims": [{"claim_id": "claim:1", "supporting_ids": [self.work["work_id"]]}],
                     "direction_summaries": [{"claim_id": "claim:D5", "code": "D5", "supporting_ids": ["event:old"]}]}
        original = copy.deepcopy(editorial)
        result = editorial_status_dependencies(editorial, status_work_views([self.work], "2026-08-31", self.sources),
                                               [{"event_id": "event:old", "work_id": self.work["work_id"]}])
        self.assertEqual(len(result), 2)
        self.assertEqual(result[1]["code"], "D5")
        self.assertEqual(editorial, original)
        self.assertTrue(all("organization_id" not in row for row in result))

    def test_current_derived_metadata_is_not_leaked_into_historical_work_projection(self):
        from build_v3_catalog import dated_work_view
        current = {**self.work, "validation_eligible": False, "research_status": {"status": "withdrawn"}, "evidence_flags": {}}
        previous = dated_work_view(current, self.versions, "2026-07-31", self.sources, self.work)
        self.assertNotIn("research_status", previous)
        self.assertNotIn("validation_eligible", previous)
        self.assertTrue(previous["evidence_flags"]["real_robot"])

    def test_status_event_day_uses_shanghai_boundary(self):
        self.work["research_status_notices"][0]["public_at"] = "2026-07-31T16:30:00Z"
        self.sources[-1]["published_at"] = "2026-07-31T16:30:00Z"
        current = status_work_views([self.work], "2026-08-31", self.sources)
        self.assertEqual(len(status_changes(current, month="2026-08")), 1)
        self.assertEqual(status_changes(current, month="2026-07"), [])

    def test_current_status_clock_can_advance_without_backdating_text_or_history(self):
        self.work["research_status_notices"][0]["public_at"] = "2026-09-05T01:00:00Z"
        self.sources[-1].update(published_at="2026-09-05T01:00:00Z", observed_at="2026-09-06T10:00:00Z")
        cut = latest_status_observation([self.work], self.sources, "2026-08-31")
        self.assertEqual(cut, "2026-09-06")
        self.assertEqual(status_work_views([self.work], "2026-08-31", self.sources), [])
        self.assertEqual(status_work_views([self.work], cut, self.sources)[0]["status"], "withdrawn")

    def test_naive_or_nonofficial_observations_cannot_advance_current_clock(self):
        self.sources[-1]["observed_at"] = "2026-09-06T10:00:00"
        self.assertEqual(latest_status_observation([self.work], self.sources, "2026-08-31"), "2026-08-31")
        self.sources[-1].update(observed_at="2026-09-06T10:00:00Z", source_type="social_status_notice")
        self.assertEqual(latest_status_observation([self.work], self.sources, "2026-08-31"), "2026-08-31")

    def test_year_precision_notice_is_never_assigned_to_december(self):
        self.work["research_status_notices"][0].update(public_at="2026", date_precision="year")
        current = status_work_views([self.work], "2026-12-31", self.sources)
        self.assertEqual(len(status_changes(current)), 1)
        self.assertEqual(status_changes(current, month="2026-12"), [])


class EditorialStatusPacketTests(unittest.TestCase):
    def notice(self, catalog, when):
        work = catalog["works"][0]
        source = {"source_record_id": "source:status", "url": "https://arxiv.org/abs/2608.00404v3",
                  "source_type": "official_arxiv_status_notice", "published_at": when}
        work["source_record_ids"].append(source["source_record_id"])
        catalog["source-records"].append(source)
        work["research_status_notices"] = [{"notice_id": "notice:withdrawn", "work_id": work["work_id"],
             "event_type": "withdrawn", "scope": "work", "public_at": when, "date_precision": "second", "review_status": "verified",
             "source_record_ids": [source["source_record_id"]], "source_url": source["url"], "summary_zh": "合成撤回通知"}]
        catalog["evidence-events"].append({"event_id": "event:withdrawn", "work_id": work["work_id"], "event_type": "withdrawn",
             "published_at": when, "date_precision": "second", "url": source["url"]})

    def test_future_withdrawal_keeps_same_historical_input_digest(self):
        snapshot, catalog = version_fixture()
        before = editor.build_evidence_packet(snapshot, catalog)
        self.notice(catalog, "2026-09-10T01:00:00Z")
        after = editor.build_evidence_packet(snapshot, catalog)
        self.assertEqual(editor.editorial_input_digest(before), editor.editorial_input_digest(after))

    def test_current_withdrawal_cannot_reenter_as_event_or_experimental_card(self):
        snapshot, catalog = version_fixture()
        before = editor.build_evidence_packet(snapshot, catalog)
        previous = valid_editorial(before)
        self.notice(catalog, "2026-08-20T01:00:00Z")
        packet = editor.build_evidence_packet(snapshot, catalog)
        self.assertNotIn("work:first", [row["work_id"] for row in packet["evidence_cards"]])
        self.assertNotIn("event:withdrawn", [row["evidence_id"] for row in packet["evidence_cards"]])
        self.assertEqual(packet["withheld_research_work_ids"], ["work:first"])
        self.assertEqual(packet["sampling"]["monthly_included_works"], 2)
        with self.assertRaises(editor.EditorialError):
            editor.validate_editorial(previous, packet)


if __name__ == "__main__":
    unittest.main()
