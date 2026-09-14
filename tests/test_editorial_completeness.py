"""Monthly quality states are derived without text generation or mutation."""
from __future__ import annotations

import copy
import unittest

from scripts.editorial_completeness import (DIRECTION_CODES, QUESTION_CODES, MISSING_VERSION_SUMMARY,
                                            assess_editorial_completeness)


def fixture():
    def summary(code):
        return {"code": code, "summary": "合成来源绑定摘要。", "supporting_ids": ["fixture:" + code]}
    return {"month": "2026-06", "editorial_status": "llm_complete",
            "directions": [{"code": code, "primary_count": 1, "multi_label_count": 1} for code in DIRECTION_CODES],
            "questions": [{"code": code, "count": 1} for code in QUESTION_CODES],
            "editorial": {"status": "complete", "claims": [{"title": "合成判断", "summary": "合成摘要。", "supporting_ids": [f"fixture:{i}"]} for i in range(5)],
                          "direction_summaries": [summary(code) for code in DIRECTION_CODES],
                          "question_summaries": [summary(code) for code in QUESTION_CODES]}}


def axis(result, family, code):
    return next(row for row in result[family] if row["code"] == code)


class EditorialCompletenessTests(unittest.TestCase):
    def test_all_axes_are_fixed_order_and_source_bound(self):
        result = assess_editorial_completeness(fixture())
        self.assertEqual(result["overall_status"], "meets_target")
        self.assertEqual([row["code"] for row in result["directions"]], list(DIRECTION_CODES))
        self.assertEqual([row["code"] for row in result["questions"]], list(QUESTION_CODES))
        self.assertEqual(result["status_counts"]["source_bound_editorial"], 26)
        self.assertEqual(result["issues"], [])

    def test_generation_success_is_not_finding_count_success(self):
        for number, status in ((0, "below_target"), (4, "below_target"), (5, "in_range"), (8, "in_range"), (9, "above_target")):
            with self.subTest(number=number):
                value = fixture()
                value["editorial"]["claims"] = [copy.deepcopy(value["editorial"]["claims"][0]) for _ in range(number)]
                result = assess_editorial_completeness(value)
                self.assertEqual(result["generation_status"], "llm_complete")
                self.assertEqual(result["executive"]["status"], status)
                self.assertEqual(result["overall_status"], "meets_target" if 5 <= number <= 8 else "needs_attention")

    def test_five_empty_or_uncited_findings_do_not_satisfy_quality(self):
        value = fixture()
        value["editorial"]["claims"][0]["supporting_ids"] = []
        result = assess_editorial_completeness(value)
        self.assertEqual(result["executive"]["status"], "unbound_claims")
        self.assertEqual(result["executive"]["source_bound_count"], 4)
        self.assertEqual(result["overall_status"], "needs_attention")

    def test_december_zero_axes_do_not_require_fabricated_citations(self):
        value = fixture()
        value["month"] = "2025-12"
        value["directions"][13].update(primary_count=0, multi_label_count=0)
        value["questions"][9]["count"] = 0
        value["editorial"]["direction_summaries"] = [row for row in value["editorial"]["direction_summaries"] if row["code"] != "D14"]
        value["editorial"]["question_summaries"] = [row for row in value["editorial"]["question_summaries"] if row["code"] != "Q9"]
        result = assess_editorial_completeness(value)
        self.assertEqual(axis(result, "directions", "D14")["status"], "zero_registered")
        self.assertEqual(axis(result, "questions", "Q9")["status"], "zero_registered")
        self.assertEqual(result["overall_status"], "meets_target")
        self.assertEqual(result["status_counts"]["zero_registered"], 2)

    def test_january_record_with_missing_historical_text_is_not_zero(self):
        value = fixture()
        value["editorial"]["question_summaries"][9]["summary"] = MISSING_VERSION_SUMMARY
        result = assess_editorial_completeness(value)
        row = axis(result, "questions", "Q9")
        self.assertEqual((row["status"], row["registered_count"]), ("missing_historical_text", 1))
        self.assertTrue(result["has_missing_historical_text"])
        self.assertTrue(result["axes_complete"])  # Accounted for, not a claim that text was read.

    def test_known_record_without_editorial_is_a_real_gap_not_zero(self):
        value = fixture()
        value["editorial"]["direction_summaries"].pop(0)
        value["directions"][0]["summary"] = "本月确定主方向1项，需阅读证据。"
        result = assess_editorial_completeness(value)
        self.assertEqual(axis(result, "directions", "D1")["status"], "editorial_missing")
        self.assertEqual(result["overall_status"], "needs_attention")

    def test_zero_primary_count_cannot_hide_positive_cross_labels(self):
        value = fixture()
        value["directions"][0].update(primary_count=0, multi_label_count=3)
        value["editorial"]["direction_summaries"].pop(0)
        row = axis(assess_editorial_completeness(value), "directions", "D1")
        self.assertEqual((row["status"], row["registered_count"]), ("editorial_missing", 3))

    def test_unknown_or_invalid_counts_are_not_zero(self):
        for invalid in (None, -1, True, "0"):
            value = fixture()
            value["questions"][0]["count"] = invalid
            value["editorial"]["question_summaries"].pop(0)
            row = axis(assess_editorial_completeness(value), "questions", "Q0")
            self.assertIsNone(row["registered_count"])
            self.assertEqual(row["status"], "editorial_missing")
        value = fixture()
        value["directions"][0] = {"code": "D1", "primary_count": 0}
        value["editorial"]["direction_summaries"].pop(0)
        self.assertIsNone(axis(assess_editorial_completeness(value), "directions", "D1")["registered_count"])

    def test_missing_snapshot_axis_is_unknown_not_implicit_zero(self):
        value = fixture()
        value["directions"].pop(0)
        value["editorial"]["direction_summaries"].pop(0)
        row = axis(assess_editorial_completeness(value), "directions", "D1")
        self.assertEqual(row["status"], "editorial_missing")
        self.assertIsNone(row["registered_count"])

    def test_placeholder_is_exact_and_requires_evidence_of_a_record(self):
        value = fixture()
        row = value["editorial"]["question_summaries"][0]
        row.update(summary=MISSING_VERSION_SUMMARY, supporting_ids=[])
        value["questions"][0]["count"] = 0
        self.assertEqual(axis(assess_editorial_completeness(value), "questions", "Q0")["status"], "editorial_missing")
        row["summary"] = "缺少历史正文，不能判断。"
        value["questions"][0]["count"] = 1
        self.assertEqual(axis(assess_editorial_completeness(value), "questions", "Q0")["status"], "editorial_missing")

    def test_current_acceptance_event_can_supply_an_axis_with_zero_new_works(self):
        value = fixture()
        value["directions"][0].update(primary_count=0, multi_label_count=0)
        value["editorial"]["direction_summaries"][0]["supporting_ids"] = ["event:older-work-accepted"]
        row = axis(assess_editorial_completeness(value), "directions", "D1")
        self.assertEqual(row["status"], "source_bound_editorial")
        self.assertEqual(row["registered_count"], 0)

    def test_data_only_and_legacy_content_do_not_masquerade_as_current_editorial(self):
        for status in ("data_only", "legacy_editorial", None):
            value = fixture()
            value["editorial_status"] = status
            value["previous_editorial"] = copy.deepcopy(value["editorial"])
            value["executive_findings"] = copy.deepcopy(value["editorial"]["claims"])
            value["directions"][13].update(primary_count=0, multi_label_count=0)
            result = assess_editorial_completeness(value)
            self.assertEqual(result["overall_status"], "not_generated")
            self.assertIsNone(result["executive"]["count"])
            self.assertEqual(axis(result, "directions", "D1")["status"], "not_generated")
            self.assertEqual(axis(result, "directions", "D14")["status"], "zero_registered")

    def test_llm_label_without_raw_editorial_is_not_enough(self):
        value = fixture()
        del value["editorial"]
        value["executive_findings"] = [{}] * 5
        result = assess_editorial_completeness(value)
        self.assertEqual(result["overall_status"], "needs_attention")
        self.assertEqual(result["executive"]["status"], "editorial_missing")

    def test_duplicate_axes_are_not_silently_last_wins(self):
        value = fixture()
        value["editorial"]["direction_summaries"].append(copy.deepcopy(value["editorial"]["direction_summaries"][0]))
        result = assess_editorial_completeness(value)
        self.assertEqual(axis(result, "directions", "D1")["status"], "editorial_missing")
        self.assertTrue(any(row["code"] == "duplicate_editorial_axis" for row in result["issues"]))

    def test_input_and_nested_mutable_values_are_never_modified_or_returned(self):
        value = fixture()
        before = copy.deepcopy(value)
        result = assess_editorial_completeness(value)
        self.assertEqual(value, before)
        result["directions"][0]["code"] = "changed"
        result["executive"]["count"] = 99
        self.assertEqual(value, before)


if __name__ == "__main__":
    unittest.main()
