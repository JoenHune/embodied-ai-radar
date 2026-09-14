"""Report excerpt facts reach editorial, search and export without backdating."""
import argparse
import contextlib
import copy
import io
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
from test_report_text import fixture, snapshot_id_for
from catalog_store import TABLES, fingerprint
import build_v3_catalog as builder
import generate_v3_editorial as editor
from audit_v3 import audit_month_report_views
from report_editorial import editorial_source_digest, report_editorial_view, add_report_facts, render_report_measurements
from report_text import report_text_as_of
from signal_evidence import source_content_digest


def packet_fixture(*, archived=True, cutoff="2026-08-31"):
    initial, report = fixture(archived=archived)
    catalog = {table: initial.get(table, []) for table in TABLES}
    work = catalog["works"][0]
    work.update(relevance={"status": "included", "score": 3, "classifier_version": "fixture"}, directions=["D1"], questions=["Q6"],
                first_public_date_precision="day", curated=True, facets={}, manifestation_ids=[report["manifestation_id"]], classification_state="accepted")
    release = {"source_record_id": "source:release", "url": report["report_url"], "published_at": "2026-08-19", "source_type": "official_company_report"}
    catalog["source-records"].append(release)
    work["source_record_ids"].append(release["source_record_id"])
    catalog["manifestations"][0].update(source_record_id=release["source_record_id"], status="technical_report")
    catalog["report-text-snapshots"] = [report]
    snapshot = {"month": "2026-08", "status": "complete", "evidence_as_of": cutoff, "coverage": {"included_works": 1},
                "directions": [{"code": "D1", "primary_count": 1, "multi_label_count": 1, "share": 1}],
                "questions": [{"code": "Q6", "count": 1}], "evidence_lanes": {"technical_report": 1}, "evidence_grades": {"E1": 1}}
    return snapshot, catalog, report


def response_fixture(packet):
    card = packet["evidence_cards"][0]
    metric, fact = next((key, value) for key, value in packet["facts"].items() if key.startswith("report."))
    claim = {"title": "公司报告的有条件结果", "summary": "公司自报提供了适配实验，尚需独立验证。",
             "directions": ["D1"], "questions": ["Q6"], "supporting_ids": [card["evidence_id"]], "counterevidence_ids": [],
             "numeric_claims": [{"metric": metric, "value": 59, "unit": "percentage", "evidence_ids": [card["evidence_id"]]}]}
    summary = {"summary": "公司自报涉及少样本适配，结果仍需进一步验证。", "supporting_ids": [card["evidence_id"]], "counterevidence_ids": [], "numeric_claims": []}
    return {"month": "2026-08", "claims": [claim], "direction_summaries": [{"code": "D1", **summary}],
            "question_summaries": [{"code": "Q6", **summary}], "organization_changes": [], "counterevidence": [], "watchlist": [],
            "limitations": packet["known_limitations"], "signal_assessments": [],
            "localizations": [{"work_id": card["work_id"], "title_zh": "通才模型少样本适配", "summary_zh": "公司自报的适配方法，仍需独立验证。", "keywords_zh": ["适配"], "source_ids": card["source_record_ids"]}]}


class ReportEditorialTests(unittest.TestCase):
    def test_audited_report_uses_separate_excerpts_not_a_fabricated_abstract(self):
        snapshot, catalog, report = packet_fixture()
        catalog["works"][0]["summary_zh"] = "后来的旧中文说明99%。"
        original = fingerprint(catalog)
        packet = editor.build_evidence_packet(snapshot, catalog)
        card = packet["evidence_cards"][0]
        self.assertTrue(card["experimental_text_available"])
        self.assertEqual(card["text_status"], "report_excerpt_available")
        self.assertEqual(card["abstract"], "")
        self.assertEqual(card["summary_zh"], "")
        self.assertEqual(card["source_record_ids"], [report["source_record_id"]])
        self.assertEqual(card["source_documents"][0]["public_at"], report["available_at"])
        self.assertEqual(packet["facts"]["coverage.included_works"]["value"], 1)
        self.assertEqual(fingerprint(catalog), original)
        editor.validate_editorial(response_fixture(packet), packet)

    def test_fresh_capture_and_prearchive_cutoffs_keep_only_metadata(self):
        for options in [{"archived": False}, {"cutoff": "2026-08-20"}]:
            snapshot, catalog, _ = packet_fixture(**options)
            packet = editor.build_evidence_packet(snapshot, catalog)
            self.assertEqual(len(packet["evidence_cards"]), 1)
            self.assertFalse(packet["evidence_cards"][0]["experimental_text_available"])
            self.assertFalse(any(key.startswith("report.") for key in packet["facts"]))
            self.assertEqual(packet["required_localization_ids"], [])

    def test_report_numeric_prose_cannot_swap_or_omit_context(self):
        snapshot, catalog, _ = packet_fixture()
        packet = editor.build_evidence_packet(snapshot, catalog)
        for text in ["公司自报达到59%。", "公司自报：单次示教为83%；多次示教为59%。", "公司自报：单次为83、多次为59。", "公司自报需要9999步适配。"]:
            value = response_fixture(packet)
            value["claims"][0]["summary"] = text
            with self.assertRaisesRegex(editor.EditorialError, "report_numeric_prose_must_be_structured"):
                editor.validate_editorial(value, packet)

    def test_report_measurements_are_rendered_only_from_bound_facts(self):
        snapshot, catalog, _ = packet_fixture()
        packet = editor.build_evidence_packet(snapshot, catalog)
        value = response_fixture(packet)
        original = copy.deepcopy(value["claims"][0])
        rendered = render_report_measurements(original, packet["facts"])
        self.assertIn("59%", rendered["summary"])
        self.assertIn("GEN-1.5（公司自报）", rendered["summary"])
        self.assertIn(next(v for k,v in packet["facts"].items() if k.startswith("report."))["required_context"], rendered["summary"])
        self.assertNotIn("83%", rendered["summary"])
        self.assertEqual(original, value["claims"][0])
        self.assertNotIn("59", original["summary"])

    def test_missing_report_owner_is_rejected_even_without_numbers(self):
        snapshot, catalog, _ = packet_fixture()
        packet = editor.build_evidence_packet(snapshot, catalog)
        value = response_fixture(packet)
        value["claims"][0]["summary"] = "适配实验已经独立验证。"
        with self.assertRaisesRegex(editor.EditorialError, "report_numeric_context_missing"):
            editor.validate_editorial(value, packet)

    def test_report_localization_cannot_hide_unbound_numbers_or_owner(self):
        snapshot, catalog, _ = packet_fixture()
        packet = editor.build_evidence_packet(snapshot, catalog)
        for text in ["公司自报成功率59%。", "适配能力得到验证。"]:
            value = response_fixture(packet)
            value["localizations"][0]["summary_zh"] = text
            with self.assertRaisesRegex(editor.EditorialError, "report_localization_requires_qualitative_attribution"):
                editor.validate_editorial(value, packet)

    def test_report_cards_do_not_enter_abstract_based_signal_protocol(self):
        snapshot, catalog, _ = packet_fixture()
        packet = editor.build_evidence_packet(snapshot, catalog)
        self.assertTrue(all(not ids for ids in packet["signal_candidate_cards"].values()))

    def test_tampered_observation_is_rejected_before_provider_input(self):
        snapshot, catalog, report = packet_fixture()
        report["observations"][0]["context"] = "Invented matched-budget comparison"
        report["snapshot_id"] = snapshot_id_for(report)
        with self.assertRaisesRegex(editor.EditorialError, "invalid_report_text_catalog"):
            editor.build_evidence_packet(snapshot, catalog)

    def test_duplicate_cards_share_one_numeric_fact_not_extra_work_counts(self):
        snapshot, catalog, _ = packet_fixture()
        packet = editor.build_evidence_packet(snapshot, catalog)
        card = packet["evidence_cards"][0]
        facts = {}
        add_report_facts(facts, [card, {**card, "evidence_id": "event:same-work"}])
        self.assertEqual(len(facts), 1)
        self.assertEqual(len(next(iter(facts.values()))["evidence_ids"]), 2)
        self.assertEqual(next(iter(facts.values()))["value"], 59)

    def test_report_localization_digest_changes_with_source_and_matches_node(self):
        snapshot, catalog, report = packet_fixture()
        work = catalog["works"][0]
        selected = report_text_as_of(work, [report], "2026-08")
        view = report_editorial_view(work, selected)
        before = editorial_source_digest(view)
        script = "import fs from 'node:fs'; import {sourceTextDigest} from './scripts/lib/versioned-search-text.mjs'; console.log(sourceTextDigest(JSON.parse(fs.readFileSync(0,'utf8'))));"
        result = subprocess.run(["node", "--input-type=module", "-e", script], cwd=ROOT, input=json.dumps(view), text=True, capture_output=True, check=True)
        self.assertEqual(result.stdout.strip(), before)
        changed = copy.deepcopy(view)
        changed["report_text"]["snapshots"][0]["snapshot_id"] = "report-text:new-version"
        self.assertNotEqual(editorial_source_digest(changed), before)
        self.assertEqual(editorial_source_digest(work), source_content_digest(work))
        self.assertIsNone(builder.localization_source_view(work, {}, {"status": "retrospective_only", "snapshot_ids": []}))

    def test_public_json_sqlite_and_monthly_views_have_exact_report_snapshot(self):
        _, catalog, report = packet_fixture()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            equipment = root / 'data/equipment'
            equipment.mkdir(parents=True)
            for table in ('devices', 'usage-evidence', 'loco-reviews', 'loco-observations'):
                (equipment / (table + '.jsonl')).write_text('')
            (root / "scripts").mkdir()
            (root / "config").mkdir()
            for name in builder.RULE_SOURCE_FILES:
                (root / "scripts" / name).parent.mkdir(parents=True, exist_ok=True)
                (root / "scripts" / name).write_text("fixture")
            for name in builder.RULE_CONFIG_FILES:
                (root / "config" / name).write_text("{}")
            (root / "config/taxonomy-v2.json").write_text(json.dumps({"categories": {str(i): {"code": f"D{i}", "label": f"Direction {i}"} for i in range(1,16)}}))
            (root / "config/research-agenda.json").write_text(json.dumps({"questions": [{"id": f"Q{i}", "title": f"Question {i}"} for i in range(11)]}))
            (root / "config/conference-editions.json").write_text('{"editions":[]}')
            (root / "config/trend-signals.json").write_text('{"signals":[]}')
            api = root / "api"
            args = argparse.Namespace(as_of="2026-08-31", ingest=False, migrate=False)
            before = fingerprint(catalog)
            with patch.multiple(builder, ROOT=root, DATA=root/"data", CATALOG=root/"data/catalog", PUBLIC_API=api, DOWNLOADS=root/"downloads"), contextlib.redirect_stdout(io.StringIO()):
                builder.export_catalog(catalog, {"data_through":"2026-08-31","catalog_hash":"fixture","input_counts":{}}, args)
            self.assertEqual(fingerprint(catalog), before)
            self.assertEqual(json.loads((api/"report-text-snapshots.json").read_text()), [report])
            month = json.loads((api/"monthly/2026-08.json").read_text())
            self.assertEqual(month["coverage"]["reports_with_dated_text"], 1)
            self.assertEqual(month["report_text_evidence"][0]["selection"]["snapshots"], [report])
            audit_args = ("2026-08", catalog["works"], {catalog["works"][0]["work_id"]:catalog["manifestations"]},
                          {row["source_record_id"]:row for row in catalog["source-records"]},
                          {catalog["works"][0]["work_id"]:[report]}, "2026-08-31")
            audit_month_report_views(month, *audit_args)
            for mutate in [lambda row: row.update(report_text_evidence=[]),
                           lambda row: row["coverage"].update(reports_with_dated_text=0),
                           lambda row: row["retrospective_evidence"].update(report_text_evidence=[]),
                           lambda row: row.update(evidence_as_of="2026-09-06")]:
                changed = copy.deepcopy(month)
                mutate(changed)
                with self.assertRaises(AssertionError):
                    audit_month_report_views(changed, *audit_args)
            with sqlite3.connect(root/"downloads/radar.sqlite") as connection:
                saved = connection.execute("SELECT canonical_work_id,payload_json FROM report_text_snapshots").fetchone()
                self.assertEqual(saved[0], catalog["works"][0]["work_id"])
                self.assertEqual(json.loads(saved[1]), report)
                self.assertEqual(connection.execute("SELECT count(*) FROM works").fetchone()[0], 1)
            connection.close()


if __name__ == "__main__":
    unittest.main()
