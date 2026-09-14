import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
from apply_editorial_review import apply_editorial_review, main, _reviewed_localizations
from test_v3_editorial import evidence_fixture, valid_editorial, editor


def fixture():
    snapshot, catalog = evidence_fixture()
    packet = editor.build_evidence_packet(snapshot, catalog)
    artifact = {**valid_editorial(packet), "status": "complete", "schema_version": "3", "month": packet["month"],
                "model": "gpt-5.6-sol", "response_id": "resp_real_fixture", "input_digest": editor.editorial_input_digest(packet),
                "generated_at": "2026-09-06T06:00:00Z", "signal_evidence_record_ids": [], "localization_work_ids": packet["required_localization_ids"]}
    for section in editor.PROSE_SECTIONS:
        for index, row in enumerate(artifact[section]):
            row["claim_id"] = f"claim:{packet['month']}:llm:{section}:{index + 1}"
    review = {"review_id": "review:august:fixture", "reviewer": "Codex source audit", "reviewer_kind": "ai", "reviewed_at": "2026-09-06T07:00:00Z",
              "parent_artifact_digest": editor.digest(artifact), "parent_response_id": artifact["response_id"], "input_digest": artifact["input_digest"],
              "edits": [{"op": "replace", "path": "/claims/0/summary", "before": artifact["claims"][0]["summary"],
                         "after": "现有摘要只支持限定实验条件下的研究判断。", "evidence_ids": ["work:first"], "reason": "区分摘要范围与完整实验。"}]}
    return artifact, review, packet


class EditorialReviewTests(unittest.TestCase):
    def test_pure_review_retains_response_and_evidence_identity(self):
        artifact, review, packet = fixture()
        before = copy.deepcopy((artifact, review, packet))
        result = apply_editorial_review(artifact, review, packet)
        self.assertEqual((artifact, review, packet), before)
        self.assertEqual(result["claims"][0]["summary"], review["edits"][0]["after"])
        for key in ["month", "model", "response_id", "input_digest", "generated_at", "signal_assessments", "signal_evidence_record_ids"]:
            self.assertEqual(result[key], artifact[key])
        receipt = result["post_edit_reviews"][0]
        self.assertEqual(receipt["edits"], review["edits"])
        self.assertEqual(receipt["label"], "AI内容审校")
        self.assertFalse(receipt["independent_validation"])
        self.assertEqual(receipt["generation_provenance"], "post_edit_not_new_model_response")

    def test_same_review_id_is_idempotent_conflicting_content_rejected(self):
        artifact, review, packet = fixture()
        result = apply_editorial_review(artifact, review, packet)
        self.assertEqual(result, apply_editorial_review(result, review, packet))
        changed = copy.deepcopy(review)
        changed["edits"][0]["reason"] = "不同内容"
        with self.assertRaisesRegex(ValueError, "review_id_conflict"):
            apply_editorial_review(result, changed, packet)

    def test_exact_parent_response_packet_and_before_required(self):
        for key, value, message in [("parent_response_id", "other", "parent_response"), ("input_digest", "0" * 64, "packet_changed"),
                                    ("parent_artifact_digest", "0" * 64, "parent_artifact")]:
            artifact, review, packet = fixture()
            review[key] = value
            with self.assertRaisesRegex(ValueError, message):
                apply_editorial_review(artifact, review, packet)
        artifact, review, packet = fixture()
        review["edits"][0]["before"] = "stale value"
        with self.assertRaisesRegex(ValueError, "before_mismatch"):
            apply_editorial_review(artifact, review, packet)

    def test_protected_metadata_numeric_and_signal_paths_rejected(self):
        for path in ["/month", "/model", "/response_id", "/input_digest", "/claims/0/numeric_claims", "/signal_assessments",
                     "/localizations/0/source_ids", "/localizations/0/work_id", "/claims/-", "/claims/00/summary"]:
            artifact, review, packet = fixture()
            review["edits"][0]["path"] = path
            with self.assertRaisesRegex(ValueError, "path_not_editable"):
                apply_editorial_review(artifact, review, packet)

    def test_whole_row_cannot_smuggle_changed_numeric_facts(self):
        artifact, review, packet = fixture()
        old = artifact["claims"][0]
        new = copy.deepcopy(old)
        new["numeric_claims"] = [{"metric": "coverage.included_works", "value": 2, "unit": "count", "evidence_ids": ["work:first"]}]
        review["edits"][0].update(path="/claims/0", before=copy.deepcopy(old), after=new)
        with self.assertRaisesRegex(ValueError, "cannot_change_numeric"):
            apply_editorial_review(artifact, review, packet)

    def test_append_referenced_failure_boundary_generates_stable_claim_id(self):
        artifact, review, packet = fixture()
        row = {key: value for key, value in artifact["claims"][0].items() if key != "claim_id"}
        row.update(title="失败边界", summary="该来源的摘要只支持有限范围的边界说明。")
        review["edits"][0].update(path="/counterevidence", before=[], after=[row])
        result = apply_editorial_review(artifact, review, packet)
        self.assertTrue(result["counterevidence"][0]["claim_id"].startswith("claim:2026-08:review:"))
        self.assertEqual(result, apply_editorial_review(artifact, review, packet))
        self.assertEqual(result["post_edit_reviews"][0]["edits"][0]["after"], [row])

    def test_array_append_preserves_unchanged_old_claim_identity(self):
        artifact, review, packet = fixture()
        added = {key: value for key, value in artifact["claims"][0].items() if key != "claim_id"}
        added.update(title="失败边界", summary="在来源给定条件内描述失败边界。")
        review["edits"][0].update(path="/claims", before=copy.deepcopy(artifact["claims"]), after=[*copy.deepcopy(artifact["claims"]), added])
        result = apply_editorial_review(artifact, review, packet)
        self.assertEqual(result["claims"][0], artifact["claims"][0])
        self.assertTrue(result["claims"][1]["claim_id"].startswith("claim:2026-08:review:"))

    def test_utc_offset_format_allowed_but_naive_or_non_utc_rejected(self):
        artifact, review, packet = fixture()
        review["reviewed_at"] = "2026-09-06T07:00:00+00:00"
        apply_editorial_review(artifact, review, packet)
        for when in ["2026-09-06T07:00:00", "2026-09-06T07:00:00+08:00"]:
            review["reviewed_at"] = when
            with self.assertRaisesRegex(ValueError, "must_be_utc"):
                apply_editorial_review(artifact, review, packet)

    def test_unknown_unrelated_and_sourceless_review_evidence_rejected(self):
        artifact, review, packet = fixture()
        review["edits"][0]["evidence_ids"] = ["unknown"]
        with self.assertRaisesRegex(ValueError, "evidence_id_unknown"):
            apply_editorial_review(artifact, review, packet)
        review["edits"][0]["evidence_ids"] = ["work:second"]
        with self.assertRaisesRegex(ValueError, "unrelated_to_edited_claim"):
            apply_editorial_review(artifact, review, packet)
        review["edits"][0]["evidence_ids"] = ["work:first"]
        next(row for row in packet["evidence_cards"] if row["evidence_id"] == "work:first")["source_record_ids"] = []
        artifact["input_digest"] = review["input_digest"] = editor.editorial_input_digest(packet)
        review["parent_artifact_digest"] = editor.digest(artifact)
        with self.assertRaisesRegex(ValueError, "no_source_id"):
            apply_editorial_review(artifact, review, packet)

    def test_added_reference_must_be_explicitly_reviewed(self):
        artifact, review, packet = fixture()
        review["edits"][0].update(path="/claims/0/supporting_ids", before=["work:first"], after=["work:first", "event:accept"])
        with self.assertRaisesRegex(ValueError, "new_citation_missing"):
            apply_editorial_review(artifact, review, packet)
        review["edits"][0]["evidence_ids"] = ["event:accept"]
        result = apply_editorial_review(artifact, review, packet)
        self.assertIn("event:accept", result["claims"][0]["supporting_ids"])

    def test_final_complete_validator_rejects_wrong_facet_even_if_reviewed(self):
        artifact, review, packet = fixture()
        review["edits"][0].update(path="/claims/0/supporting_ids", before=["work:first"], after=["work:second"], evidence_ids=["work:second"])
        with self.assertRaisesRegex(ValueError, "direction_citation_mismatch"):
            apply_editorial_review(artifact, review, packet)

    def test_ai_cannot_claim_human_review_or_independent_verification(self):
        artifact, review, packet = fixture()
        review["reviewer_kind"] = "human"
        with self.assertRaisesRegex(ValueError, "cannot_be_labeled_human"):
            apply_editorial_review(artifact, review, packet)
        review["reviewer_kind"] = "ai"
        review["independent_validation"] = True
        with self.assertRaisesRegex(ValueError, "invalid_editorial_review_fields"):
            apply_editorial_review(artifact, review, packet)

    def test_tampered_reviewed_content_or_receipt_scope_rejected(self):
        artifact, review, packet = fixture()
        result = apply_editorial_review(artifact, review, packet)
        result["claims"][0]["summary"] = "未经登记的内容修订。"
        with self.assertRaisesRegex(ValueError, "artifact_content_changed"):
            apply_editorial_review(result, review, packet)
        result = apply_editorial_review(artifact, review, packet)
        result["post_edit_reviews"][0]["independent_validation"] = True
        with self.assertRaisesRegex(ValueError, "scope_changed"):
            apply_editorial_review(result, review, packet)

    def test_cache_update_requires_same_source_digest_and_all_old_content(self):
        artifact, review, packet = fixture()
        old = artifact["localizations"][0]
        review["edits"][0].update(path="/localizations/0/summary_zh", before=old["summary_zh"], after="经过内容审校的合成研究摘要。")
        result = apply_editorial_review(artifact, review, packet)
        card = next(row for row in packet["evidence_cards"] if row["evidence_id"] == old["work_id"])
        cached = {**old, "source_content_digest": card["source_content_digest"], "model": "gpt-5.6-sol"}
        changed = _reviewed_localizations(artifact, result, [cached], review, packet)
        self.assertEqual(changed[0]["summary_zh"], result["localizations"][0]["summary_zh"])
        self.assertEqual(changed[0]["model"], cached["model"])
        self.assertEqual(changed, _reviewed_localizations(artifact, result, changed, review, packet))
        with self.assertRaisesRegex(ValueError, "source_changed"):
            _reviewed_localizations(artifact, result, [{**cached, "source_content_digest": "other"}], review, packet)
        with self.assertRaisesRegex(ValueError, "before_mismatch"):
            _reviewed_localizations(artifact, result, [{**cached, "keywords_zh": ["other"]}], review, packet)

    def test_cli_archives_parent_syncs_cache_and_is_idempotent_only_in_temp_directory(self):
        artifact, review, packet = fixture()
        old = artifact["localizations"][0]
        review["edits"][0].update(path="/localizations/0/summary_zh", before=old["summary_zh"], after="经过内容审校的合成研究摘要。")
        card = next(row for row in packet["evidence_cards"] if row["evidence_id"] == old["work_id"])
        with tempfile.TemporaryDirectory(prefix="editorial-review-test-") as directory:
            root = Path(directory)
            editor.write_json(root / "monthly/2026-08.json", artifact)
            editor.write_json(root / "review.json", review)
            editor.write_json(root / "packet.json", packet)
            editor.atomic_text(root / "work-localizations.jsonl", json.dumps({**old, "source_content_digest": card["source_content_digest"]}) + "\n")
            args = ["--review", str(root / "review.json"), "--packet", str(root / "packet.json"), "--output-directory", str(root)]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(args), 0)
                first = (root / "monthly/2026-08.json").read_bytes()
                self.assertEqual(main(args), 0)
            self.assertEqual(first, (root / "monthly/2026-08.json").read_bytes())
            archive = root / "revisions/2026-08" / (review["parent_artifact_digest"] + ".json")
            self.assertEqual(json.loads(archive.read_text()), artifact)
            self.assertEqual(len(list((root / "reviews/2026-08").glob("*.json"))), 1)
            self.assertEqual(editor.read_jsonl(root / "work-localizations.jsonl")[0]["summary_zh"], review["edits"][0]["after"])

    def test_cli_preflights_cache_conflicts_before_any_live_content_write(self):
        artifact, review, packet = fixture()
        old = artifact["localizations"][0]
        review["edits"][0].update(path="/localizations/0/title_zh", before=old["title_zh"], after="审校后的合成标题")
        with tempfile.TemporaryDirectory(prefix="editorial-review-conflict-") as directory:
            root = Path(directory)
            editor.write_json(root / "monthly/2026-08.json", artifact)
            editor.write_json(root / "review.json", review)
            editor.write_json(root / "packet.json", packet)
            editor.atomic_text(root / "work-localizations.jsonl", json.dumps({**old, "source_content_digest": "stale"}) + "\n")
            parent_bytes = (root / "monthly/2026-08.json").read_bytes()
            cache_bytes = (root / "work-localizations.jsonl").read_bytes()
            with self.assertRaisesRegex(ValueError, "source_changed"):
                main(["--review", str(root / "review.json"), "--packet", str(root / "packet.json"), "--output-directory", str(root)])
            self.assertEqual(parent_bytes, (root / "monthly/2026-08.json").read_bytes())
            self.assertEqual(cache_bytes, (root / "work-localizations.jsonl").read_bytes())
            self.assertFalse((root / "revisions").exists())


if __name__ == "__main__":
    unittest.main()
