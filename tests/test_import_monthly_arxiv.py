"""Offline temporary-directory tests; no production --apply or network calls."""
import contextlib
import copy
import importlib.util
import io
import json
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("import_monthly_arxiv", ROOT / "scripts/import_monthly_arxiv.py")
monthly = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monthly)
CUTOFF = date(2026, 9, 14)
NOW = datetime(2026, 9, 14, 12, tzinfo=timezone.utc)


def record(ident="2609.00001", status="included"):
    return {"arxiv_id": ident, "work_id": "arxiv:" + ident, "preprint_id": "arxiv:" + ident,
            "title": "Original title", "raw_title": "Original\n title", "abstract": "Robot x < y and $a>b$.",
            "raw_abstract": "Robot x < y\n and $a>b$.", "authors": ["A. Author"], "raw_authors": ["A. Author"],
            "first_submitted": "2026-09-11", "updated": "2026-09-11",
            "submitted_at": "2026-09-11", "updated_at": "2026-09-11",
            "submitted_at_precision": "day", "updated_at_precision": "day", "date_precision": "day",
            "version": "v1", "arxiv_version_id": ident + "v1", "period": "provisional", "cohort_status": "provisional",
            "metadata_temporal_basis": "official_search;time_of_day_not_exposed",
            "relevance": {"status": status, "score": 0}, "included": status == "included",
            "source_observations": [{"source_url": "https://arxiv.org/search/advanced?query=robot", "raw_sha256": "a" * 64,
                                     "fetched_at": "2026-09-14T01:00:00Z", "raw_file": "outside-staging/page.html"}],
            "custom_field": {"keep": [None, False, 1.2]}}


def coverage(count=1):
    return {"month": "2026-09", "records": count, "cohort_status": "provisional", "month_closed": False,
            "requested_window": {"from": "2026-09-01", "until": "2026-09-14", "basis": "first_submission_date_UTC"},
            "first_submission_day_max": "2026-09-11", "collection_finished_at": "2026-09-14T01:00:00Z",
            "api_collection_manifest": "api.json", "core_cs_ro": {"advertised_month_list_total": count,
                "listed_unique_ids": count, "listing_pagination_complete": True, "metadata_complete_for_observed_month_list": True},
            "supplementary": {key: {"status": "ok", "complete_pagination": True,
                "search_advertised_total_before_category_filter": count,
                "search_unique_ids_before_category_filter": count, "original_api_query_status": "failed"}
                for key in ("robot_crosslist", "embodied_crosslist")}, "coverage_gaps": ["Provisional; API failed."]}


class ImportMonthlyArxivTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.input = self.root / "staging/author-complete-cohort.json"
        self.coverage_path = self.root / "staging/fallback-manifest.json"
        self.old = [{"arxiv_id": "2407.00001", "title": "User original", "do_not_touch": [False, None, {"x": "原文"}]}]
        self.write(self.root / "data/preprints.json", self.old)
        self.write(self.root / "config/source-registry.json", {"window": {"from": "2024-07-01", "until": "2026-08-31"},
                                                               "updated": "2026-08-31", "unrelated": {"preserve": True}})
        self.write(self.input, [record()])
        self.write(self.coverage_path, coverage())
        self.write(self.root / "staging/api.json", {"status": "failed", "complete_within_registered_query_scope": False,
            "corpus_count": None, "network_observed_records": 0, "queries": [{"query_id": "cs_ro", "status": "failed",
                "complete": False, "advertised_total": None, "observed_records": 0, "error_type": "HTTPError"}]})

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")

    def plan(self):
        return monthly.prepare(self.root, self.input, self.coverage_path, CUTOFF, now=NOW)

    def file_snapshot(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}

    def test_dry_run_never_creates_directories_or_changes_bytes(self):
        before = self.file_snapshot()
        directories = {str(p) for p in self.root.rglob("*") if p.is_dir()}
        plan = self.plan()
        self.assertEqual(plan["report"]["added_records"], 1)
        self.assertFalse(plan["report"]["applied"])
        self.assertEqual(self.file_snapshot(), before)
        self.assertEqual({str(p) for p in self.root.rglob("*") if p.is_dir()}, directories)
        self.assertEqual(len(plan["updates"]), 4)

    def test_cli_without_apply_only_prints_plan(self):
        before = self.file_snapshot()
        with patch.object(monthly, "ROOT", self.root), contextlib.redirect_stdout(io.StringIO()) as output:
            monthly.main(["--input", str(self.input), "--coverage", str(self.coverage_path), "--cutoff", "2026-09-14"])
        self.assertFalse(json.loads(output.getvalue())["applied"])
        self.assertEqual(self.file_snapshot(), before)

    def test_append_preserves_every_old_object_and_all_new_states(self):
        incoming = [record(f"2609.0000{i}", state) for i, state in enumerate(("included", "candidate", "manual_review", "excluded"), 1)]
        incoming[0]["metadata_history"] = [{"raw_abstract": "older exact text", "unrecognized": 17}]
        self.write(self.input, incoming)
        self.write(self.coverage_path, coverage(4))
        plan = self.plan()
        monthly.apply_plan(plan)  # Only this test's temporary fixture directory.
        actual = json.loads((self.root / "data/preprints.json").read_text())
        self.assertEqual(actual[:len(self.old)], self.old)
        self.assertEqual(actual[len(self.old):], incoming)
        registry = json.loads((self.root / "config/source-registry.json").read_text())
        self.assertEqual(registry["unrelated"], {"preserve": True})
        self.assertEqual(registry["window"]["until"], "2026-09-14")
        self.assertIn("analysis_cutoff", registry["window"]["until_basis"])
        self.assertEqual(registry["updated"], "2026-09-14")

    def test_identical_replay_is_byte_idempotent(self):
        monthly.apply_plan(self.plan())
        before = self.file_snapshot()
        replay = monthly.prepare(self.root, self.input, self.coverage_path, CUTOFF,
                                 now=datetime(2026, 9, 15, 12, tzinfo=timezone.utc))
        self.assertEqual(replay["report"]["added_records"], 0)
        self.assertEqual(replay["updates"], {})
        monthly.apply_plan(replay)
        self.assertEqual(self.file_snapshot(), before)

    def test_same_id_changed_payload_aborts_before_any_write(self):
        monthly.apply_plan(self.plan())
        changed = record()
        changed["custom_field"]["new_user_field"] = "do not overwrite"
        self.write(self.input, [changed])
        before = self.file_snapshot()
        with self.assertRaisesRegex(ValueError, "payload conflict"):
            self.plan()
        self.assertEqual(self.file_snapshot(), before)

    def test_duplicate_input_identical_allowed_conflicting_rejected(self):
        self.write(self.input, [record(), record()])
        self.assertEqual(self.plan()["report"]["added_records"], 1)
        changed = record()
        changed["abstract"] += " changed"
        self.write(self.input, [record(), changed])
        with self.assertRaisesRegex(ValueError, "payload conflict"):
            self.plan()

    def test_bad_identifiers_dates_empty_metadata_and_provenance_rejected(self):
        mutations = [lambda r: r.update(arxiv_id="2609.1"), lambda r: r.update(work_id="arxiv:2609.00002"),
                     lambda r: r.update(first_submitted="2026-08-31"), lambda r: r.update(first_submitted="2026-09-15"),
                     lambda r: r.update(first_submitted="2026-09-31"), lambda r: r.update(authors=[]),
                     lambda r: r.update(authors=[""]), lambda r: r.update(abstract=" "), lambda r: r.update(version="latest"),
                     lambda r: r.update(arxiv_version_id="2609.00001v7"), lambda r: r.update(source_observations=[]),
                     lambda r: r["source_observations"][0].update(raw_sha256="unknown"),
                     lambda r: r["source_observations"][0].update(source_url="file:///tmp/unknown")]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                row = record()
                mutate(row)
                with self.assertRaises(ValueError):
                    monthly.validate_record(row, CUTOFF)

    def test_author_truncation_guard(self):
        row = record()
        row["authors"] = [f"Author {i}" for i in range(25)]
        for flag in (None, False):
            row["authors_complete"] = flag
            with self.assertRaisesRegex(ValueError, "complete"):
                monthly.validate_record(row, CUTOFF)
        row["authors_complete"] = True
        monthly.validate_record(row, CUTOFF)

    def test_precision_cannot_invent_midnight_and_seconds_must_be_evidenced(self):
        row = record()
        row.update(submitted_at="2026-09-11T00:00:00Z")
        with self.assertRaises(ValueError):
            monthly.validate_record(row, CUTOFF)
        row["submitted_at_precision"] = "second"
        with self.assertRaisesRegex(ValueError, "day-only"):
            monthly.validate_record(row, CUTOFF)
        row.update(updated_at="2026-09-11T00:00:00Z", updated_at_precision="second",
                   metadata_temporal_basis="official_abstract_submission_history_UTC")
        monthly.validate_record(row, CUTOFF)  # Real midnight is not categorically banned.
        row["updated_at"] = "2026-09-10T23:59:59Z"
        with self.assertRaises(ValueError):
            monthly.validate_record(row, CUTOFF)

    def test_future_observation_and_version_dates_rejected(self):
        row = record()
        row["source_observations"][0]["fetched_at"] = "2026-09-10T23:59:59Z"
        with self.assertRaisesRegex(ValueError, "postdates"):
            monthly.validate_record(row, CUTOFF)
        row = record()
        row.update(version="v2", arxiv_version_id="2609.00001v2", updated_at="2026-09-15", updated="2026-09-15")
        with self.assertRaisesRegex(ValueError, "future"):
            monthly.validate_record(row, CUTOFF)

    def test_coverage_keeps_failure_unknown_counts_and_old_sources(self):
        old_source = {"source": "publications", "status": "failed", "complete": False, "expected_records": None,
                      "observed_records": None, "checked_at": "2026-09-01T10:00:00Z", "error_type": "HTTPError",
                      "custom_evidence": {"preserve": [1, 2]}}
        self.write(self.root / "data/weekly-v3/source-coverage.json", {"sources": [old_source], "custom_top": 9,
            "complete_through": "2026-08-31", "primary_corpora_complete_through": "2026-08-31"})
        monthly.apply_plan(self.plan())
        audit = json.loads((self.root / "data/collection-runs/2026-09-14/arxiv.json").read_text())
        self.assertTrue(audit["html_fallback"]["complete_for_observed_html_scope"])
        self.assertEqual(audit["api_collection"]["status"], "failed")
        self.assertIsNone(audit["api_collection"]["expected_records"])
        self.assertEqual(audit["last_observed_arxiv_v1_date"], "2026-09-11")
        self.assertEqual(audit["analysis_cutoff"], "2026-09-14")
        self.assertIsNone(audit["source_data_through"])
        weekly = json.loads((self.root / "data/weekly-v3/source-coverage.json").read_text())
        retained = next(row for row in weekly["sources"] if row["source"] == "publications")
        self.assertEqual(retained.pop("check_status_this_run"), "not_checked_this_run")
        self.assertFalse(retained.pop("rechecked_this_run"))
        self.assertEqual(retained, old_source)
        self.assertEqual(weekly["custom_top"], 9)
        self.assertEqual(weekly["complete_through"], "2026-08-31")
        self.assertEqual(weekly["available_data_through"], "2026-09-11")
        self.assertFalse(weekly["registered_scope_complete"])

    def test_missing_api_manifest_is_unknown_not_zero(self):
        (self.root / "staging/api.json").unlink()
        plan = self.plan()
        audit = json.loads(plan["updates"][self.root / "data/collection-runs/2026-09-14/arxiv.json"])
        self.assertEqual(audit["api_collection"]["status"], "failed")  # Explicit fallback checks report failure.
        self.assertIsNone(audit["api_collection"]["expected_records"])
        self.assertIsNone(audit["api_collection"]["observed_records"])

    def test_conflicting_or_incomplete_coverage_not_promoted(self):
        value = coverage()
        value["supplementary"]["robot_crosslist"]["search_unique_ids_before_category_filter"] = 0
        self.write(self.coverage_path, value)
        self.assertFalse(self.plan()["report"]["html_fallback_complete"])
        for key, changed in (("month", "2026-08"), ("records", 2), ("first_submission_day_max", "2026-09-12")):
            value = coverage()
            value[key] = changed
            self.write(self.coverage_path, value)
            with self.assertRaises(ValueError):
                self.plan()

    def test_no_cutoff_regression_or_manifest_path_escape(self):
        registry = json.loads((self.root / "config/source-registry.json").read_text())
        registry["window"]["until"] = "2026-09-20"
        self.write(self.root / "config/source-registry.json", registry)
        with self.assertRaisesRegex(ValueError, "regression"):
            self.plan()
        registry["window"]["until"] = "2026-08-31"
        self.write(self.root / "config/source-registry.json", registry)
        value = coverage()
        value["api_collection_manifest"] = "../private.json"
        self.write(self.coverage_path, value)
        with self.assertRaisesRegex(ValueError, "within coverage"):
            self.plan()

    def test_concurrent_change_prevents_all_writes(self):
        plan = self.plan()
        self.write(self.root / "data/preprints.json", self.old + [{"arxiv_id": "2407.00002", "user_edit": True}])
        before = self.file_snapshot()
        with self.assertRaisesRegex(RuntimeError, "concurrent"):
            monthly.apply_plan(plan)
        self.assertEqual(self.file_snapshot(), before)


if __name__ == "__main__":
    unittest.main()
