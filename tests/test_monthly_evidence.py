"""Integration checks on actual exported monthly JSON, never production data."""
import argparse
import contextlib
import io
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_v3_catalog as builder
from catalog_store import fingerprint
from test_catalog_rules import empty_payload, work
from trend_signals import assess_signal


class MonthlyEvidenceTest(unittest.TestCase):
    def test_missing_hardware_dictionary_fails_before_any_public_export(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = argparse.Namespace(as_of='2026-09-14', ingest=False, migrate=False)
            with patch.multiple(builder, ROOT=root, DATA=root / 'data', CATALOG=root / 'data/catalog',
                                PUBLIC_API=root / 'api', DOWNLOADS=root / 'downloads'):
                with self.assertRaisesRegex(FileNotFoundError, 'hardware_coverage_dictionary_required'):
                    builder.export_catalog({}, {}, args)
            self.assertFalse((root / 'api').exists())
            self.assertFalse((root / 'downloads').exists())

    def test_monthly_org_projection_keeps_work_id_and_declared_date_precision(self):
        event = {"event_id": "report-event", "work_id": "report:fixture", "organization_id": "org:fixture",
                 "event_type": "technical_report", "title": "A company report", "url": "https://example.test/report",
                 "published_at": "2026-08-01", "date_precision": "month"}
        original = fingerprint(event)
        compact = builder.monthly_organization_change(event, {"display_name": "Fixture Company", "tier": "T0"})
        self.assertEqual(compact["date_precision"], "month")
        self.assertEqual(compact["published_at"], "2026-08-01")
        self.assertEqual(compact["work_id"], "report:fixture")
        self.assertEqual(fingerprint(event), original)
        event.pop("date_precision")
        self.assertEqual(builder.monthly_organization_change(event, {})["date_precision"], "unknown")

    def test_translation_requires_available_edition_and_selected_source_ownership(self):
        from generate_v3_editorial import valid_work_localization, source_content_digest
        row = {**work(), "title": "Future revision", "abstract": "New September experiment", "source_record_ids": ["old", "new"]}
        localization = {"work_id": row["work_id"], "title_zh": "新修订", "summary_zh": "新的实验结论", "source_ids": ["new"], "source_content_digest": source_content_digest(row)}
        self.assertTrue(valid_work_localization(localization, row))
        for status in ["unavailable", "retrospective_only", "conflicting_snapshots"]:
            self.assertIsNone(builder.localization_source_view(row, {"status": status, "title": None, "abstract": None}))
        # Identical wording does not let a future/other edition supply a citation.
        selected = {"status": "available", "title": row["title"], "abstract": row["abstract"], "source_ids": ["old"]}
        view = builder.localization_source_view(row, selected)
        self.assertFalse(valid_work_localization(localization, view))
        selected["source_ids"] = ["new"]
        self.assertTrue(valid_work_localization(localization, builder.localization_source_view(row, selected)))

    def test_one_validation_event_is_visible_to_all_evidenced_collaborators(self):
        event = {"event_id": "acceptance", "event_type": "accepted", "work_id": "w", "organization_id": None}
        links = {"w": {"lab-a": {"evidence_grade": "G1", "evidence_url": "https://a.edu/papers"}, "lab-b": {"evidence_grade": "G2", "evidence_url": "https://b.edu/people"}}}
        result = builder.organization_event_views([event], links)
        self.assertEqual(len(result), 2)
        self.assertEqual({row["organization_id"] for row in result}, {"lab-a", "lab-b"})
        self.assertEqual({row["event_id"] for row in result}, {"acceptance"})
        self.assertIsNone(event["organization_id"])

    def test_export_separates_historical_and_retrospective_peer_review(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data, api = root / "data", root / "public/api/v1"
            equipment = data / "equipment"
            equipment.mkdir(parents=True)
            for table in ('devices', 'usage-evidence', 'loco-reviews', 'loco-observations'):
                (equipment / (table + '.jsonl')).write_text('')
            config = root / "config"
            config.mkdir(parents=True)
            (root / "scripts").mkdir()
            for name in builder.RULE_SOURCE_FILES:
                (root / "scripts" / name).parent.mkdir(parents=True, exist_ok=True)
                (root / "scripts" / name).write_text("fixture")
            for name in builder.RULE_CONFIG_FILES:
                (config / name).write_text("{}")
            (config / "hardware-dictionary.json").write_text('{"schema_version":"1","version":"fixture-empty","entries":[]}')
            (config / "trend-signals.json").write_text('{"signals": []}')
            (config / "conference-editions.json").write_text('{"editions": []}')
            (config / "taxonomy-v2.json").write_text(json.dumps({"categories": {str(i): {"code": f"D{i}", "label": f"Direction {i}"} for i in range(1, 16)}}))
            (config / "research-agenda.json").write_text(json.dumps({"questions": [{"id": f"Q{i}", "title": f"Question {i}"} for i in range(11)]}))
            payload = empty_payload()
            row = work()
            row.update(first_public_date="2026-08-01", abstract="A robot policy study", evidence_grade="E3", strict_peer_reviewed=True, evidence_flags={})
            row["source_record_ids"] = ["preprint", "decision"]
            payload["works"] = [row]
            payload["source-records"] = [{"source_record_id": "preprint", "url": "https://arxiv.org/abs/2608.00001"}, {"source_record_id": "decision", "url": "https://openreview.net/forum?id=official", "source_type": "official_openreview_decision"}]
            payload["manifestations"] = [
                {"manifestation_id": "preprint", "work_id": row["work_id"], "kind": "preprint", "url": "https://arxiv.org/abs/2608.00001", "published_at": "2026-08-01", "date_precision": "day", "status": "preprint", "peer_reviewed": False, "source_record_id": "preprint"},
                {"manifestation_id": "decision", "work_id": row["work_id"], "kind": "conference", "url": "https://openreview.net/forum?id=official", "accepted_at": "2026-09-04T12:00:00Z", "date_precision": "day", "status": "accepted_peer_reviewed", "peer_reviewed": True, "source_record_id": "decision", "venue": "CoRL", "year": 2026},
            ]
            payload["evidence-events"] = [{"event_id": "accepted", "work_id": row["work_id"], "event_type": "accepted", "attribution_grade": "G1", "published_at": "2026-09-04T12:00:00Z", "url": "https://openreview.net/forum?id=official", "title": row["title"], "research_eligible": True}]
            before = fingerprint(payload)
            args = argparse.Namespace(as_of="2026-09-05", ingest=False, migrate=False)
            with patch.multiple(builder, ROOT=root, DATA=data, CATALOG=data / "catalog", PUBLIC_API=api, DOWNLOADS=root / "downloads"), contextlib.redirect_stdout(io.StringIO()):
                builder.export_catalog(payload, {"data_through": "2026-09-05", "catalog_hash": "fixture", "input_counts": {}}, args)
            august = json.loads((api / "monthly/2026-08.json").read_text())
            september = json.loads((api / "monthly/2026-09.json").read_text())
            self.assertEqual(august["coverage"]["included_works"], 1)
            self.assertEqual(august["coverage"]["strict_peer_reviewed"], 0)
            self.assertEqual(august["evidence_grades"]["E0"], 1)
            self.assertNotIn("conference", august["evidence_lanes"])
            self.assertEqual(august["retrospective_evidence"]["strict_peer_reviewed"], 1)
            self.assertEqual(august["retrospective_evidence"]["evidence_grades"]["E3"], 1)
            self.assertEqual(september["coverage"]["included_works"], 0)
            self.assertEqual([event["event_id"] for event in september["evidence_events"]], ["accepted"])
            self.assertTrue((api / "monthly/2025-09.json").exists(), "Empty months in the required window must also exist")
            self.assertEqual(fingerprint(payload), before, "Export must not mutate canonical input")
            coverage = json.loads((api / 'equipment/coverage-summary.json').read_text())
            manifest = json.loads((api / 'catalog-manifest.json').read_text())
            self.assertEqual(coverage['all_works']['denominator'], len(payload['works']))
            self.assertEqual(coverage['dataset_version'], manifest['dataset_version'])
            self.assertEqual(manifest['equipment']['coverage_api'], '/api/v1/equipment/coverage-summary.json')
            self.assertTrue((root / 'downloads/equipment/hardware-coverage.jsonl.gz').is_file())
            connection = sqlite3.connect(root / "downloads/radar.sqlite")
            self.assertEqual(connection.execute("PRAGMA page_size").fetchone()[0], 16384)
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM hardware_coverage').fetchone()[0], len(payload['works']))
            restored = json.loads(connection.execute("SELECT payload_json FROM work_payloads WHERE work_id=?", (row["work_id"],)).fetchone()[0])
            self.assertEqual(restored["abstract"], row["abstract"])
            self.assertEqual(restored["authors"], row["authors"])
            self.assertTrue(restored["strict_peer_reviewed"])
            self.assertIn("title_zh", restored)
            self.assertIsNone(restored["title_zh"])
            self.assertEqual(restored["source_record_ids"], sorted(row["source_record_ids"]))
            connection.close()

    def test_retrospective_signal_does_not_add_newer_works_to_original_cohort(self):
        spec = {"signal_id": "S1", "title": "A research question", "terms": ["policy"], "required_terms": ["robot"]}
        a, b = work("a"), work("b")
        a["first_public_date"], b["first_public_date"] = "2026-08-01", "2026-09-01"
        past = assess_signal(spec, [a, b], ["2026-07", "2026-08"], {}, {}, evidence_cutoff="2026-09-05")
        self.assertEqual(past["months"], ["2026-07", "2026-08"])
        self.assertEqual(past["counts"], [0, 1])
        self.assertEqual(past["candidate_work_ids"], ["a"])
        self.assertEqual(past["evidence_as_of"], "2026-09-05")


if __name__ == "__main__":
    unittest.main()
