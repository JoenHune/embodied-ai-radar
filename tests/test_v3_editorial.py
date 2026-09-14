"""Monthly editorial checks use synthetic evidence and Responses fixtures."""
from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("editorial", ROOT / "scripts/generate_v3_editorial.py")
editor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(editor)
MONTH = "2026-08"


def evidence_fixture():
    works = [
        {"work_id": "work:first", "title": "Fixture embodied policy", "authors": ["Fixture Author"],
         "abstract": "Synthetic evidence for controlled tests, with real robot experiments.", "first_public_date": "2026-08-04",
         "first_public_date_precision": "day", "relevance": {"status": "included"}, "directions": ["D1"], "questions": ["Q0"],
         "evidence_cluster_id": "cluster:first", "source_record_ids": ["source:first"], "strict_peer_reviewed": True},
        {"work_id": "work:second", "title": "Fixture world model", "authors": ["Another Author"],
         "abstract": "A synthetic test compares a world model with a baseline.", "first_public_date": "2026-08-10",
         "first_public_date_precision": "day", "relevance": {"status": "included"}, "directions": ["D3"], "questions": ["Q1"],
         "evidence_cluster_id": "cluster:second", "source_record_ids": ["source:second"], "strict_peer_reviewed": False},
        {"work_id": "work:old", "title": "Fixture prior-month paper", "abstract": "Prior month research newly accepted now.",
         "first_public_date": "2026-05-03", "first_public_date_precision": "day", "relevance": {"status": "included"},
         "directions": ["D1"], "questions": ["Q0"], "source_record_ids": ["source:old"]},
    ]
    works[0]["curated"] = True
    versions = [{"work_id": row["work_id"], "kind": "preprint", "url": f"https://example.test/{index}", "public_at": row["first_public_date"], "date_precision": "day",
                 "source_record_id": row["source_record_ids"][0]} for index, row in enumerate(works)]
    events = [{"event_id": "event:accept", "work_id": "work:old", "event_type": "peer_review_acceptance",
               "published_at": "2026-08-20T00:00:00Z", "url": "https://openreview.net/forum?id=fixture",
               "organization_id": "org:test", "attribution_grade": "G1", "direction_codes": ["D1"], "question_codes": ["Q0"]}]
    snapshot = {"month": MONTH, "status": "complete", "coverage": {"included_works": 2, "strict_peer_reviewed": 1},
                "directions": [{"code": "D1", "primary_count": 1, "multi_label_count": 1, "share": .5, "share_delta": .1},
                               {"code": "D3", "primary_count": 1, "multi_label_count": 1, "share": .5, "share_delta": -.1}],
                "questions": [{"code": "Q0", "count": 1}, {"code": "Q1", "count": 1}],
                "evidence_lanes": {"preprint": 2}, "evidence_grades": {"E2": 2}, "high_signal_works": []}
    sources = [{"source_record_id": version["source_record_id"], "url": version["url"], "published_at": version["public_at"]} for version in versions]
    return snapshot, {"works": works, "manifestations": versions, "evidence-events": events, "source-records": sources}


def valid_editorial(packet):
    def summary(code, family):
        evidence = next(row["evidence_id"] for row in packet["evidence_cards"] if code in row[family])
        return {"code": code, "summary": "现有证据提示研究正在关注可复核的实验条件。", "supporting_ids": [evidence],
                "counterevidence_ids": [], "numeric_claims": []}
    first = packet["evidence_cards"][0]
    claim = {"title": "实验条件值得关注", "summary": "输入研究提出了可进一步验证的机器人学习方法。",
             "directions": first["directions"], "questions": first["questions"], "supporting_ids": [first["evidence_id"]],
             "counterevidence_ids": [], "numeric_claims": []}
    return {"month": packet["month"], "claims": [claim],
            "direction_summaries": [summary(code, "directions") for code in packet["required_direction_codes"]],
            "question_summaries": [summary(code, "questions") for code in packet["required_question_codes"]],
            "organization_changes": [], "counterevidence": [], "limitations": packet["known_limitations"], "watchlist": [], "signal_assessments": [],
            "localizations": [{"work_id": value, "title_zh": "合成测试论文", "summary_zh": "用于回归验证的机器人学习研究。",
                               "keywords_zh": ["机器人学习"], "source_ids": next(row["source_record_ids"] for row in packet["evidence_cards"] if row["evidence_id"] == value)}
                              for value in packet["required_localization_ids"]]}


def response(value, **extra):
    return {"id": "resp_fixture", "status": "completed", "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(value)}]}], **extra}


def version_fixture():
    from scripts.versioned_text import snapshot_from_payload
    snapshot, catalog = evidence_fixture()
    work = catalog["works"][0]
    work.update(identifiers={"arxiv": "2608.00404"}, title="Future revised title", abstract="Future experiment reaches 99% success.",
                authors=["Future Author"], title_zh="未来修订中文标题", summary_zh="未来修订实验成功率达到99%。")
    catalog["text-snapshots"] = []
    for version, when, title, abstract, author in [("v1", "2026-08-04T10:00:00Z", "Original robot title", "Original robot experiment with a baseline.", "Original Author"),
                                                  ("v2", "2026-09-02T10:00:00Z", work["title"], work["abstract"], "Future Author")]:
        source = {"source_record_id": "source:" + version, "url": "https://arxiv.org/abs/2608.00404" + version,
                  "published_at": when, "date_precision": "second", "source_type": "official_arxiv_version_metadata"}
        catalog["source-records"].append(source)
        work["source_record_ids"].append(source["source_record_id"])
        payload = {"arxiv_id": "2608.00404", "version": version, "title": title, "abstract": abstract, "authors": [author],
                   "submitted_at": "2026-08-04T10:00:00Z", "updated_at": when}
        source["text_content_digest"] = editor.source_content_digest(payload)
        catalog["text-snapshots"].append(snapshot_from_payload(work, source, payload))
    return snapshot, catalog


class EditorialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="v3-editorial-fixture-")
        self.output = Path(self.temp.name) / "editorial"
        self.snapshot, self.catalog = evidence_fixture()
        self.packet = editor.build_evidence_packet(self.snapshot, self.catalog)
        self.value = valid_editorial(self.packet)

    def tearDown(self):
        self.temp.cleanup()

    def test_unchanged_verified_month_is_cached_without_a_provider_call(self):
        first = self.run_editor()
        self.assertEqual(first["status"], "complete")
        original = (self.output / "monthly" / f"{MONTH}.json").read_bytes()
        def unexpected_request(*_):
            raise AssertionError("Unchanged completed month must not call the model")
        second = editor.run_month(self.packet, MONTH, self.output, requester=unexpected_request)
        self.assertEqual(second["status"], "complete")
        self.assertTrue(second["cached"])
        self.assertEqual((self.output / "monthly" / f"{MONTH}.json").read_bytes(), original)

    def run_editor(self, value=None, **kwargs):
        value = copy.deepcopy(value or self.value)
        return editor.run_month(self.packet, MONTH, self.output, base_url="http://127.0.0.1:9999",
                                requester=lambda *_: (value, response(value)), sleeper=lambda _: None,
                                generated_at="2026-09-05T12:00:00Z", **kwargs)

    def assert_invalid(self, value, reason=None):
        with self.assertRaises(editor.EditorialError) as caught:
            editor.validate_editorial(value, self.packet)
        if reason:
            self.assertEqual(str(caught.exception), reason)

    def test_full_schema_and_single_finding_are_valid(self):
        editor.validate_editorial(self.value, self.packet)
        self.value["claims"] = []
        editor.validate_editorial(self.value, self.packet)

    def test_report_localization_feedback_identifies_forbidden_quantity(self):
        card = next(row for row in self.packet["evidence_cards"] if row["evidence_id"] == self.value["localizations"][0]["work_id"])
        card["report_text"] = {"status": "available", "snapshots": []}
        self.value["localizations"][0]["summary_zh"] = "公司自报的两种适配方式。"
        feedback = editor.editorial_repair_context(self.value, self.packet, "report_localization_requires_qualitative_attribution")
        issue = next(row for row in feedback["issues"] if row["path"] == "/localizations/0/summary_zh")
        self.assertEqual(issue["forbidden_quantity_phrases"], ["两种"])
        self.assertFalse(issue["missing_company_attribution"])

    def test_saved_candidate_can_seed_first_request_without_changing_evidence(self):
        bad = copy.deepcopy(self.value)
        bad["claims"][0]["directions"] = ["D15"]
        feedback = editor.editorial_repair_context(bad, self.packet, "direction_citation_mismatch")
        calls = []
        def repaired(packet, model, base, key, *, repair_context=None):
            calls.append(copy.deepcopy(repair_context))
            return self.value, response(self.value)
        result = editor.run_month(self.packet, MONTH, self.output, base_url="http://fixture.invalid", requester=repaired,
                                  sleeper=lambda _: None, initial_repair_context=feedback)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["attempts"], 1)
        self.assertEqual(calls, [feedback])

    def test_saved_candidate_with_changed_packet_is_rejected_before_provider(self):
        feedback = {"input_digest": "outdated", "evidence_month": MONTH}
        with self.assertRaisesRegex(editor.EditorialError, "resume_evidence_packet_changed"):
            editor.run_month(self.packet, MONTH, self.output, base_url="http://fixture.invalid",
                             requester=lambda *_: self.fail("Provider must not be called"), initial_repair_context=feedback)

    def test_schema_rejects_additional_fields_bad_types_and_illegal_codes(self):
        for mutate in [lambda x: x.update(extra="hallucinated"),
                       lambda x: x["claims"][0].update(supporting_ids="work:first"),
                       lambda x: x["claims"][0].update(directions=["D99"]),
                       lambda x: x["claims"][0].update(questions=["Q11"]),
                       lambda x: x["direction_summaries"][0].update(summary=5)]:
            value = copy.deepcopy(self.value)
            mutate(value)
            self.assert_invalid(value, "schema_validation_failed")

    def test_factual_references_must_not_be_empty_or_unknown(self):
        for references in ([], ["missing:paper"]):
            value = copy.deepcopy(self.value)
            value["claims"][0]["supporting_ids"] = references
            self.assert_invalid(value)

    def test_reference_month_and_response_month_must_match(self):
        self.value["month"] = "2026-07"
        self.assert_invalid(self.value, "month_mismatch")
        self.value["month"] = MONTH
        self.packet["evidence_cards"][0]["evidence_month"] = "2026-07"
        self.assert_invalid(self.value, "citation_unknown_or_wrong_month")

    def test_direction_and_question_citations_must_match(self):
        self.value["direction_summaries"][0]["supporting_ids"] = ["work:second"]
        self.assert_invalid(self.value, "direction_citation_mismatch")
        self.value = valid_editorial(self.packet)
        self.value["question_summaries"][0]["supporting_ids"] = ["work:second"]
        self.assert_invalid(self.value, "question_citation_mismatch")

    def test_relevant_citation_cannot_mask_unrelated_added_evidence(self):
        self.value["direction_summaries"][0]["supporting_ids"].append("work:second")
        self.assert_invalid(self.value, "unrelated_facet_citation")

    def test_facet_repair_explains_current_labels_without_rewriting_valid_content(self):
        self.value["claims"][0].update(directions=["D1"], questions=["Q1"], supporting_ids=["work:first"])
        before = copy.deepcopy(self.value)
        feedback = editor.editorial_repair_context(self.value, self.packet, "question_citation_mismatch")
        issue = next(row for row in feedback["issues"] if row["code"] == "question_citation_mismatch")
        self.assertEqual(issue["facet_path"], "/claims/0/questions")
        self.assertEqual(issue["current_supporting_facets"], {"work:first": ["Q0"]})
        self.assertIn("verbatim", feedback["policy"])
        self.assertEqual(feedback["previous_candidate"], before)
        self.assertEqual(self.value, before)

    def test_every_evidenced_facet_requires_summary_without_duplicate_codes(self):
        self.value["direction_summaries"].pop()
        self.assert_invalid(self.value, "incomplete_facet_coverage")
        self.value = valid_editorial(self.packet)
        self.value["question_summaries"].append(copy.deepcopy(self.value["question_summaries"][0]))
        self.assert_invalid(self.value, "duplicate_summary_code")

    def test_bound_numeric_statistics_pass_but_invented_values_fail(self):
        claim = self.value["claims"][0]
        claim["summary"] = "本月纳入 2 篇论文。"
        claim["numeric_claims"] = [{"metric": "coverage.included_works", "value": 2, "unit": "count", "evidence_ids": ["work:first"]}]
        editor.validate_editorial(self.value, self.packet)
        claim["numeric_claims"][0]["value"] = 99
        self.assert_invalid(self.value, "unsupported_numeric_claim")

    def test_unbound_numbers_in_arabic_or_chinese_prose_fail(self):
        for text in ("成功率达到 99%。", "获得三项提升。", "增加 2 个百分点。", "需要9999步适配。", "需要九步梯度更新。"):
            self.value["claims"][0]["summary"] = text
            self.assert_invalid(self.value, "unbound_number_in_prose")

    def test_scaled_quantities_bind_base_counts_not_magnitude_coefficients(self):
        for text, count, coefficient in (("2万篇", 20000, 2), ("两万篇", 20000, 2),
                                          ("二十万组", 200000, 20), ("1.5亿次", 150000000, 1.5),
                                          ("三亿个", 300000000, 3), ("一百二十万", 1200000, 120),
                                          ("0.25 万项", 2500, .25), ("0亿篇", 0, 0)):
            with self.subTest(text=text):
                packet, value = copy.deepcopy(self.packet), copy.deepcopy(self.value)
                claim = value["claims"][0]
                claim["summary"] = "本月纳入" + text + "。"
                number = {"metric": "fixture.scaled_count", "value": count, "unit": "count", "evidence_ids": ["work:first"]}
                claim["numeric_claims"] = [number]
                packet["facts"][number["metric"]] = {"value": count, "unit": "count", "evidence_ids": ["work:first"]}
                editor.validate_editorial(value, packet)
                self.assertEqual(editor.unbound_prose_quantities(claim), [])
                if coefficient != count:
                    number["value"] = coefficient
                    packet["facts"][number["metric"]]["value"] = coefficient
                    with self.assertRaisesRegex(editor.EditorialError, "unbound_number_in_prose"):
                        editor.validate_editorial(value, packet)

    def test_scaled_count_does_not_scale_neighboring_percentages_or_points(self):
        claim = self.value["claims"][0]
        claim["summary"] = "纳入2万篇，份额2%，变化二个百分点。"
        for name, number, unit in (("count", 20000, "count"), ("share", 2, "percentage"), ("delta", 2, "percentage_points")):
            metric = "fixture." + name
            self.packet["facts"][metric] = {"value": number, "unit": unit, "evidence_ids": ["work:first"]}
            claim["numeric_claims"].append({"metric": metric, "value": number, "unit": unit, "evidence_ids": ["work:first"]})
        editor.validate_editorial(self.value, self.packet)
        for index in (1, 2):
            broken, packet = copy.deepcopy(self.value), copy.deepcopy(self.packet)
            number = broken["claims"][0]["numeric_claims"][index]
            number["value"] = 20000
            packet["facts"][number["metric"]]["value"] = 20000
            with self.assertRaisesRegex(editor.EditorialError, "unbound_number_in_prose"):
                editor.validate_editorial(broken, packet)

    def test_scaled_percent_suffix_cannot_be_bound_as_count(self):
        for text, count, unit in (("2万%", 20000, "percentage"), ("两亿％", 200000000, "percentage"),
                                  ("2 万个百分点", 20000, "percentage_points")):
            with self.subTest(text=text):
                packet, value = copy.deepcopy(self.packet), copy.deepcopy(self.value)
                claim = value["claims"][0]
                claim["summary"] = "测量值为" + text + "。"
                number = {"metric": "fixture.scaled", "value": count, "unit": "count", "evidence_ids": ["work:first"]}
                claim["numeric_claims"] = [number]
                packet["facts"][number["metric"]] = {"value": count, "unit": "count", "evidence_ids": ["work:first"]}
                with self.assertRaisesRegex(editor.EditorialError, "unbound_number_in_prose"):
                    editor.validate_editorial(value, packet)
                number["unit"] = unit
                packet["facts"][number["metric"]]["unit"] = unit
                editor.validate_editorial(value, packet)

    def test_scaled_numeric_preserves_fact_and_evidence_checks(self):
        claim = self.value["claims"][0]
        claim["summary"] = "纳入2万篇论文。"
        number = {"metric": "coverage.included_works", "value": 20000, "unit": "count", "evidence_ids": ["work:first"]}
        claim["numeric_claims"] = [number]
        self.assert_invalid(self.value, "unsupported_numeric_claim")  # Actual fixture fact is 2.
        self.packet["facts"][number["metric"]]["value"] = 20000
        number["evidence_ids"] = ["work:second"]
        self.assert_invalid(self.value, "numeric_evidence_mismatch")
        number.update(evidence_ids=["work:first"], unit="percentage")
        self.assert_invalid(self.value, "unsupported_numeric_claim")

    def test_scaled_numeric_feedback_uses_expanded_value(self):
        claim = self.value["claims"][0]
        claim["summary"] = "纳入两万篇论文。"
        claim["numeric_claims"] = [{"metric": "coverage.included_works", "value": 2, "unit": "count", "evidence_ids": ["work:first"]}]
        self.assert_invalid(self.value, "unbound_number_in_prose")
        issue = editor.editorial_repair_context(self.value, self.packet, "unbound_number_in_prose")["issues"][0]
        self.assertEqual((issue["quantity_text"], issue["parsed_value"], issue["source_unit"], issue["expected_unit"]),
                         ("两万", 20000, "万", "count"))
        self.assertEqual(issue["path"], "/claims/0/summary")

    def test_localization_scaled_numbers_match_source_base_values_and_units(self):
        localized = self.value["localizations"][0]
        card = next(row for row in self.packet["evidence_cards"] if row["evidence_id"] == localized["work_id"])
        for source in ("Tested 20000 tasks with 25% success.", "评估两万项任务，成功率25%。"):
            card["abstract"] = source
            localized["summary_zh"] = "评估2万项任务，成功率二十五%。"
            editor.validate_editorial(self.value, self.packet)
            localized["summary_zh"] = "评估2项任务。"
            self.assert_invalid(self.value, "unsupported_localization_number")
        card["abstract"] = "Tested 2 tasks with 25% success."
        localized["summary_zh"] = "评估两万项任务。"
        self.assert_invalid(self.value, "unsupported_localization_number")
        card["abstract"] = "Improved by 2万%."
        self.assert_invalid(self.value, "unsupported_localization_number")  # Same value, wrong unit.

    def test_numeric_feedback_locates_incidental_quantity_not_camera_perspective(self):
        bad, original_packet = copy.deepcopy(self.value), copy.deepcopy(self.packet)
        bad["claims"][0]["summary"] = "DexMan从第三人称视频生成技能；另一项预印本利用第一人称视频。"
        original = copy.deepcopy(bad)
        feedback = editor.editorial_repair_context(bad, self.packet, "unbound_number_in_prose")
        self.assertEqual(len(feedback["issues"]), 1)
        issue = feedback["issues"][0]
        self.assertEqual(issue["path"], "/claims/0/summary")
        self.assertEqual(issue["numeric_claims_path"], "/claims/0/numeric_claims")
        self.assertEqual(issue["quantity_text"], "一项")
        self.assertEqual((issue["parsed_value"], issue["source_unit"], issue["expected_unit"]), (1, "项", "count"))
        span = issue["prose_spans"][0]
        self.assertEqual(bad["claims"][0]["summary"][span["start"]:span["end"]], "一项")
        self.assertEqual(span["path"], "/claims/0/summary")
        self.assertNotIn("allowed_metrics", issue)  # No irrelevant aggregate-number bait.
        self.assertEqual(feedback["previous_candidate"], original)
        self.assertEqual(self.packet, original_packet)
        self.assertEqual(bad, original)
        self.assert_invalid(bad, "unbound_number_in_prose")  # Feedback is not a validator bypass.

    def test_numeric_feedback_identifies_all_prose_units_and_skips_bound_counts(self):
        claim = self.value["claims"][0]
        claim["title"] = "🦾误差 2% 与 2个百分点"
        claim["summary"] = "两篇论文，成功率99％；需要九步并重复 3 次。"
        claim["numeric_claims"] = [{"metric": "coverage.included_works", "value": 2, "unit": "count", "evidence_ids": ["work:first"]}]
        feedback = editor.editorial_repair_context(self.value, self.packet, "unbound_number_in_prose")
        issues = feedback["issues"]
        self.assertEqual([item["quantity_text"] for item in issues], ["2%", "2个百分点", "99％", "九步", "3 次"])
        self.assertEqual([item["expected_unit"] for item in issues], ["percentage", "percentage_points", "percentage", "count", "count"])
        self.assertEqual([item["path"] for item in issues[:2]], ["/claims/0/title"] * 2)
        for item in issues:
            self.assertEqual(item["offset_unit"], "unicode_codepoints")
            self.assertEqual(item["span_end"], "exclusive")
            for span in item["prose_spans"]:
                self.assertEqual(claim[span["field"]][span["start"]:span["end"]], span["text"])
        self.assert_invalid(self.value, "unbound_number_in_prose")

    def test_numeric_feedback_matches_validator_across_title_summary_boundary(self):
        self.value["claims"][0].update(title="涉及2", summary="篇论文。")
        self.assert_invalid(self.value, "unbound_number_in_prose")
        feedback = editor.editorial_repair_context(self.value, self.packet, "unbound_number_in_prose")
        issue = feedback["issues"][0]
        self.assertEqual(issue["quantity_text"], "2 篇")
        self.assertEqual(issue["path"], "/claims/0")
        self.assertEqual([(span["path"], span["text"]) for span in issue["prose_spans"]],
                         [("/claims/0/title", "2"), ("/claims/0/summary", "篇")])

    def test_numeric_feedback_separates_accepted_metadata_and_missing_facet_notes(self):
        packet, bad = copy.deepcopy(self.packet), copy.deepcopy(self.value)
        event = next(card for card in packet["evidence_cards"] if card["evidence_id"] == "event:accept")
        event.update(experimental_text_available=False, text_status="non_arxiv_unverified_source_text")
        event["questions"].append("Q10")
        packet["required_question_codes"].append("Q10")
        bad["question_summaries"].append({"code": "Q10", "summary": editor.MISSING_VERSION_SUMMARY,
                                           "supporting_ids": ["event:accept"], "counterevidence_ids": [], "numeric_claims": []})
        bad["organization_changes"] = [{**copy.deepcopy(bad["claims"][0]), "supporting_ids": ["event:accept"],
                                         "title": "会议记录", "summary": "本月登记正式发表事件。"}]
        bad["watchlist"] = [{**copy.deepcopy(bad["claims"][0]), "summary": "不将发表事件作为另一篇论文。"}]
        feedback = editor.editorial_repair_context(bad, packet, "unbound_number_in_prose")
        self.assertEqual(len(feedback["issues"]), 1)
        issue = feedback["issues"][0]
        self.assertEqual((issue["path"], issue["quantity_text"]), ("/watchlist/0/summary", "一篇"))
        self.assertTrue(issue["currently_violates_rule"])
        self.assertEqual({item["path"] for item in feedback["accepted_exceptions"]}, {"/question_summaries/2", "/organization_changes/0"})
        self.assertTrue(all(item["currently_violates_rule"] is False for item in feedback["accepted_exceptions"]))
        self.assertTrue(all("available_research_ids_by_facet" not in item for item in feedback["accepted_exceptions"]))
        bad["watchlist"][0]["summary"] = "不将发表事件重复计为新论文。"
        editor.validate_editorial(bad, packet)

    def test_precise_numeric_feedback_can_resume_saved_candidate_with_unchanged_packet(self):
        bad = copy.deepcopy(self.value)
        bad["claims"][0]["summary"] = "另一项预印本利用自我视角视频。"
        feedback = editor.editorial_repair_context(bad, self.packet, "unbound_number_in_prose")
        before_packet, before_candidate = copy.deepcopy(self.packet), copy.deepcopy(bad)
        calls = []
        def repaired(packet, model, base, key, *, repair_context=None):
            calls.append(copy.deepcopy(repair_context))
            self.assertEqual(repair_context["issues"][0]["quantity_text"], "一项")
            value = copy.deepcopy(repair_context["previous_candidate"])
            value["claims"][0]["summary"] = "相关预印本利用自我视角视频。"
            return value, response(value)
        result = editor.run_month(self.packet, MONTH, self.output, base_url="http://fixture.invalid", requester=repaired,
                                  sleeper=lambda _: None, initial_repair_context=feedback)
        self.assertEqual((result["status"], result["attempts"]), ("complete", 1))
        self.assertEqual(calls, [feedback])
        self.assertEqual(self.packet, before_packet)
        self.assertEqual(bad, before_candidate)
        self.assertEqual(result["input_digest"], editor.editorial_input_digest(before_packet))

    def test_numeric_units_and_cited_evidence_must_match(self):
        claim = self.value["claims"][0]
        number = {"metric": "directions.D1.primary_count", "value": 1, "unit": "percentage", "evidence_ids": ["work:first"]}
        claim["numeric_claims"] = [number]
        self.assert_invalid(self.value, "unsupported_numeric_claim")
        number.update(unit="count", evidence_ids=["work:second"])
        self.assert_invalid(self.value, "numeric_evidence_mismatch")

    def test_new_validation_event_can_reference_older_work_without_recounting(self):
        ids = {row["evidence_id"] for row in self.packet["evidence_cards"]}
        self.assertIn("event:accept", ids)
        self.assertNotIn("work:old", ids)
        event = next(row for row in self.packet["evidence_cards"] if row["kind"] == "event")
        self.assertIn("Prior month", event["abstract"])

    def test_missing_non_arxiv_abstract_does_not_use_legacy_summary_as_experiment(self):
        self.catalog["works"][0].update(abstract="", summary_zh="后来的内部成功率达到99%。", title_zh="后续译文")
        packet = editor.build_evidence_packet(self.snapshot, self.catalog)
        card = next(row for row in packet["evidence_cards"] if row["work_id"] == "work:first")
        self.assertFalse(card["experimental_text_available"])
        self.assertEqual(card["abstract"], "")
        self.assertEqual(card["summary_zh"], "")
        self.assertNotIn("work:first", packet["required_localization_ids"])
        self.assertEqual(packet["coverage"]["included_works"], 2)

    def test_mutable_report_date_does_not_authenticate_current_body(self):
        self.catalog["manifestations"][0]["kind"] = "technical_report"
        original = copy.deepcopy(self.catalog)
        packet = editor.build_evidence_packet(self.snapshot, self.catalog)
        card = next(row for row in packet["evidence_cards"] if row["work_id"] == "work:first")
        self.assertEqual(card["text_status"], "non_arxiv_unverified_source_text")
        self.assertFalse(card["experimental_text_available"])
        self.assertEqual(card["abstract"], "")
        self.assertEqual(self.catalog, original)
        self.assertTrue(any("公司报告" in item for item in packet["known_limitations"]))

    def test_report_event_preserves_metadata_without_importing_later_experimental_summary(self):
        self.catalog["manifestations"][2]["kind"] = "technical_report"
        self.catalog["evidence-events"][0]["summary_zh"] = "后续新增实验达到99%。"
        packet = editor.build_evidence_packet(self.snapshot, self.catalog)
        event = next(row for row in packet["evidence_cards"] if row["kind"] == "event")
        self.assertFalse(event["experimental_text_available"])
        self.assertEqual(event["summary_zh"], "")
        self.assertEqual(event["published_at"], "2026-08-20T00:00:00Z")
        self.assertEqual(event["organization_id"], "org:test")

    def test_organization_claim_requires_actual_organization_event(self):
        self.value["organization_changes"] = [copy.deepcopy(self.value["claims"][0])]
        self.assert_invalid(self.value, "organization_change_without_event")
        self.value["organization_changes"][0]["supporting_ids"] = ["event:accept"]
        editor.validate_editorial(self.value, self.packet)

    def test_localization_requires_real_source_and_required_key_work(self):
        self.value["localizations"][0]["source_ids"] = ["source:unknown"]
        self.assert_invalid(self.value, "invalid_localization_source")
        self.value["localizations"] = []
        self.assert_invalid(self.value, "required_localization_missing")

    def test_incomplete_refusal_and_empty_responses_are_rejected(self):
        for raw in [response(self.value, status="incomplete"), response(self.value, status="failed"),
                    {"status": "completed", "output": [{"content": [{"type": "refusal", "refusal": "no"}]}]},
                    {"status": "completed", "output": []}]:
            with self.assertRaises(editor.EditorialError):
                editor.extract_output_text(raw)

    def test_real_request_uses_responses_strict_schema_and_parses_all_text(self):
        captured = []
        class Reply(io.BytesIO):
            def __enter__(self):
                return self
            def __exit__(self, *args):
                self.close()
        def fake_urlopen(request, timeout):
            captured.append(request)
            return Reply(json.dumps(response(self.value)).encode())
        with patch.object(editor.urllib.request, "urlopen", fake_urlopen):
            value, raw = editor.request_editorial(self.packet, "gpt-5.6-sol", "http://localhost:9000/v1", "fixture-key")
        self.assertEqual(value, self.value)
        self.assertEqual(captured[0].full_url, "http://localhost:9000/v1/responses")
        body = json.loads(captured[0].data)
        self.assertTrue(body["text"]["format"]["strict"])
        self.assertFalse(body["store"])
        self.assertIn("evidence_cards", body["input"][1]["content"][0]["text"])
        remote_schema = body["text"]["format"]["schema"]
        self.assertNotIn('"format": "uri"', json.dumps(remote_schema))
        self.assertNotIn('"minLength"', json.dumps(remote_schema))
        self.assertIn("source_spans", remote_schema["$defs"]["signal_assessment"]["required"])

    def test_nan_provider_json_and_forged_refusal_success_are_rejected(self):
        with self.assertRaises(editor.EditorialError):
            json.loads('{"value":NaN}', parse_constant=editor.reject_json_constant)
        raw = response(self.value)
        raw["output"][0]["content"].append({"type": "refusal", "refusal": "fixture refusal"})
        status = editor.run_month(self.packet, MONTH, self.output, base_url="http://localhost",
                                  requester=lambda *_: (self.value, raw), sleeper=lambda _: None)
        self.assertEqual(status["failure"], {"reason": "response_refused", "attempts": 3})

    def test_success_persists_month_and_localizations_without_mutating_input(self):
        before = copy.deepcopy(self.value)
        status = self.run_editor()
        self.assertEqual(status["status"], "complete")
        artifact = json.loads((self.output / "monthly/2026-08.json").read_text())
        self.assertTrue(artifact["claims"][0]["claim_id"].startswith("claim:2026-08:llm"))
        self.assertEqual(artifact["localization_work_ids"], ["work:first"])
        self.assertEqual(editor.read_jsonl(self.output / "work-localizations.jsonl")[0]["source_ids"], ["source:first"])
        self.assertEqual(self.value, before)
        self.run_editor()
        self.assertEqual(len(editor.read_jsonl(self.output / "work-localizations.jsonl")), 1)

    def test_three_failures_preserve_previous_complete_file_and_hide_secret(self):
        self.run_editor()
        original = (self.output / "monthly/2026-08.json").read_bytes()
        calls = []
        def broken(*_):
            calls.append(True)
            raise ValueError("secret-key https://private-host.example/v1")
        changed_packet = copy.deepcopy(self.packet)
        changed_packet["known_limitations"].append("来源条件发生变化，需要重写本月编辑。")
        status = editor.run_month(changed_packet, MONTH, self.output, base_url="http://private-host", api_key="secret-key",
                                  requester=broken, sleeper=lambda _: None)
        self.assertEqual(len(calls), 3)
        self.assertEqual(status["status"], "data_only")
        self.assertTrue(status["previous_complete_preserved"])
        self.assertEqual(original, (self.output / "monthly/2026-08.json").read_bytes())
        self.assertNotIn("secret-key", json.dumps(status))
        self.assertNotIn("private-host", json.dumps(status))

    def test_invalid_candidate_receives_precise_feedback_then_repairs_without_fact_changes(self):
        bad = copy.deepcopy(self.value)
        bad["question_summaries"][0]["supporting_ids"] = ["work:second"]
        original_bad, original_packet = copy.deepcopy(bad), copy.deepcopy(self.packet)
        calls = []
        def requester(packet, model, base, key, *, repair_context=None):
            calls.append(copy.deepcopy(repair_context))
            self.assertEqual(packet, original_packet)
            if len(calls) == 1:
                return bad, response(bad)
            self.assertEqual(repair_context["previous_candidate"], original_bad)
            self.assertEqual(repair_context["error_code"], "question_citation_mismatch")
            problem = next(issue for issue in repair_context["issues"] if issue["code"] == "question_citation_mismatch")
            self.assertEqual(problem["path"], "/question_summaries/0/supporting_ids")
            self.assertEqual(problem["facet"], "Q0")
            self.assertIn("work:first", problem["allowed_evidence_ids"])
            self.assertNotIn("work:second", problem["allowed_evidence_ids"])
            return self.value, response(self.value)
        status = editor.run_month(self.packet, MONTH, self.output, base_url="http://fixture.invalid", requester=requester, sleeper=lambda _: None)
        self.assertEqual(status["status"], "complete")
        self.assertEqual(status["attempts"], 2)
        self.assertEqual(len(calls), 2)
        self.assertIsNone(calls[0])
        self.assertEqual(self.packet, original_packet)
        self.assertEqual(bad, original_bad)
        self.assertEqual(status["input_digest"], editor.editorial_input_digest(original_packet))
        cached = editor.run_month(self.packet, MONTH, self.output, requester=lambda *_: self.fail("cache must not call model"))
        self.assertTrue(cached["cached"])

    def test_repair_feedback_does_not_loosen_checks_or_replace_completed_history(self):
        self.run_editor()
        original = (self.output / "monthly/2026-08.json").read_bytes()
        packet = copy.deepcopy(self.packet)
        packet["known_limitations"].append("合成修订条件。")
        bad = valid_editorial(packet)
        bad["claims"][0]["supporting_ids"] = ["invented:work"]
        contexts = []
        def broken(packet, model, base, key, *, repair_context=None):
            contexts.append(copy.deepcopy(repair_context))
            return bad, response(bad)
        status = editor.run_month(packet, MONTH, self.output, base_url="http://fixture.invalid", requester=broken, sleeper=lambda _: None)
        self.assertEqual(status["failure"], {"reason": "citation_unknown_or_wrong_month", "attempts": 3})
        self.assertTrue(status["previous_complete_preserved"])
        self.assertEqual(len(contexts), 3)
        self.assertTrue(all(context is not None for context in contexts[1:]))
        self.assertEqual((self.output / "monthly/2026-08.json").read_bytes(), original)
        self.assertEqual(bad["claims"][0]["supporting_ids"], ["invented:work"])

    def test_service_errors_never_become_model_feedback_or_leak_exception_text(self):
        contexts = []
        def unavailable(packet, model, base, key, *, repair_context=None):
            contexts.append(repair_context)
            raise editor.EditorialError("secret-key https://private-host.example/internal")
        status = editor.run_month(self.packet, MONTH, self.output, base_url="http://private-host", api_key="secret-key", requester=unavailable, sleeper=lambda _: None)
        self.assertEqual(contexts, [None, None, None])
        self.assertEqual(status["failure"]["reason"], "invalid_response_or_provider_error")
        self.assertNotIn("secret-key", json.dumps(status))
        self.assertNotIn("private-host", json.dumps(status))

    def test_content_feedback_survives_transient_service_failure_without_service_details(self):
        bad = copy.deepcopy(self.value)
        bad["question_summaries"][0]["supporting_ids"] = ["work:second"]
        contexts = []
        def requester(packet, model, base, key, *, repair_context=None):
            contexts.append(copy.deepcopy(repair_context))
            if len(contexts) == 1:
                return bad, response(bad)
            if len(contexts) == 2:
                raise editor.urllib.error.URLError("secret-key private-host")
            return self.value, response(self.value)
        status = editor.run_month(self.packet, MONTH, self.output, base_url="http://fixture.invalid", requester=requester, sleeper=lambda _: None)
        self.assertEqual(status["status"], "complete")
        self.assertEqual(status["attempts"], 3)
        self.assertEqual(contexts[1], contexts[2])
        self.assertNotIn("secret-key", json.dumps(contexts))
        self.assertNotIn("private-host", json.dumps(contexts))

    def test_invalid_json_feedback_has_no_raw_body_and_never_writes_factual_authority(self):
        contexts = []
        def requester(packet, model, base, key, *, repair_context=None):
            contexts.append(copy.deepcopy(repair_context))
            json.loads('{"private-host": "secret-key", BROKEN')
        status = editor.run_month(self.packet, MONTH, self.output, base_url="http://fixture.invalid", requester=requester, sleeper=lambda _: None)
        self.assertEqual(status["status"], "data_only")
        self.assertEqual(status["failure"], {"reason": "invalid_json", "attempts": 3})
        self.assertEqual(len(contexts), 3)
        self.assertIsNone(contexts[1]["previous_candidate"])
        self.assertNotIn("private-host", json.dumps(contexts))
        self.assertNotIn("secret-key", json.dumps(contexts))
        self.assertFalse((self.output / "work-localizations.jsonl").exists())
        self.assertFalse((self.output / "signal-evidence.jsonl").exists())
        self.assertEqual(json.loads((self.output / "monthly/2026-08.json").read_text())["claims"], [])

    def test_incomplete_or_refused_candidate_never_echoed_as_repair_draft(self):
        for raw in [response(self.value, status="incomplete"), {"status": "completed", "refusal": "private-host secret-key"}]:
            contexts = []
            def requester(packet, model, base, key, *, repair_context=None):
                contexts.append(repair_context)
                return self.value, raw
            editor.run_month(self.packet, MONTH, self.output, base_url="http://fixture.invalid", requester=requester, sleeper=lambda _: None)
            self.assertEqual(contexts, [None, None, None])

    def test_repair_request_keeps_strict_schema_original_packet_and_separate_candidate(self):
        bad = copy.deepcopy(self.value)
        bad["question_summaries"][0]["supporting_ids"] = ["work:second"]
        feedback = editor.editorial_repair_context(bad, self.packet, "question_citation_mismatch")
        sent = []
        class Reply(io.BytesIO):
            def __enter__(self):
                return self
            def __exit__(self, *args):
                self.close()
        def fake_urlopen(request, timeout):
            sent.append(json.loads(request.data))
            return Reply(json.dumps(response(self.value)).encode())
        with patch.object(editor.urllib.request, "urlopen", fake_urlopen):
            editor.request_editorial(self.packet, "gpt-5.6-sol", "http://fixture.invalid/v1", "private-test-key", repair_context=feedback)
        body = sent[0]
        self.assertTrue(body["text"]["format"]["strict"])
        from scripts.editorial_response_schema import packet_response_schema
        self.assertEqual(body["text"]["format"]["schema"], editor.responses_schema(packet_response_schema(editor.OUTPUT_SCHEMA, self.packet, editor.MISSING_VERSION_SUMMARY)))
        self.assertEqual(json.loads(body["input"][1]["content"][0]["text"]), self.packet)
        self.assertEqual(json.loads(body["input"][2]["content"][0]["text"])["repair_context"], feedback)
        self.assertNotIn("private-test-key", json.dumps(body))
        self.assertNotIn("fixture.invalid", json.dumps(body))

    def test_schema_feedback_uses_paths_and_rules_not_arbitrary_validation_messages(self):
        bad = copy.deepcopy(self.value)
        bad["claims"][0]["directions"] = ["bad-private-host"]
        feedback = editor.editorial_repair_context(bad, self.packet, "schema_validation_failed")
        self.assertEqual(feedback["issues"][0]["path"], "/claims/0/directions/0")
        self.assertNotIn("bad-private-host", json.dumps(feedback["issues"]))
        self.assertEqual(feedback["previous_candidate"], bad)
        self.assertIsNone(editor.editorial_repair_context(bad, self.packet, "provider_http_error"))

    def test_feedback_identifies_every_unavailable_reference_and_available_same_facet(self):
        packet = copy.deepcopy(self.packet)
        next(card for card in packet["evidence_cards"] if card["evidence_id"] == "work:first").update(experimental_text_available=False, text_status="retrospective_only")
        bad = copy.deepcopy(self.value)
        before = copy.deepcopy(bad)
        feedback = editor.editorial_repair_context(bad, packet, "historical_text_unavailable_for_claim")
        issues = [item for item in feedback["issues"] if item["code"] == "historical_text_unavailable_for_claim"]
        self.assertEqual({item["path"] for item in issues}, {"/claims/0", "/direction_summaries/0", "/question_summaries/0"})
        claim = next(item for item in issues if item["path"] == "/claims/0")
        self.assertTrue(claim["currently_violates_rule"])
        self.assertEqual(claim["unavailable_ids"], ["work:first"])
        self.assertEqual(claim["unavailable_reference_paths"][0]["path"], "/claims/0/supporting_ids/0")
        self.assertIn("event:accept", claim["available_research_evidence_ids"])
        self.assertNotIn("work:first", claim["available_research_evidence_ids"])
        self.assertNotIn("work:second", claim["available_research_evidence_ids"])
        self.assertEqual(set(claim["available_research_ids_by_facet"]), {"D1", "Q0"})
        self.assertFalse(claim["exceptions"]["missing_facet_summary"]["eligible"])
        self.assertEqual(bad, before)
        with self.assertRaisesRegex(editor.EditorialError, "historical_text_unavailable_for_claim"):
            editor.validate_editorial(bad, packet)

    def test_unavailable_counterevidence_cannot_be_masked_by_available_support(self):
        packet = copy.deepcopy(self.packet)
        next(card for card in packet["evidence_cards"] if card["evidence_id"] == "work:first")["experimental_text_available"] = False
        bad = copy.deepcopy(self.value)
        bad["claims"][0].update(supporting_ids=["event:accept"], counterevidence_ids=["work:first"])
        feedback = editor.editorial_repair_context(bad, packet, "historical_text_unavailable_for_claim")
        issue = next(item for item in feedback["issues"] if item["path"] == "/claims/0" and item["code"] == "historical_text_unavailable_for_claim")
        self.assertEqual(issue["unavailable_reference_paths"][0]["path"], "/claims/0/counterevidence_ids/0")
        self.assertTrue(issue["currently_violates_rule"])

    def test_feedback_explains_exact_missing_facet_and_metadata_exceptions(self):
        packet = copy.deepcopy(self.packet)
        next(card for card in packet["evidence_cards"] if card["evidence_id"] == "work:first")["experimental_text_available"] = False
        bad = copy.deepcopy(self.value)
        bad["direction_summaries"][0]["summary"] = editor.MISSING_VERSION_SUMMARY
        feedback = editor.editorial_repair_context(bad, packet, "historical_text_unavailable_for_claim")
        issue = next(item for item in feedback["accepted_exceptions"] if item["path"] == "/direction_summaries/0")
        self.assertFalse(issue["currently_violates_rule"])
        rule = issue["exceptions"]["missing_facet_summary"]
        self.assertTrue(rule["eligible"])
        self.assertTrue(rule["numeric_claims_must_be_empty"])
        self.assertTrue(rule["counterevidence_ids_must_be_empty"])
        self.assertEqual(rule["required_summary"], editor.MISSING_VERSION_SUMMARY)
        next(card for card in packet["evidence_cards"] if card["evidence_id"] == "event:accept")["experimental_text_available"] = False
        bad["organization_changes"] = [{**copy.deepcopy(bad["claims"][0]), "supporting_ids": ["event:accept"]}]
        feedback = editor.editorial_repair_context(bad, packet, "historical_text_unavailable_for_claim")
        issue = next(item for item in feedback["accepted_exceptions"] if item["path"] == "/organization_changes/0")
        self.assertFalse(issue["currently_violates_rule"])
        self.assertTrue(issue["exceptions"]["organization_metadata_only"]["eligible"])
        self.assertTrue(issue["exceptions"]["organization_metadata_only"]["all_references_must_be_events"])

    def test_feedback_lists_duplicate_conflicting_references_and_missing_localizations(self):
        bad = copy.deepcopy(self.value)
        bad["claims"][0].update(supporting_ids=["work:first", "work:first"], counterevidence_ids=["work:first"])
        bad["localizations"] = []
        feedback = editor.editorial_repair_context(bad, self.packet, "duplicate_or_conflicting_citations")
        issue = next(item for item in feedback["issues"] if item["code"] == "duplicate_or_conflicting_citations")
        self.assertEqual(issue["path"], "/claims/0")
        self.assertEqual(issue["duplicate_ids_by_role"]["supporting_ids"], ["work:first"])
        self.assertEqual(issue["conflicting_ids"], ["work:first"])
        localization = next(item for item in feedback["issues"] if item["code"] == "required_localization_missing")
        self.assertEqual(localization["path"], "/localizations")
        self.assertEqual(localization["missing_work_ids"], ["work:first"])
        self.assertEqual(localization["requirements"][0]["allowed_source_ids"], ["source:first"])
        self.assertTrue(localization["requirements"][0]["experimental_text_available"])
        with self.assertRaises(editor.EditorialError):
            editor.validate_editorial(bad, self.packet)

    def test_feedback_does_not_hide_unavailable_reference_behind_unknown_id(self):
        packet = copy.deepcopy(self.packet)
        next(card for card in packet["evidence_cards"] if card["evidence_id"] == "work:first")["experimental_text_available"] = False
        bad = copy.deepcopy(self.value)
        bad["claims"][0]["supporting_ids"] = ["missing:work", "work:first"]
        feedback = editor.editorial_repair_context(bad, packet, "citation_unknown_or_wrong_month")
        issue = next(item for item in feedback["issues"] if item["path"] == "/claims/0" and item["code"] == "historical_text_unavailable_for_claim")
        self.assertEqual(issue["unavailable_reference_paths"][0]["path"], "/claims/0/supporting_ids/1")
        self.assertFalse(issue["exceptions"]["missing_facet_summary"]["eligible"])

    def test_limitations_describe_partial_coverage_and_zero_verified_not_global_absence(self):
        self.snapshot["coverage"]["strict_peer_reviewed"] = 0
        self.catalog["manifestations"][0]["kind"] = "technical_report"
        packet = editor.build_evidence_packet(self.snapshot, self.catalog)
        limitations = packet["known_limitations"]
        self.assertTrue(any(item.startswith("部分公司报告或项目网页") for item in limitations))
        self.assertFalse(any(item.startswith("公司报告或项目网页尚无") for item in limitations))
        self.assertTrue(any("严格同行评审计数为零" in item and "不表示本月不存在" in item for item in limitations))
        self.assertTrue(any("摘要未提及" in item and "不代表论文全文没有" in item for item in limitations))
        self.assertTrue(any("子主题缺少可比历史证据" in item for item in limitations))
        self.assertEqual(packet["coverage"]["strict_peer_reviewed"], 0)

    def test_request_instructions_limit_monthly_scope_and_preserve_affordance_term(self):
        captured = []
        class Reply(io.BytesIO):
            def __enter__(self):
                return self
            def __exit__(self, *args):
                self.close()
        def fake_urlopen(request, timeout):
            captured.append(json.loads(request.data))
            return Reply(json.dumps(response(self.value)).encode())
        with patch.object(editor.urllib.request, "urlopen", fake_urlopen):
            editor.request_editorial(self.packet, "gpt-5.6-sol", "http://fixture.invalid", None)
        instructions = captured[0]["input"][0]["content"][0]["text"]
        for text in ["当月已登记", "子主题没有可比历史证据", "不写‘转向’‘开始’", "所提供摘要未披露", "affordance统一译为‘可供性’", "不代表该月不存在评审研究"]:
            self.assertIn(text, instructions)
        self.assertEqual(captured[0]["model"], "gpt-5.6-sol")
        self.assertTrue(captured[0]["text"]["format"]["strict"])

    def test_no_config_or_no_evidence_downgrades_without_provider_call(self):
        def should_not_call(*_):
            self.fail("No provider call expected")
        status = editor.run_month(self.packet, MONTH, self.output, requester=should_not_call)
        self.assertEqual(status["failure"], {"reason": "provider_not_configured", "attempts": 0})
        status = editor.run_month(None, "2026-09", self.output, base_url="http://localhost", requester=should_not_call)
        self.assertEqual(status["failure"]["reason"], "no_eligible_monthly_evidence")
        self.assertEqual(status["claims"], [])

    def test_cluster_sampling_avoids_repeated_project_and_uses_abstracts(self):
        self.catalog["works"][0]["strict_peer_reviewed"] = False
        self.catalog["works"][0]["curated"] = False
        for index in range(15):
            row = copy.deepcopy(self.catalog["works"][0])
            row["work_id"] = f"work:duplicate-{index}"
            self.catalog["works"].append(row)
            self.catalog["manifestations"].append({"work_id": row["work_id"], "kind": "preprint", "url": "https://example.test/paper", "public_at": "2026-08-04", "date_precision": "day"})
        packet = editor.build_evidence_packet(self.snapshot, self.catalog)
        self.assertEqual(packet["sampling"]["selected_works"], 2)
        self.assertTrue(all(row["abstract"] and row["source_urls"] for row in packet["evidence_cards"]))

    def test_sharded_authority_is_preferred_and_year_precision_excluded(self):
        directory = Path(self.temp.name) / "catalog"
        (directory / "works").mkdir(parents=True)
        (directory / "works/a.jsonl").write_text(json.dumps(self.catalog["works"][0]) + "\n")
        (directory / "works.jsonl").write_text(json.dumps(self.catalog["works"][1]) + "\n")
        self.assertEqual(editor.read_table(directory, "works")[0]["work_id"], "work:first")
        self.catalog["works"][0]["first_public_date_precision"] = "year"
        packet = editor.build_evidence_packet(self.snapshot, self.catalog)
        self.assertNotIn("work:first", {row["evidence_id"] for row in packet["evidence_cards"]})

    def test_all_month_selection_and_fixture_cli(self):
        manifest = {"complete_months": [f"2025-{i:02d}" for i in range(1, 13)] + [MONTH], "provisional_month": "2026-09"}
        months = editor.select_months(manifest, month=None, all_months=True)
        self.assertEqual(len(months), 13)
        self.assertEqual(months[-2:], [MONTH, "2026-09"])
        fixture = {"manifest": {"complete_months": [MONTH], "provisional_month": "2026-09"},
                   "catalog": self.catalog, "snapshots": {MONTH: self.snapshot}, "responses": {MONTH: response(self.value)}}
        path = Path(self.temp.name) / "fixture.json"
        path.write_text(json.dumps(fixture))
        with contextlib.redirect_stdout(io.StringIO()) as stream:
            result = editor.main(["--fixture", str(path), "--output-directory", str(self.output), "--all-months", "--allow-data-only"])
        self.assertEqual(result, 0)
        self.assertIn("complete", stream.getvalue())
        self.assertIn("data_only", stream.getvalue())
        self.assertFalse((self.output / "api").exists())

    def test_packet_hides_future_peer_assets_and_unproven_current_flags(self):
        work = self.catalog["works"][0]
        work.update(evidence_grade="E4", strict_peer_reviewed=True, evidence_flags={"real_robot": True, "open_code": True})
        self.catalog["manifestations"] += [
            {"work_id": work["work_id"], "manifestation_id": "future:peer", "kind": "conference", "peer_reviewed": True,
             "url": "https://example.test/future-peer", "accepted_at": "2026-09-01", "date_precision": "day", "publication_status": "accepted"},
            {"work_id": work["work_id"], "manifestation_id": "future:code", "kind": "code", "status": "official_release",
             "url": "https://example.test/future-code", "public_at": "2026-09-01", "date_precision": "day"}]
        packet = editor.build_evidence_packet({**self.snapshot, "evidence_as_of": "2026-08-31"}, self.catalog)
        card = next(row for row in packet["evidence_cards"] if row["evidence_id"] == work["work_id"])
        self.assertFalse(card["strict_peer_reviewed"])
        self.assertEqual(card["evidence_grade"], "E0")
        self.assertFalse(card["evidence_flags"]["real_robot"])
        self.assertFalse(card["evidence_flags"]["open_code"])
        self.assertEqual(card["output_types"], ["preprint"])
        self.assertNotIn("https://example.test/future-peer", card["source_urls"])

    def test_unknown_manifestation_date_does_not_leak_into_historical_packet(self):
        self.catalog["manifestations"][0].pop("public_at")
        packet = editor.build_evidence_packet(self.snapshot, self.catalog)
        self.assertNotIn("work:first", {row["evidence_id"] for row in packet["evidence_cards"]})

    def test_event_utc_boundary_is_converted_to_shanghai_month(self):
        self.catalog["evidence-events"][0]["published_at"] = "2026-08-31T18:00:00Z"
        packet = editor.build_evidence_packet(self.snapshot, self.catalog)
        self.assertNotIn("event:accept", {row["evidence_id"] for row in packet["evidence_cards"]})

    def test_localization_binds_full_original_text_and_refreshes_changed_source(self):
        self.run_editor()
        localized = editor.read_jsonl(self.output / "work-localizations.jsonl")[0]
        original = self.catalog["works"][0]
        self.assertTrue(editor.valid_work_localization(localized, original))
        self.assertFalse(editor.valid_work_localization({key: value for key, value in localized.items() if key != "source_content_digest"}, original))
        self.assertEqual(editor.localization_status({key: value for key, value in localized.items() if key != "source_content_digest"}, original), "legacy_source_review_required")
        self.catalog["work-localizations"] = [localized]
        translated_packet = editor.build_evidence_packet(self.snapshot, self.catalog)
        self.assertEqual(translated_packet["required_localization_ids"], [])
        self.assertEqual(editor.editorial_input_digest(translated_packet), editor.editorial_input_digest(self.packet))
        original["abstract"] += " Additional corrected source sentence."
        self.assertEqual(editor.localization_status(localized, original), "source_changed")
        changed = editor.build_evidence_packet(self.snapshot, self.catalog)
        self.assertIn(original["work_id"], changed["required_localization_ids"])
        self.assertNotEqual(editor.editorial_input_digest(changed), editor.editorial_input_digest(self.packet))

    def test_saved_overlay_requires_schema_citations_and_input_digest(self):
        self.run_editor()
        saved = json.loads((self.output / "monthly" / f"{MONTH}.json").read_text())
        self.assertTrue(editor.validated_editorial_overlay(saved, self.packet)["usable"])
        saved["claims"][0]["supporting_ids"] = ["work:does-not-exist"]
        self.assertEqual(editor.validated_editorial_overlay(saved, self.packet)["reason"], "saved_editorial_validation_failed")
        saved["input_digest"] = "0" * 64
        self.assertEqual(editor.validated_editorial_overlay(saved, self.packet)["reason"], "input_digest_changed")

    def test_retrospective_and_old_generated_summary_do_not_change_digest(self):
        before = editor.editorial_input_digest(self.packet)
        self.snapshot["retrospective_evidence"] = {"strict_peer_reviewed": 100}
        self.snapshot["claims"] = [{"summary": "Old generated text"}]
        self.snapshot["directions"][0]["summary"] = "Old generated direction text"
        self.assertEqual(editor.editorial_input_digest(editor.build_evidence_packet(self.snapshot, self.catalog)), before)
        self.snapshot["directions"][0]["primary_count"] = 99
        self.assertNotEqual(editor.editorial_input_digest(editor.build_evidence_packet(self.snapshot, self.catalog)), before)

    def test_signal_draft_round_trip_persists_separate_reviewable_records(self):
        card = next(row for row in self.packet["evidence_cards"] if row["work_id"] == "work:second")
        source = card["source_documents"][0]
        row = {"signal_id": "S1", "work_id": card["work_id"], "evidence_card_id": card["evidence_id"], "stance": "neutral",
               "statement": "摘要提出世界模型与基线的比较，尚不足以判断闭环控制收益。", "source_url": source["url"],
               "source_record_ids": [source["source_record_id"]], "public_at": source["public_at"], "public_at_precision": source["public_at_precision"],
               "research_scope": "in_scope", "experiment": {"setting": None, "baseline": "a baseline", "metric": None, "limitations": []},
               "source_spans": [{"field": "abstract", "start": 0, "end": len(card["abstract"]), "quote": card["abstract"]}]}
        self.value["signal_assessments"] = [row]
        self.run_editor()
        records = editor.read_jsonl(self.output / "signal-evidence.jsonl")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["review_status"], "draft")
        self.assertEqual(records[0]["review_history"], [])
        self.assertEqual(records[0]["source_text_snapshot"]["abstract"], card["abstract"])
        self.run_editor()
        self.assertEqual(editor.read_jsonl(self.output / "signal-evidence.jsonl"), records)
        self.value["signal_assessments"][0]["experiment"]["metric"] = "99% success"
        self.assert_invalid(self.value, "invalid_signal_assessment:experiment_not_verbatim_source")

    def test_strict_output_schema_cannot_claim_automatic_verification(self):
        self.value["signal_assessments"] = [{"review_status": "verified"}]
        self.assert_invalid(self.value, "schema_validation_failed")

    def test_versioned_card_uses_old_title_abstract_authors_and_digest(self):
        snapshot, catalog = version_fixture()
        packet = editor.build_evidence_packet(snapshot, catalog)
        card = next(row for row in packet["evidence_cards"] if row["work_id"] == "work:first")
        self.assertEqual(card["title"], "Original robot title")
        self.assertEqual(card["authors"], ["Original Author"])
        self.assertNotIn("99%", card["abstract"])
        self.assertEqual(card["summary_zh"], "")
        self.assertEqual(card["source_record_ids"], ["source:v1"])
        self.assertEqual(card["text_version"], "v1")
        self.assertEqual(card["text_snapshot_ids"], [catalog["text-snapshots"][0]["snapshot_id"]])
        self.assertEqual(card["source_content_digest"], editor.source_content_digest(catalog["text-snapshots"][0]))
        self.assertEqual(card["source_documents"][0]["public_at"], "2026-08-04T10:00:00Z")
        self.assertEqual(card["source_documents"][0]["public_at_precision"], "second")

    def test_missing_historical_version_keeps_work_but_blocks_experimental_prose(self):
        snapshot, catalog = version_fixture()
        catalog["text-snapshots"] = catalog["text-snapshots"][1:]
        packet = editor.build_evidence_packet(snapshot, catalog)
        card = next(row for row in packet["evidence_cards"] if row["work_id"] == "work:first")
        self.assertEqual(card["text_status"], "retrospective_only")
        self.assertEqual(card["abstract"], "")
        self.assertEqual(card["authors"], [])
        self.assertEqual(card["summary_zh"], "")
        self.assertTrue(card["title_is_current_identifier"])
        self.assertEqual(packet["coverage"]["included_works"], 2)
        self.assertNotIn("work:first", packet["required_localization_ids"])
        value = valid_editorial(packet)
        value["claims"] = []
        for family in ["direction_summaries", "question_summaries"]:
            for item in value[family]:
                if item["supporting_ids"] == ["work:first"]:
                    item["summary"] = editor.MISSING_VERSION_SUMMARY
        editor.validate_editorial(value, packet)
        value["claims"] = [{"title": "实验结果", "summary": "机器人实验得到改善。", "directions": ["D1"], "questions": ["Q0"], "supporting_ids": ["work:first"], "counterevidence_ids": [], "numeric_claims": []}]
        with self.assertRaisesRegex(editor.EditorialError, "historical_text_unavailable_for_claim"):
            editor.validate_editorial(value, packet)
        self.assertTrue(any("后续摘要" in message for message in packet["known_limitations"]))

    def test_unavailable_arxiv_does_not_fall_back_to_legacy_chinese(self):
        snapshot, catalog = version_fixture()
        catalog["text-snapshots"] = []
        card = next(row for row in editor.build_evidence_packet(snapshot, catalog)["evidence_cards"] if row["work_id"] == "work:first")
        self.assertEqual(card["text_status"], "unavailable")
        self.assertIsNone(card["title_zh"])
        self.assertEqual(card["summary_zh"], "")
        self.assertEqual(card["source_documents"], [])

    def test_synthetic_first_submitted_date_cannot_date_a_revised_text_draft(self):
        snapshot, catalog = version_fixture()
        first = catalog["text-snapshots"][0]
        first["source_record_id"] = "source:first"
        packet = editor.build_evidence_packet(snapshot, catalog)
        card = next(row for row in packet["evidence_cards"] if row["work_id"] == "work:first")
        self.assertEqual(card["text_status"], "available")
        self.assertEqual(card["source_documents"], [])
        self.assertNotIn("work:first", packet["signal_candidate_cards"]["S4"])
        self.assertTrue(any("首次投稿日" in message for message in packet["known_limitations"]))

    def test_translation_cache_is_bound_to_selected_version_not_current_canonical(self):
        snapshot, catalog = version_fixture()
        packet = editor.build_evidence_packet(snapshot, catalog)
        current = catalog["works"][0]
        old_translation = {"work_id": current["work_id"], "title_zh": "未来标题", "summary_zh": "未来修订摘要", "source_ids": ["source:v2"], "source_content_digest": editor.source_content_digest(current)}
        catalog["work-localizations"] = [old_translation]
        stale = editor.build_evidence_packet(snapshot, catalog)
        self.assertIn("work:first", stale["required_localization_ids"])
        self.assertNotIn("translation_context", next(row for row in stale["evidence_cards"] if row["work_id"] == "work:first"))
        selected = catalog["text-snapshots"][0]
        catalog["work-localizations"] = [{**old_translation, "title_zh": "原版标题", "summary_zh": "原版摘要", "source_ids": ["source:v1"], "source_content_digest": editor.source_content_digest(selected)}]
        valid = editor.build_evidence_packet(snapshot, catalog)
        self.assertNotIn("work:first", valid["required_localization_ids"])
        self.assertEqual(editor.editorial_input_digest(valid), editor.editorial_input_digest(packet))

    def test_monthly_digest_binds_snapshot_and_version_even_if_text_is_same(self):
        snapshot, catalog = version_fixture()
        before = editor.editorial_input_digest(editor.build_evidence_packet(snapshot, catalog))
        catalog["text-snapshots"][0]["snapshot_id"] += "-source-corrected"
        after = editor.editorial_input_digest(editor.build_evidence_packet(snapshot, catalog))
        self.assertNotEqual(before, after)
        catalog["works"][0]["summary_zh"] = "另外一版未经验证的摘要"
        self.assertEqual(after, editor.editorial_input_digest(editor.build_evidence_packet(snapshot, catalog)))

    def test_second_precision_signal_and_translation_persist_with_version_provenance(self):
        self.snapshot, self.catalog = version_fixture()
        self.packet = editor.build_evidence_packet(self.snapshot, self.catalog)
        self.value = valid_editorial(self.packet)
        card = next(row for row in self.packet["evidence_cards"] if row["work_id"] == "work:first")
        doc = card["source_documents"][0]
        self.value["signal_assessments"] = [{"signal_id": "S4", "work_id": card["work_id"], "evidence_card_id": card["evidence_id"], "stance": "neutral", "statement": "需要进一步核验研究与记忆机制的关系。",
                                            "source_url": doc["url"], "source_record_ids": [doc["source_record_id"]], "public_at": doc["public_at"], "public_at_precision": doc["public_at_precision"], "research_scope": "uncertain",
                                            "experiment": {"setting": None, "baseline": "a baseline", "metric": None, "limitations": []}, "source_spans": [{"field": "abstract", "start": 0, "end": len(card["abstract"]), "quote": card["abstract"]}]}]
        self.assertEqual(self.run_editor()["status"], "complete")
        translation = editor.read_jsonl(self.output / "work-localizations.jsonl")[0]
        self.assertEqual(translation["source_content_digest"], card["source_content_digest"])
        self.assertEqual(translation["text_version"], "v1")
        record = editor.read_jsonl(self.output / "signal-evidence.jsonl")[0]
        self.assertEqual(record["public_at_precision"], "second")
        self.assertEqual(record["public_at"], card["text_available_at"])
        self.assertEqual(record["review_status"], "draft")
        from scripts.signal_evidence import validate_signal_record
        self.assertEqual(validate_signal_record(record, self.catalog["works"][0], self.catalog["source-records"]), [])

    def test_catalog_loader_includes_persisted_text_snapshots(self):
        directory = Path(self.temp.name) / "catalog"
        directory.mkdir()
        (directory / "text-snapshots.jsonl").write_text('{"snapshot_id":"fixture"}\n')
        self.assertEqual(editor.load_catalog(directory)["text-snapshots"], [{"snapshot_id": "fixture"}])


if __name__ == "__main__":
    unittest.main()
