"""Synthetic source-bound evidence; no generated assertion becomes verified."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts import signal_evidence as signals


def fixture():
    work = {"work_id": "work:fixture", "title": "World model control", "abstract": "On a real robot, the baseline achieved 40% success and the world model achieved 60% success. Evaluation is limited to one robot.",
            "directions": ["D3"], "questions": ["Q1"], "source_record_ids": ["source:fixture"]}
    source = {"source_record_id": "source:fixture", "url": "https://example.test/paper", "published_at": "2026-08-04"}
    card = {**work, "evidence_id": work["work_id"], "source_content_digest": signals.source_content_digest(work),
            "source_documents": [{**source, "public_at": source["published_at"], "public_at_precision": "day"}]}
    assessment = {"signal_id": "S1", "work_id": work["work_id"], "evidence_card_id": work["work_id"], "stance": "supports", "statement": "报告在真机设置中比较了基线与世界模型策略，仍需独立核验。",
                  "source_url": source["url"], "source_record_ids": [source["source_record_id"]], "public_at": source["published_at"], "public_at_precision": "day",
                  "research_scope": "in_scope", "experiment": {"setting": "On a real robot", "baseline": "the baseline", "metric": "60% success", "limitations": ["Evaluation is limited to one robot."]},
                  "source_spans": [{"field": "abstract", "start": 0, "end": len(work["abstract"]), "quote": work["abstract"]}]}
    draft = signals.make_signal_draft(assessment, card, month="2026-08", model="gpt-5.6-sol", generated_at="2026-09-05T00:00:00Z", input_digest="a" * 64)
    return work, source, card, assessment, draft


class SignalEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.work, self.source, self.card, self.assessment, self.draft = fixture()

    def test_complete_draft_is_valid_but_never_verified(self):
        self.assertEqual(signals.validate_signal_record(self.draft, self.work, [self.source]), [])
        self.assertEqual(self.draft["review_status"], "draft")
        self.assertEqual(self.draft["review_history"], [])

    def test_automatic_response_cannot_supply_verified_or_review_history(self):
        for field, value in [("review_status", "verified"), ("review_history", [])]:
            row = {**self.assessment, field: value}
            self.assertEqual(signals.assessment_errors(row, self.card), ["assessment_schema_invalid"])

    def test_ids_facets_and_source_url_cannot_be_invented(self):
        for field, value, reason in [("work_id", "other", "evidence_card_mismatch"), ("signal_id", "S99", "unknown_signal"),
                                     ("signal_id", "S5", "signal_outside_card_facets"), ("source_url", "https://evil.test", "source_not_bound_to_card"),
                                     ("source_record_ids", ["source:other"], "source_not_bound_to_card")]:
            self.assertIn(reason, signals.assessment_errors({**self.assessment, field: value}, self.card))

    def test_wrong_span_numeric_or_experiment_constraints_fail(self):
        mutations = [(lambda row: row["source_spans"][0].update(start=1), "source_span_mismatch"),
                     (lambda row: row["experiment"].update(metric="99% success"), "experiment_not_verbatim_source"),
                     (lambda row: row.update(statement="成功率达到99%。"), "statement_number_not_in_source"),
                     (lambda row: row.update(statement="有三个机器人支持结果。"), "statement_number_not_in_source")]
        for mutate, expected in mutations:
            row = copy.deepcopy(self.assessment)
            mutate(row)
            self.assertIn(expected, signals.assessment_errors(row, self.card))

    def test_neutral_can_use_title_with_missing_experiment(self):
        row = {**self.assessment, "stance": "neutral", "experiment": {"setting": None, "baseline": None, "metric": None, "limitations": []},
               "source_spans": [{"field": "title", "start": 0, "end": len(self.work["title"]), "quote": self.work["title"]}]}
        self.assertEqual(signals.assessment_errors(row, self.card), [])
        row["stance"] = "contradicts"
        self.assertIn("directional_assessment_requires_abstract", signals.assessment_errors(row, self.card))

    def test_source_dates_must_match_and_unknown_is_not_guessed(self):
        row = {**self.assessment, "public_at": "2026-07-01"}
        self.assertIn("source_public_date_mismatch", signals.assessment_errors(row, self.card))
        row = {**self.assessment, "public_at": None, "public_at_precision": "unknown"}
        card = copy.deepcopy(self.card)
        card["source_documents"][0].update(public_at=None, public_at_precision="unknown")
        self.assertEqual(signals.assessment_errors(row, card), [])
        forged = copy.deepcopy(self.draft)
        forged["public_at"] = "2026-07-01"
        forged["content_digest"] = signals.record_content_digest(forged)
        self.assertIn("source_record_public_date_mismatch", signals.validate_signal_record(forged, self.work, [self.source]))

    def test_verified_requires_explicit_named_semantic_review(self):
        row = {**self.draft, "review_status": "verified"}
        self.assertIn("semantic_review_required", signals.validate_signal_record(row, self.work, [self.source]))
        with self.assertRaises(ValueError):
            signals.review_signal_record(self.draft, reviewer="Fixture reviewer", note="Reviewed experiment and inference", reviewed_at="2026-09-05T02:00:00Z")
        reviewed = self.review()
        self.assertEqual(signals.validate_signal_record(reviewed, self.work, [self.source]), [])

    def review(self):
        return signals.review_signal_record(self.draft, reviewer="Fixture reviewer", note="Read exact experimental statement and checked its relevance to the signal", reviewed_at="2026-09-05T02:00:00Z", semantic_check_completed=True)

    def test_same_month_rerun_is_idempotent_and_preserves_human_changes(self):
        later = copy.deepcopy(self.draft)
        later["updated_at"] = "2026-09-06T00:00:00Z"
        self.assertEqual(signals.merge_signal_drafts([self.draft], [later], "2026-08"), [self.draft])
        human = copy.deepcopy(self.draft)
        human["statement"] = "人工修订尚未再次核验。"
        self.assertEqual(signals.merge_signal_drafts([human], [later], "2026-08"), [human])
        self.assertEqual(signals.merge_signal_drafts([self.review()], [], "2026-08"), [self.review()])
        self.assertEqual(signals.merge_signal_drafts([self.draft], [], "2026-08"), [])

    def test_human_reviewed_draft_and_other_months_are_preserved(self):
        reviewed = signals.review_signal_record(self.draft, reviewer="Tester", note="Needs more source checks", reviewed_at="2026-09-05T02:00:00Z", decision="draft")
        self.assertEqual(signals.merge_signal_drafts([reviewed], [], "2026-08"), [reviewed])
        self.assertEqual(signals.merge_signal_drafts([self.draft], [], "2026-09"), [self.draft])
        with self.assertRaises(ValueError):
            signals.merge_signal_drafts([], [self.review()], "2026-08")

    def test_source_changed_preserves_historical_review_but_invalidates_draft(self):
        work = {**self.work, "abstract": "A corrected abstract."}
        self.assertIn("canonical_source_changed", signals.validate_signal_record(self.draft, work, [self.source]))
        self.assertEqual(signals.validate_signal_record(self.review(), work, [self.source]), [])
        tampered = copy.deepcopy(self.review())
        tampered["source_text_snapshot"]["abstract"] += " tampered"
        self.assertIn("record_content_changed_requires_review", signals.validate_signal_record(tampered, work, [self.source]))

    def test_source_must_belong_to_work_and_match_url(self):
        self.assertIn("source_not_owned_by_work", signals.validate_signal_record(self.draft, {**self.work, "source_record_ids": []}, [self.source]))
        self.assertIn("source_record_url_mismatch", signals.validate_signal_record(self.draft, self.work, [{**self.source, "url": "https://example.test/other"}]))

    def test_historical_draft_can_use_archived_version_digest_without_promotion(self):
        source = {**self.source, "source_type": "official_arxiv_version_metadata", "text_content_digest": signals.source_content_digest(self.work)}
        revised = {**self.work, "title": "New title", "abstract": "Changed current abstract."}
        self.assertEqual(signals.validate_signal_record(self.draft, revised, [source]), [])
        self.assertEqual(self.draft["review_status"], "draft")
        self.assertEqual(self.draft["review_history"], [])
        self.assertIn("source_record_public_date_mismatch", signals.validate_signal_record(self.draft, revised, [{**source, "published_at": "2026-09-01"}]))
        self.assertIn("source_record_url_mismatch", signals.validate_signal_record(self.draft, revised, [{**source, "url": "https://wrong.test"}]))
        self.assertIn("canonical_source_changed", signals.validate_signal_record(self.draft, revised, [{**source, "text_content_digest": "b" * 64}]))

    def test_archived_snapshot_fallback_matches_exact_original_text(self):
        source = {**self.source, "source_type": "official_arxiv_version_metadata", "archived_text_snapshot": {"title": self.work["title"], "abstract": self.work["abstract"]}}
        revised = {**self.work, "abstract": "Later abstract."}
        self.assertEqual(signals.validate_signal_record(self.draft, revised, [source]), [])
        forged = copy.deepcopy(self.draft)
        forged["source_text_snapshot"]["abstract"] += " Invented sentence."
        forged["source_text_digest"] = signals.digest(forged["source_text_snapshot"])
        forged["content_digest"] = signals.record_content_digest(forged)
        self.assertIn("canonical_source_changed", signals.validate_signal_record(forged, revised, [source]))

    def test_truncated_historical_draft_requires_full_archive_not_only_full_hash(self):
        work = {**self.work, "abstract": self.work["abstract"] + " Extra source sentence." * 200}
        card = {**self.card, "abstract": work["abstract"][:3500], "source_content_digest": signals.source_content_digest(work)}
        draft = signals.make_signal_draft(self.assessment, card, month="2026-08", model="gpt-5.6-sol", generated_at="2026-09-05T00:00:00Z", input_digest="a" * 64)
        revised = {**work, "abstract": "New abstract."}
        source = {**self.source, "source_type": "official_arxiv_version_metadata", "text_content_digest": signals.source_content_digest(work)}
        self.assertIn("canonical_source_changed", signals.validate_signal_record(draft, revised, [source]))
        source["archived_text_snapshot"] = {"title": work["title"], "abstract": work["abstract"]}
        self.assertEqual(signals.validate_signal_record(draft, revised, [source]), [])

    def test_current_canonical_digest_cannot_authenticate_an_invented_excerpt(self):
        forged = copy.deepcopy(self.draft)
        forged["source_text_snapshot"]["abstract"] += " Invented source sentence."
        forged["source_text_digest"] = signals.digest(forged["source_text_snapshot"])
        forged["content_digest"] = signals.record_content_digest(forged)
        self.assertIn("source_excerpt_not_bound_to_original", signals.validate_signal_record(forged, self.work, [self.source]))

    def test_loader_retains_invalid_queue_and_overlay_never_mutates_work(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.jsonl"
            path.write_text(json.dumps(self.draft) + "\n" + "not-json\n")
            report = signals.load_signal_evidence(path, works=[self.work], source_records=[self.source])
            self.assertEqual(report["counts"], {"total": 2, "verified": 0, "draft": 1, "invalid": 1})
            before = copy.deepcopy(self.work)
            output = signals.overlay_signal_evidence([self.work], report["records"])
            self.assertEqual(output[0]["signal_evidence"], [self.draft])
            self.assertEqual(before, self.work)
            path.write_text((json.dumps(self.draft) + "\n") * 2)
            self.assertEqual(signals.load_signal_evidence(path, works=[self.work])["counts"]["invalid"], 2)


if __name__ == "__main__":
    unittest.main()
