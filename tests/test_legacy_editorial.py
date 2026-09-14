"""Exact identity, preservation and review-state tests for historical editing."""
from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("legacy", ROOT / "scripts/import_legacy_editorial.py")
legacy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(legacy)


class LegacyEditorialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="legacy-editorial-fixture-")
        self.output = Path(self.temp.name) / "output"
        self.works = [
            {"work_id": "doi:10.fixture/first", "title": "First fixture", "identifiers": {"arxiv": "2608.00001"},
             "relevance": {"status": "included"}, "classification_state": "accepted", "first_public_date": "2026-08-01",
             "first_public_date_precision": "day", "directions": ["D1"], "questions": ["Q0"]},
            {"work_id": "arxiv:2608.00002", "title": "Second fixture", "identifiers": {"arxiv": "2608.00002"},
             "relevance": {"status": "manual_review"}, "classification_state": "review_required", "first_public_date": "2026-08-02",
             "first_public_date_precision": "day", "directions": ["D3"], "questions": ["Q1"]},
        ]
        self.aliases = [{"alias": "arxiv:2608.00001", "work_id": "doi:10.fixture/first"}]
        self.versions = [{"work_id": "doi:10.fixture/first", "url": "https://arxiv.org/abs/2608.00001"}]
        self.trends = {"months": {
            "2025-08": [{"title": "Historical card", "change": "原有研究判断。", "evidence_ids": ["2608.00001"], "grade": "B", "kind": "consensus"}],
            "2026-08": [{"title": "Current historical card", "change": "旧编辑正文原样保留。", "comparison": "旧环比为 20%。",
                         "evidence_ids": ["2608.00001", "2608.00002"], "grade": "C", "kind": "weak", "bottleneck": "旧瓶颈说明。"},
                        {"title": "Missing reference card", "change": "缺少映射也不能删除正文。", "evidence_ids": ["2608.99999"]}]
        }}
        self.papers = [{"id": "2608.00001", "title": "First fixture", "v1_month": "2026-08", "contribution_zh": "原始贡献。",
                        "limitation_zh": "原始局限；不是独立反证。", "selection_reason_zh": "原始入选理由。"}]
        self.directions = {"foundation": {"label": "旧基础模型方向", "representative_ids": ["2608.00001"], "definition": "历史定义。"}}
        self.forecasts = {"as_of": "2026-08-31", "signals": [{"title": "未来假设", "judgment": "可能出现新的验证路线。",
                           "observed": "已有可引用工作。", "confirm": "未来可检验条件。", "falsifier": "未来反证条件。",
                           "evidence_ids": ["2608.00001"], "confidence": "低", "horizon": "3–9个月"}]}

    def tearDown(self):
        self.temp.cleanup()

    def resolver(self):
        return legacy.Resolver(self.works, self.aliases, self.versions)

    def restore(self):
        return legacy.restore(self.trends, self.papers, self.directions, self.forecasts, self.resolver(),
                              ["2026-08"], "2026-09", self.output)

    def month(self, value="2026-08"):
        return json.loads((self.output / f"{value}.json").read_text())

    def test_exact_arxiv_versions_urls_and_aliases_map_to_canonical_doi(self):
        for identifier in ("2608.00001", "2608.00001v3", "arxiv:2608.00001", "https://arxiv.org/abs/2608.00001v4", "https://arxiv.org/pdf/2608.00001.pdf"):
            row = self.resolver().resolve(identifier, "2026-08")
            self.assertEqual(row["work_id"], "doi:10.fixture/first")
            self.assertEqual(row["mapping_status"], "exact")

    def test_title_similarity_does_not_resolve_unknown_id(self):
        self.works[0]["title"] = "2608.99999"
        row = self.resolver().resolve("2608.99999", "2026-08")
        self.assertIsNone(row["work_id"])
        self.assertEqual(row["mapping_status"], "unresolved")
        self.assertEqual(row["source_urls"], ["https://arxiv.org/abs/2608.99999"])

    def test_ambiguous_aliases_remain_unresolved(self):
        self.aliases.append({"alias": "2608.00001", "work_id": "arxiv:2608.00002"})
        row = self.resolver().resolve("2608.00001", "2026-08")
        self.assertEqual(row["mapping_status"], "ambiguous")
        self.assertIsNone(row["work_id"])
        self.assertEqual(len(row["candidate_work_ids"]), 2)

    def test_multiple_registered_arxiv_identifiers_are_resolved_exactly(self):
        self.works[0]["identifier_aliases"] = {"arxiv": ["2607.12345", "2608.00001"]}
        self.assertEqual(self.resolver().resolve("2607.12345")["work_id"], "doi:10.fixture/first")

    def test_all_cards_are_reconciled_including_outside_window(self):
        report = self.restore()
        self.assertEqual(report["source_counts"]["trend_cards"], 3)
        self.assertEqual(report["restored_counts"]["trend_cards"], 3)
        self.assertEqual(report["restored_counts"]["active_window_trend_cards"], 2)
        self.assertFalse(self.month("2025-08")["in_active_window"])
        old = next(row for row in report["cards"] if row["month"] == "2025-08")
        self.assertEqual(old["disposition"], "restored_archive_outside_default_window")
        self.assertEqual(self.month("2026-09")["claims"], [])

    def test_manual_review_and_missing_refs_do_not_drop_or_upgrade_card(self):
        before = copy.deepcopy(self.works)
        self.restore()
        current, missing = self.month()["claims"]
        self.assertTrue(current["evidence_review_required"])
        self.assertEqual(current["review_required_work_ids"], ["arxiv:2608.00002"])
        self.assertEqual(missing["supporting_ids"], [])
        self.assertEqual(missing["unresolved_legacy_ids"], ["2608.99999"])
        self.assertTrue(missing["evidence_review_required"])
        self.assertEqual(self.works, before)

    def test_future_evidence_flagged_while_older_context_allowed(self):
        resolver = self.resolver()
        self.assertIn("evidence_postdates_editorial_month", resolver.resolve("2608.00001", "2025-08")["review_reasons"])
        self.assertEqual(resolver.resolve("2608.00001", "2026-09")["temporal_role"], "historical_context")
        self.assertEqual(resolver.resolve("2608.00001", "2026-09")["review_reasons"], [])

    def test_original_wording_grade_and_source_hash_are_preserved(self):
        self.restore()
        row = self.month()["claims"][0]
        source = self.trends["months"]["2026-08"][0]
        self.assertEqual(row["original_record"], source)
        self.assertEqual(row["summary"], source["change"])
        self.assertEqual(row["legacy_grade"], "C")
        self.assertNotIn("evidence_grade", row)
        self.assertEqual(row["original_source"]["record_sha256"], legacy.digest(source))
        self.assertEqual(row["status"], "legacy_editorial")
        self.assertNotIn("llm", row["generator"])

    def test_paper_contributions_limitations_and_selection_reason_survive(self):
        self.restore()
        row = self.month()["work_notes"][0]
        self.assertEqual(row["work_id"], "doi:10.fixture/first")
        self.assertEqual(row["contribution_zh"], self.papers[0]["contribution_zh"])
        self.assertEqual(row["limitation_zh"], self.papers[0]["limitation_zh"])
        self.assertEqual(row["selection_reason_zh"], self.papers[0]["selection_reason_zh"])
        self.assertEqual(row["counterevidence_ids"], [])
        self.assertEqual(legacy.read_table(self.output, "work-notes")[0]["limitation_zh"], row["limitation_zh"])

    def test_historical_comparison_does_not_masquerade_as_current_statistics(self):
        self.restore()
        self.assertTrue(self.month()["claims"][0]["historical_statistic_review_required"])
        self.assertEqual(self.month()["claims"][0]["comparison"], "旧环比为 20%。")
        self.assertIn("未作为当前统计值", self.month()["limitations"][1])

    def test_direction_context_not_inserted_as_monthly_findings(self):
        self.restore()
        context = json.loads((self.output / "context.json").read_text())
        self.assertEqual(context["direction_context"][0]["monthly_use"], "background_only_not_monthly_observation")
        self.assertIsNone(context["direction_context"][0]["as_of"])
        self.assertNotIn("历史定义。", [row["summary"] for row in self.month()["claims"]])

    def test_forecasts_keep_asof_and_falsification_without_claiming_outcomes(self):
        self.restore()
        forecast = self.month()["historical_watchlist"][0]
        self.assertEqual(forecast["as_of"], "2026-08-31")
        self.assertEqual(forecast["status"], "legacy_forecast")
        self.assertFalse(forecast["outcome_verified"])
        self.assertEqual(forecast["falsifier"], self.forecasts["signals"][0]["falsifier"])
        self.assertEqual(self.month("2026-09")["historical_watchlist"], [])

    def test_repeated_import_is_byte_identical(self):
        self.restore()
        before = {path.name: path.read_bytes() for path in self.output.iterdir() if path.is_file()}
        self.restore()
        after = {path.name: path.read_bytes() for path in self.output.iterdir() if path.is_file()}
        self.assertEqual(before, after)

    def test_canonical_direction_union_does_not_reuse_old_five_categories(self):
        self.restore()
        row = self.month()["claims"][0]
        self.assertEqual(row["directions"], ["D1", "D3"])
        self.assertEqual(row["direction_assignment"], "canonical_evidence_union")

    def test_shards_take_precedence_over_legacy_combined_file(self):
        directory = Path(self.temp.name) / "catalog"
        (directory / "works").mkdir(parents=True)
        (directory / "works/a.jsonl").write_text(json.dumps(self.works[0]) + "\n")
        (directory / "works.jsonl").write_text(json.dumps(self.works[1]) + "\n")
        self.assertEqual(legacy.read_table(directory, "works"), [self.works[0]])


if __name__ == "__main__":
    unittest.main()
