import copy
import unittest

from scripts.compile_signal_reading import compile_reading, merge_reading
from scripts.signal_evidence import merge_signal_drafts
from tests.test_signal_evidence import fixture


class CompileSignalReadingTests(unittest.TestCase):
    def setUp(self):
        work, source, card, assessment, _ = fixture()
        self.packet = {"month": "2026-08", "evidence_cards": [card]}
        self.catalog = {"works": [work], "source-records": [source]}
        self.reading = {"month": "2026-08", "origin": "codex_session_source_reading", "model": None,
                        "reviewed_at": "2026-09-05T00:00:00Z", "reviewer": "Codex AI source check; not a human review",
                        "assessments": [{key: assessment[key] for key in ("work_id", "signal_id", "stance", "statement", "source_url", "experiment")} | {
                            "quotes": [work["abstract"]], "note": "AI reading, not a human approval."}]}

    def compile(self):
        return compile_reading(self.reading, self.packet, self.catalog)

    def test_real_source_reading_is_draft_with_explicit_ai_provenance(self):
        [row] = self.compile()
        self.assertEqual(row["review_status"], "draft")
        self.assertIsNone(row["model"])
        self.assertEqual(row["review_history"][-1]["decision"], "draft")
        self.assertIn("not a human", row["review_history"][-1]["reviewer"])

    def test_rerun_is_idempotent_and_llm_cannot_erase_reading(self):
        rows = self.compile()
        self.assertEqual(merge_reading(rows, self.compile()), rows)
        self.assertEqual(merge_signal_drafts(rows, [], "2026-08"), rows)

    def test_changed_assessment_needs_explicit_revision(self):
        original = self.compile()
        self.reading["assessments"][0]["statement"] = "Another interpretation."
        with self.assertRaisesRegex(ValueError, "requires_revision"):
            merge_reading(original, self.compile())

    def test_unrelated_packet_change_preserves_original_reading_provenance(self):
        original = self.compile()
        self.packet["coverage"] = {"included_works": 999}
        incoming = self.compile()
        self.assertNotEqual(original[0]["input_digest"], incoming[0]["input_digest"])
        self.assertEqual(merge_reading(original, incoming), original)

    def test_explicit_ai_revision_keeps_prior_interpretation_and_creation_date(self):
        original = self.compile()
        self.reading["reviewed_at"] = "2026-09-05T01:00:00Z"
        self.reading["assessments"][0].update(stance="neutral", statement="Only part of the question was tested.", note="AI corrected the interpretation scope.")
        with self.assertRaisesRegex(ValueError, "requires_revision"):
            merge_reading(original, self.compile())
        revised = merge_reading(original, self.compile(), allow_revision=True)[0]
        self.assertEqual(revised["stance"], "neutral")
        self.assertEqual(revised["review_status"], "draft")
        self.assertEqual(revised["created_at"], original[0]["created_at"])
        self.assertEqual(len(revised["review_history"]), 2)
        self.assertIn(original[0]["statement"], revised["review_history"][-1]["note"])
        self.assertEqual(merge_reading([revised], self.compile()), [revised])

    def test_ai_revision_cannot_replace_human_review(self):
        original = self.compile()
        original[0]["review_history"][-1]["reviewer"] = "Human editor"
        self.reading["reviewed_at"] = "2026-09-05T01:00:00Z"
        self.reading["assessments"][0]["stance"] = "neutral"
        with self.assertRaisesRegex(ValueError, "requires_revision"):
            merge_reading(original, self.compile(), allow_revision=True)

    def test_clock_only_refresh_does_not_add_a_review(self):
        original = self.compile()
        self.reading["reviewed_at"] = "2026-09-05T01:00:00Z"
        self.assertEqual(merge_reading(original, self.compile()), original)

    def test_human_or_responses_identity_cannot_be_forged(self):
        for field, value in [("reviewer", "Human reviewer"), ("origin", "responses_api"), ("model", "invented-model"), ("month", "2026-09")]:
            row = copy.deepcopy(self.reading)
            row[field] = value
            with self.assertRaisesRegex(ValueError, "origin_or_month"):
                compile_reading(row, self.packet, self.catalog)

    def test_review_time_must_be_valid_utc_and_not_future(self):
        for value in ["2999-01-01T00:00:00Z", "not-a-date", "2026-09-05T00:00:00", "2026-09-05T00:00:00+08:00"]:
            row = {**self.reading, "reviewed_at": value}
            with self.assertRaisesRegex(ValueError, "review_date_invalid"):
                compile_reading(row, self.packet, self.catalog)

    def test_unavailable_version_or_unowned_source_is_rejected(self):
        self.packet["evidence_cards"][0]["experimental_text_available"] = False
        with self.assertRaisesRegex(ValueError, "source_text_unavailable"):
            self.compile()
        self.packet["evidence_cards"][0]["experimental_text_available"] = True
        self.catalog["works"][0]["source_record_ids"] = []
        with self.assertRaisesRegex(ValueError, "source_not_owned_by_work"):
            self.compile()

    def test_invented_quote_or_metric_is_rejected(self):
        self.reading["assessments"][0]["quotes"] = ["Never occurred in the archived abstract"]
        with self.assertRaisesRegex(ValueError, "quote_not_in_archived"):
            self.compile()

    def test_duplicate_reading_cannot_inflate_records(self):
        self.reading["assessments"] *= 2
        with self.assertRaisesRegex(ValueError, "duplicate_record"):
            self.compile()


if __name__ == "__main__":
    unittest.main()
