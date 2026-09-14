"""Pure notice fixtures: no network or authority mutations."""
import ast
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from research_status import research_status_as_of


def fixture(events):
    work = {"work_id": "work:research", "aliases": ["arxiv:2607.04837"], "source_record_ids": [],
            "research_status_notices": [], "strict_peer_reviewed": True, "evidence_grade": "E3"}
    sources = []
    for index, (kind, when, precision) in enumerate(events):
        sid, url = f"source:{index}", f"https://example.test/notices/{index}"
        work["source_record_ids"].append(sid)
        work["research_status_notices"].append({"notice_id": f"notice:{index}", "event_type": kind, "scope": "work",
            "public_at": when, "date_precision": precision, "source_record_ids": [sid], "source_url": url,
            "review_status": "verified", "summary_zh": "来源明确披露的研究状态通知。"})
        sources.append({"source_record_id": sid, "url": url, "source_type": "official_publisher_status_notice"})
    return work, sources


class ResearchStatusTests(unittest.TestCase):
    def test_no_notices_is_active_without_top_level_temporal_import(self):
        work, sources = fixture([])
        self.assertEqual(research_status_as_of(work, "2026-08", sources),
                         {"status": "active", "validation_eligible": True, "notices": [], "information_gaps": []})
        tree = ast.parse((ROOT / "scripts/research_status.py").read_text())
        self.assertFalse(any(isinstance(node, ast.ImportFrom) and "temporal_evidence" in (node.module or "") for node in tree.body))

    def test_withdrawal_is_time_aware_and_does_not_edit_raw_evidence(self):
        work, sources = fixture([("withdrawn", "2026-08-24T07:00:55Z", "second")])
        before = copy.deepcopy((work, sources))
        july = research_status_as_of(work, "2026-07", sources)
        self.assertEqual(july, {"status": "active", "validation_eligible": True, "notices": [], "information_gaps": []})
        august = research_status_as_of(work, "2026-08", sources)
        self.assertEqual(august["status"], "withdrawn")
        self.assertFalse(august["validation_eligible"])
        self.assertEqual(august["notices"], work["research_status_notices"])
        self.assertEqual((work, sources), before)

    def test_retraction_is_not_cleared_by_correction_or_concern(self):
        work, sources = fixture([("retracted", "2026-08-10", "day"), ("corrected", "2026-08-12", "day"),
                                 ("expression_of_concern", "2026-08-14", "day")])
        result = research_status_as_of(work, "2026-08", sources)
        self.assertEqual(result["status"], "retracted")
        self.assertFalse(result["validation_eligible"])
        self.assertEqual(len(result["notices"]), 3)

    def test_unreinstated_retraction_remains_stronger_than_later_withdrawal(self):
        work, sources = fixture([("retracted", "2026-08-10", "day"), ("withdrawn", "2026-08-12", "day")])
        self.assertEqual(research_status_as_of(work, "2026-08", sources)["status"], "retracted")

    def test_correction_and_concern_warn_but_do_not_block(self):
        for kind in ["corrected", "expression_of_concern"]:
            work, sources = fixture([(kind, "2026-08-10", "day")])
            result = research_status_as_of(work, "2026-08", sources)
            self.assertEqual(result["status"], kind)
            self.assertTrue(result["validation_eligible"])
            self.assertEqual(len(result["notices"]), 1)

    def test_dated_reinstatement_restores_but_keeps_all_notices(self):
        work, sources = fixture([("withdrawn", "2026-08-10", "day"), ("corrected", "2026-08-11", "day"),
                                 ("reinstated", "2026-08-12", "day")])
        result = research_status_as_of(work, "2026-08", sources)
        self.assertEqual(result["status"], "active")
        self.assertTrue(result["validation_eligible"])
        self.assertEqual(len(result["notices"]), 3)

    def test_later_withdrawal_reblocks_after_reinstatement(self):
        work, sources = fixture([("withdrawn", "2026-08-10", "day"), ("reinstated", "2026-08-12", "day"),
                                 ("withdrawn", "2026-08-13", "day")])
        self.assertFalse(research_status_as_of(work, "2026-08", sources)["validation_eligible"])

    def test_future_notices_add_neither_fact_nor_gap_even_without_sources(self):
        work, sources = fixture([("withdrawn", "2026-09-04", "day")])
        for records in [None, sources, []]:
            result = research_status_as_of(work, "2026-08", records)
            self.assertTrue(result["validation_eligible"])
            self.assertEqual(result["notices"], [])
            self.assertEqual(result["information_gaps"], [])
        work, sources = fixture([("withdrawn", "2026-08-10", "day"), ("reinstated", "2026-09-04", "day")])
        self.assertEqual(research_status_as_of(work, "2026-08", sources)["status"], "withdrawn")
        self.assertEqual(research_status_as_of(work, "2026-09", sources)["status"], "active")

    def test_unknown_date_cannot_block_or_reinstate(self):
        work, sources = fixture([("withdrawn", None, "unknown")])
        result = research_status_as_of(work, "2026-08", sources)
        self.assertTrue(result["validation_eligible"])
        self.assertEqual(result["notices"], [])
        self.assertEqual(result["information_gaps"][0]["reason"], "notice_date_unknown_or_invalid")
        work, sources = fixture([("withdrawn", "2026-08-10", "day"), ("reinstated", "2026-08-11", "unknown")])
        self.assertEqual(research_status_as_of(work, "2026-08", sources)["status"], "withdrawn")

    def test_naive_malformed_or_wrong_precision_dates_are_not_invented(self):
        for when, precision in [("2026-08-10T12:00:00", "second"), ("2026-08", "day"), ("2026-13", "month"),
                                ("2026-08-35", "day"), ("2026-08-10", "invented")]:
            work, sources = fixture([("withdrawn", when, precision)])
            result = research_status_as_of(work, "2026-12", sources)
            self.assertTrue(result["validation_eligible"])
            self.assertTrue(result["information_gaps"])

    def test_month_year_and_date_only_are_available_at_interval_end(self):
        work, sources = fixture([("withdrawn", "2026-08-01", "month")])
        self.assertTrue(research_status_as_of(work, "2026-08-20", sources)["validation_eligible"])
        self.assertFalse(research_status_as_of(work, "2026-08-31", sources)["validation_eligible"])
        work, sources = fixture([("withdrawn", "2026", "year")])
        self.assertTrue(research_status_as_of(work, "2026-11", sources)["validation_eligible"])
        self.assertFalse(research_status_as_of(work, "2026-12-31", sources)["validation_eligible"])

    def test_shanghai_month_boundary_and_exact_timestamp_cutoff(self):
        work, sources = fixture([("withdrawn", "2026-08-31T16:00:00Z", "second")])
        self.assertTrue(research_status_as_of(work, "2026-08-31", sources)["validation_eligible"])
        self.assertFalse(research_status_as_of(work, "2026-09-01", sources)["validation_eligible"])
        self.assertTrue(research_status_as_of(work, "2026-08-31T15:59:59Z", sources)["validation_eligible"])
        self.assertFalse(research_status_as_of(work, "2026-08-31T16:00:00Z", sources)["validation_eligible"])

    def test_same_day_unordered_conflict_is_blocked_ambiguous_and_order_independent(self):
        work, sources = fixture([("withdrawn", "2026-08-24", "day"), ("reinstated", "2026-08-24", "day")])
        result = research_status_as_of(work, "2026-08", sources)
        self.assertFalse(result["validation_eligible"])
        gap = next(row for row in result["information_gaps"] if row["reason"] == "ambiguous_status_notice_order")
        self.assertTrue(gap["ambiguous"])
        self.assertTrue(gap["validation_blocked"])
        work["research_status_notices"].reverse()
        self.assertEqual(research_status_as_of(work, "2026-08", sources), result)

    def test_same_day_exact_clock_order_can_reinstate(self):
        work, sources = fixture([("withdrawn", "2026-08-24T01:00:00Z", "second"),
                                 ("reinstated", "2026-08-24T02:00:00Z", "second")])
        self.assertFalse(research_status_as_of(work, "2026-08-24T01:30:00Z", sources)["validation_eligible"])
        result = research_status_as_of(work, "2026-08-24T02:00:00Z", sources)
        self.assertEqual(result["status"], "active")
        self.assertEqual(result["information_gaps"], [])

    def test_equal_instants_and_month_overlap_remain_ambiguous(self):
        work, sources = fixture([("withdrawn", "2026-08-24T01:00:00Z", "second"),
                                 ("reinstated", "2026-08-24T01:00:00Z", "second")])
        self.assertFalse(research_status_as_of(work, "2026-08", sources)["validation_eligible"])
        work, sources = fixture([("withdrawn", "2026-08", "month"), ("reinstated", "2026-08-25", "day"),
                                 ("reinstated", "2026-09-01", "day")])
        august = research_status_as_of(work, "2026-08", sources)
        self.assertFalse(august["validation_eligible"])
        self.assertTrue(any(row.get("ambiguous") for row in august["information_gaps"]))
        september = research_status_as_of(work, "2026-09", sources)
        self.assertTrue(september["validation_eligible"])
        self.assertFalse(any(row.get("ambiguous") for row in september["information_gaps"]))

    def test_unverified_notice_is_only_a_gap(self):
        work, sources = fixture([("withdrawn", "2026-08-10", "day")])
        work["research_status_notices"][0]["review_status"] = "draft"
        result = research_status_as_of(work, "2026-08", sources)
        self.assertTrue(result["validation_eligible"])
        self.assertEqual(result["notices"], [])
        self.assertEqual(result["information_gaps"][0]["reason"], "notice_not_verified")

    def test_owned_ordinary_paper_or_social_source_cannot_assert_status(self):
        for kind in ["arxiv", "official_arxiv_version_metadata", "social_post", None]:
            work, sources = fixture([("withdrawn", "2026-08-10", "day")])
            sources[0]["source_type"] = kind
            result = research_status_as_of(work, "2026-08", sources)
            self.assertTrue(result["validation_eligible"])
            self.assertEqual(result["information_gaps"][0]["reason"], "notice_source_not_official_status_notice")

    def test_foreign_missing_mismatched_or_unprovided_source_cannot_form_fact(self):
        for case in ["foreign", "missing", "wrong_url", "wrong_identity", "no_map"]:
            work, sources = fixture([("withdrawn", "2026-08-10", "day")])
            if case == "foreign":
                work["source_record_ids"] = []
            elif case == "missing":
                sources = []
            elif case == "wrong_url":
                sources[0]["url"] = "https://example.test/unrelated"
            elif case == "wrong_identity":
                sources = {sources[0]["source_record_id"]: {**sources[0], "source_record_id": "other"}}
            else:
                sources = None
            result = research_status_as_of(work, "2026-08", sources)
            self.assertTrue(result["validation_eligible"], case)
            self.assertEqual(result["notices"], [])
            self.assertTrue(result["information_gaps"])

    def test_wrong_work_and_scope_rejected_historical_alias_allowed(self):
        work, sources = fixture([("withdrawn", "2026-08-10", "day")])
        notice = work["research_status_notices"][0]
        notice["work_id"] = "wrong"
        self.assertTrue(research_status_as_of(work, "2026-08", sources)["validation_eligible"])
        notice["work_id"] = "arxiv:2607.04837"
        self.assertFalse(research_status_as_of(work, "2026-08", sources)["validation_eligible"])
        notice["scope"] = "manifestation"
        self.assertTrue(research_status_as_of(work, "2026-08", sources)["validation_eligible"])

    def test_source_record_owned_by_other_work_rejected(self):
        work, sources = fixture([("withdrawn", "2026-08-10", "day")])
        sources[0]["work_id"] = "wrong"
        self.assertTrue(research_status_as_of(work, "2026-08", sources)["validation_eligible"])

    def test_bad_reinstatement_never_clears_previous_block(self):
        for failure in ["draft", "unknown_date", "wrong_source"]:
            work, sources = fixture([("withdrawn", "2026-08-10", "day"), ("reinstated", "2026-08-12", "day")])
            if failure == "draft":
                work["research_status_notices"][1]["review_status"] = "draft"
            elif failure == "unknown_date":
                work["research_status_notices"][1]["date_precision"] = "unknown"
            else:
                sources[1]["source_type"] = "social_post"
            self.assertFalse(research_status_as_of(work, "2026-08", sources)["validation_eligible"])

    def test_warning_conflict_is_visible_without_automatic_retraction(self):
        work, sources = fixture([("corrected", "2026-08-10", "day"), ("expression_of_concern", "2026-08-10", "day")])
        result = research_status_as_of(work, "2026-08", sources)
        self.assertTrue(result["validation_eligible"])
        self.assertEqual(result["status"], "expression_of_concern")
        self.assertTrue(any(row.get("ambiguous") for row in result["information_gaps"]))

    def test_output_is_copy_and_retains_all_available_notice_types(self):
        work, sources = fixture([("withdrawn", "2026-08-10", "day"), ("corrected", "2026-08-11", "day"),
                                 ("reinstated", "2026-08-12", "day"), ("expression_of_concern", "2026-08-13", "day")])
        result = research_status_as_of(work, "2026-08", sources)
        self.assertEqual(result["status"], "expression_of_concern")
        self.assertEqual(len(result["notices"]), 4)
        result["notices"][0]["summary_zh"] = "changed"
        self.assertNotEqual(work["research_status_notices"][0]["summary_zh"], "changed")


if __name__ == "__main__":
    unittest.main()
