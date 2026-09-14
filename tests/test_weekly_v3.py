"""Weekly orchestration regression tests: no network or production mutations."""
import contextlib
import importlib.util
import io
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import tempfile
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


weekly = module("run_weekly_v3")
installer = module("install_weekly_launchd")
feishu = module("publish_group_weekly_to_feishu")


class WeeklyTests(unittest.TestCase):
    def test_same_week_metadata_only_keeps_revision_and_no_publish_change(self):
        now = datetime(2026, 9, 7, tzinfo=timezone.utc)
        context = weekly.week_context(now)
        checks = [{"source": name, "status": "ok", "complete": True, "checked_at": now.isoformat()} for name in weekly.EXPECTED_SOURCES]
        coverage = weekly.collection_coverage(checks, date(2026, 9, 6), "2026-08-31")
        state = {"works": [{"work_id": "a", "title": "A", "updated_at": now.isoformat(), "source_record_ids": ["old"]}], "editorial": {"claims": []}}
        previous, change = weekly.choose_snapshot({}, context, now, state, coverage, "data_only")
        self.assertEqual(previous["revision"], 1)
        state["works"][0].update(updated_at=(now + timedelta(hours=2)).isoformat())
        for row in coverage["sources"]:
            row["checked_at"] = (now + timedelta(hours=2)).isoformat()
        result, change = weekly.choose_snapshot(previous, context, now + timedelta(hours=2), state, coverage, "data_only")
        self.assertEqual(result, previous)
        self.assertEqual(change, {"research_changed": False, "coverage_changed": False, "publish_changed": False})

    def test_health_change_preserved_without_new_research_revision(self):
        now = datetime(2026, 9, 7, tzinfo=timezone.utc)
        context = weekly.week_context(now)
        checks = [{"source": name, "status": "ok", "complete": True} for name in weekly.EXPECTED_SOURCES]
        complete = weekly.collection_coverage(checks, date(2026, 9, 6), "2026-08-31")
        previous, _ = weekly.choose_snapshot({}, context, now, {"works": ["a"]}, complete, "data_only")
        checks[0].update(status="partial", complete=False)
        partial = weekly.collection_coverage(checks, date(2026, 9, 6), "2026-09-06", complete)
        snapshot, change = weekly.choose_snapshot(previous, context, now, {"works": ["a"]}, partial, "data_only")
        self.assertEqual(snapshot["revision"], 1)
        self.assertFalse(change["research_changed"])
        self.assertTrue(change["coverage_changed"])
        self.assertEqual(snapshot["collection_coverage"]["status"], "partial")

    def test_fallback_data_then_local_summary_updates_same_week(self):
        now = datetime(2026, 9, 7, tzinfo=timezone.utc)
        context = weekly.week_context(now)
        coverage = weekly.collection_coverage([], date(2026, 9, 6), "2026-08-31")
        first, _ = weekly.choose_snapshot({}, context, now, {"works": ["a"], "claims": []}, coverage, "data_only")
        later, change = weekly.choose_snapshot(first, context, now + timedelta(hours=4), {"works": ["a"], "claims": [{"statement": "Verified summary", "work_ids": ["a"]}]}, coverage, "llm_complete")
        self.assertEqual(later["week"], first["week"])
        self.assertEqual(later["revision"], 2)
        self.assertTrue(change["research_changed"])
        again, change = weekly.choose_snapshot(later, context, now + timedelta(hours=5), {"works": ["a"], "claims": [{"statement": "Verified summary", "work_ids": ["a"]}]}, coverage, "llm_complete")
        self.assertEqual(again, later)
        self.assertFalse(change["publish_changed"])

    def test_retained_stale_editorial_is_not_current_llm_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            monthly = root / "docs/public/api/v1/monthly"
            monthly.mkdir(parents=True)
            (monthly / "2026-08.json").write_text(json.dumps({"month": "2026-08", "editorial_status": "data_only"}))
            (monthly / "2026-09.json").write_text(json.dumps({"month": "2026-09", "editorial_status": "legacy_editorial"}))
            manifest = {"complete_months": ["2026-08"], "provisional_month": "2026-09"}
            stale = {"months": [{"month": "2026-08", "status": "complete", "previous_complete_preserved": True},
                                {"month": "2026-09", "status": "data_only", "previous_complete_preserved": True}]}
            with patch.object(weekly, "ROOT", root):
                result = weekly.published_editorial_completion(manifest, stale)
            self.assertEqual(result["summary_mode"], "data_only")
            self.assertEqual(result["current_completed_months"], [])
            self.assertEqual(result["historical_retained_months"], ["2026-08", "2026-09"])

    def test_only_final_current_month_statuses_determine_summary_completion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            monthly = root / "docs/public/api/v1/monthly"
            monthly.mkdir(parents=True)
            (monthly / "2026-08.json").write_text(json.dumps({"month": "2026-08", "editorial_status": "llm_complete"}))
            manifest = {"complete_months": ["2026-08"], "provisional_month": "2026-09"}
            with patch.object(weekly, "ROOT", root):
                partial = weekly.published_editorial_completion(manifest)
                self.assertEqual(partial["summary_mode"], "llm_partial")
                self.assertEqual(partial["current_month_statuses"]["2026-09"], "missing")
                (monthly / "2026-09.json").write_text(json.dumps({"month": "2026-09", "editorial_status": "llm_complete"}))
                complete = weekly.published_editorial_completion(manifest, {"months": [{"month": "2026-08", "status": "data_only"}]})
                self.assertEqual(complete["summary_mode"], "llm_complete")
                self.assertEqual(complete["current_completed_months"], ["2026-08", "2026-09"])
                self.assertEqual(weekly.published_editorial_completion({})["summary_mode"], "data_only")

    def test_partial_never_claims_full_cutoff_and_retains_usable_rows(self):
        checks = [{"source": "arxiv", "status": "partial", "complete": False, "last_observed_data_through": "2026-09-03"},
                  {"source": "publications", "status": "failed", "complete": False}]
        coverage = weekly.collection_coverage(checks, date(2026, 9, 6), "2026-08-31")
        self.assertEqual(coverage["available_data_through"], "2026-09-03")
        self.assertIsNone(coverage["complete_through"])
        self.assertIsNone(coverage["primary_corpora_complete_through"])
        self.assertFalse(coverage["registered_scope_complete"])
        self.assertEqual(coverage["incomplete_sources"], list(weekly.EXPECTED_SOURCES))

    def test_one_complete_corpus_does_not_mean_all_sources_complete(self):
        checks = [{"source": "arxiv", "status": "ok", "complete": True}, {"source": "publications", "status": "partial", "complete": False}]
        coverage = weekly.collection_coverage(checks, date(2026, 9, 6), "2026-08-31", {"complete_through": "2026-08-24"})
        self.assertEqual(coverage["available_data_through"], "2026-09-06")
        self.assertEqual(coverage["complete_through"], "2026-08-24")
        self.assertFalse(coverage["primary_corpora_complete"])

    def test_historical_recheck_does_not_regress_verified_coverage(self):
        checks = [{"source": name, "status": "ok", "complete": True} for name in weekly.EXPECTED_SOURCES]
        coverage = weekly.collection_coverage(checks, date(2026, 8, 31), "2026-09-06", {"complete_through": "2026-09-06", "primary_corpora_complete_through": "2026-09-06"})
        self.assertEqual(coverage["complete_through"], "2026-09-06")
        self.assertEqual(coverage["available_data_through"], "2026-09-06")

    def test_partial_arxiv_page_preserves_completed_pages_and_other_queries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = lambda identifier: {"arxiv_id": identifier, "title": identifier, "first_submitted": "2026-08-10"}
            def fetch(query, _text, _month, offset, _size):
                if query == "bad" and offset:
                    raise TimeoutError("sensitive error details must not be stored")
                return (2, [record("a")]) if query == "bad" else (1, [record("b")])
            collector = SimpleNamespace(REGISTRY={"window": {}, "arxiv_sources": {"queries": [{"id": "bad", "query": "x"}, {"id": "good", "query": "y"}]}}, RAW=root / "raw", OUTPUT=root / "rows.json", COVERAGE=root / "coverage.json", fetch=fetch, parse_feed=lambda body: body, merge_record=lambda old, row, query: row, classify=lambda rows: None, summarize=lambda rows: {"count": len(rows)})
            collector.OUTPUT.write_text(json.dumps([record("old")]))
            with patch.object(weekly.importlib, "import_module", return_value=collector), patch.object(weekly, "collection_months", return_value=["2026-08"]):
                result = weekly.collect_arxiv(date(2026, 8, 31), datetime(2026, 9, 7, tzinfo=timezone.utc))
            self.assertEqual(result["status"], "partial")
            self.assertFalse(result["complete"])
            self.assertIsNone(result["source_data_through"])
            self.assertEqual({r["arxiv_id"] for r in json.loads(collector.OUTPUT.read_text())}, {"a", "b", "old"})
            self.assertEqual(result["checks"][0]["error_type"], "TimeoutError")
            self.assertNotIn("sensitive", json.dumps(result))
            self.assertTrue(result["checks"][1]["complete"])

    def test_incomplete_publication_cache_is_not_complete_success(self):
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory)
            (raw / "dblp-test-2026.json").write_text(json.dumps({"hits": [1, 2], "expected_total": 3, "complete": False}))
            collector = SimpleNamespace(RAW=raw)
            rows = weekly._publication_pages(collector, {"venue": "TEST", "dblp_stream": "streams/test", "years": [2026]}, date(2026, 8, 31))
            self.assertEqual(rows[0]["status"], "partial")
            self.assertFalse(rows[0]["complete"])
            self.assertEqual(rows[0]["requested_window"], {"year": 2026, "basis": "dblp_venue_year_index"})

    def test_successful_process_with_blocked_corl_status_is_not_success(self):
        now = datetime(2026, 9, 7, tzinfo=timezone.utc)
        raw = {"status": "access_blocked", "complete": False, "checked_at": "2026-09-07T00:00:01Z", "expected_count": None, "fetched_count": 0}
        with patch.object(weekly, "read_json", return_value=raw):
            result = weekly.read_collector_check("corl", now)
        self.assertFalse(result["complete"])
        self.assertIsNone(result["expected_records"])
        self.assertEqual(result["source_status"], "access_blocked")

    def test_old_healthy_group_status_is_not_a_current_check(self):
        now = datetime(2026, 9, 7, tzinfo=timezone.utc)
        raw = {"sources": [{"source_id": "x", "status": "healthy", "last_checked": "2026-09-06T00:00:00Z"}]}
        with patch.object(weekly, "read_json", return_value=raw):
            result = weekly.read_collector_check("official_groups", now)
        self.assertFalse(result["complete"])
        self.assertEqual(result["checks"][0]["status"], "not_checked_this_run")

    def test_registered_group_source_missing_status_stays_in_denominator(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / "data/catalog"
            catalog.mkdir(parents=True)
            (catalog / "organizations.jsonl").write_text(json.dumps({"organization_id": "org:lab", "tier": "T0", "official_urls": {"publications": "https://example.test/papers"}}) + "\n")
            with patch.object(weekly, "ROOT", root):
                result = weekly.read_collector_check("official_groups", datetime(2026, 9, 7, tzinfo=timezone.utc))
            self.assertEqual(result["expected_checks"], 1)
            self.assertFalse(result["complete"])
            self.assertEqual(result["checks"][0]["status"], "not_checked_this_run")

    def test_exact_checkpoint_does_not_touch_unknown_or_review_files(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as backup:
            root = Path(directory)
            old = root / "generated.json"
            old.write_text("old")
            with patch.object(weekly, "ROOT", root):
                checkpoint = weekly.checkpoint_generated(["generated.json", "known-new.json"], Path(backup))
                old.write_text("new metadata")
                (root / "known-new.json").write_text("generated")
                (root / "unknown.json").write_text("user data")
                (root / "review-additions.jsonl").write_text("manual review")
                weekly.restore_generated(checkpoint, weekly.generated_hashes(checkpoint))
            self.assertEqual(old.read_text(), "old")
            self.assertFalse((root / "known-new.json").exists())
            self.assertEqual((root / "unknown.json").read_text(), "user data")
            self.assertEqual((root / "review-additions.jsonl").read_text(), "manual review")

    def test_checkpoint_rejects_concurrent_changes(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as backup:
            root = Path(directory)
            (root / "generated.json").write_text("old")
            with patch.object(weekly, "ROOT", root):
                checkpoint = weekly.checkpoint_generated(["generated.json"], Path(backup))
                expected = weekly.generated_hashes(checkpoint)
                (root / "generated.json").write_text("concurrent user edit")
                with self.assertRaises(RuntimeError):
                    weekly.restore_generated(checkpoint, expected)
            self.assertEqual((root / "generated.json").read_text(), "concurrent user edit")

    def test_monthly_checkpoint_uses_real_monthly_path_and_preserves_unknown_month(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as backup:
            root = Path(directory)
            api = root / "docs/public/api/v1/catalog-manifest.json"
            api.parent.mkdir(parents=True)
            api.write_text(json.dumps({"available_months": ["2026-08"], "complete_months": ["2026-08"]}))
            folder = root / "data/snapshots/monthly/2026-08"
            folder.mkdir(parents=True)
            (folder / "history.json").write_text(json.dumps([{"revision": 1}]))
            (folder / "r1.json").write_text("original snapshot")
            context = {"week": "2026-W36"}
            with patch.object(weekly, "ROOT", root):
                paths = weekly.planned_generated_paths(context)
                self.assertIn("data/snapshots/monthly/2026-08/r2.json", paths)
                self.assertNotIn("data/snapshots/2026-08/r2.json", paths)
                self.assertNotIn("data/editorial/signal-evidence.jsonl", paths)
                self.assertFalse(any("config/" in path or "additions" in path for path in paths))
                checkpoint = weekly.checkpoint_generated(paths, Path(backup))
                (folder / "history.json").write_text(json.dumps([{"revision": 1}, {"revision": 2}]))
                (folder / "r2.json").write_text("metadata-only generated snapshot")
                unknown = root / "data/snapshots/monthly/2026-09/r1.json"
                unknown.parent.mkdir(parents=True)
                unknown.write_text("new month not in original output manifest")
                weekly.restore_generated(checkpoint, weekly.generated_hashes(checkpoint))
            self.assertEqual(json.loads((folder / "history.json").read_text()), [{"revision": 1}])
            self.assertFalse((folder / "r2.json").exists())
            self.assertTrue(unknown.exists())

    def test_first_discovery_revision_is_not_timestamp_noise(self):
        first = {"work_id": "a", "first_seen_at": "2026-08-30T23:00:00Z"}
        revised = {**first, "first_seen_at": "2026-08-29T23:00:00Z"}
        self.assertNotEqual(weekly.content_hash(first), weekly.content_hash(revised))
        self.assertNotEqual(weekly.content_hash({"authors": ["First", "Second"]}), weekly.content_hash({"authors": ["Second", "First"]}))

    def test_calendar_rollover_is_a_content_revision(self):
        now = datetime(2026, 9, 7, tzinfo=timezone.utc)
        context = weekly.week_context(now)
        coverage = weekly.collection_coverage([], date(2026, 9, 6), "2026-08-31")
        old = {"works": ["a"], "calendar": {"complete_months": ["2026-07"], "provisional_month": "2026-08"}}
        new = {"works": ["a"], "calendar": {"complete_months": ["2026-08"], "provisional_month": "2026-09"}}
        previous, _ = weekly.choose_snapshot({}, context, now, old, coverage, "data_only")
        current, change = weekly.choose_snapshot(previous, context, now, new, coverage, "data_only")
        self.assertEqual(current["revision"], 2)
        self.assertTrue(change["research_changed"])

    def test_unknown_public_date_keeps_event_first_observation_in_research_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / "data/catalog"
            folder.mkdir(parents=True)
            path = folder / "evidence-events.jsonl"
            event = {"event_id": "demo", "work_id": "a", "event_type": "company_demo", "published_at": None, "date_precision": "unknown", "observed_at": "2026-08-30T12:00:00Z"}
            path.write_text(json.dumps(event) + "\n")
            with patch.object(weekly, "ROOT", root):
                first = weekly.research_state()
                event["observed_at"] = "2026-08-29T12:00:00Z"
                path.write_text(json.dumps(event) + "\n")
                second = weekly.research_state()
            self.assertNotEqual(weekly.content_hash(first), weekly.content_hash(second))

    def test_digest_time_is_stable_and_s_lane_remains_observation(self):
        event = {"event_id": "s", "work_id": "a", "title": "Deployment update", "url": "https://example.test/work", "event_type": "technical_report", "evidence_layer": "S", "published_at": "2026-08-31", "date_precision": "day"}
        context = {"week": "2026-W36", "from": "2026-08-31", "until": "2026-09-06"}
        with patch.object(weekly, "read_json", return_value=[{"organization_id": "a", "name": "Alpha", "updates": [event]}]):
            first = weekly.weekly_digest(context, datetime(2026, 9, 7, tzinfo=timezone.utc), write=False)
            second = weekly.weekly_digest(context, datetime(2026, 9, 8, tzinfo=timezone.utc), write=False)
        self.assertEqual(first, second)
        self.assertIn("0 项研究发布与 1 项战略观察", first)

    def test_publish_noop_records_run_audit_without_commit_or_push(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            now = datetime.now(timezone.utc)
            context = weekly.week_context(now)
            cutoff = now.astimezone(weekly.SHANGHAI).date() - timedelta(days=1)
            checks = [{"source": name, "status": "ok", "complete": True} for name in weekly.EXPECTED_SOURCES]
            coverage = weekly.collection_coverage(checks, cutoff, cutoff.isoformat())
            weekly.write_json(root / "data/weekly-v3/source-coverage.json", coverage)
            previous, _ = weekly.choose_snapshot({}, context, now, {"works": ["same"]}, coverage, "data_only")
            snapshot = root / "data/weekly-v3" / (context["week"] + ".json")
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            snapshot.write_text(json.dumps(previous))
            manifest = root / "data/catalog/manifest.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({"data_through": cutoff.isoformat()}))
            with patch.object(weekly, "ROOT", root), patch.object(weekly, "git", side_effect=["main", "", str(root / "lock"), ""]), patch.object(weekly, "_status_git_changes", return_value=set()), patch.object(weekly, "run") as run, patch.object(weekly, "collect_sources", return_value=checks), patch.object(weekly, "research_state", return_value={"works": ["same"]}), patch.object(weekly, "weekly_digest"), contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(weekly.main(["--publish", "--data-only"]), 0)
            commands = [call.args[0] for call in run.call_args_list]
            self.assertFalse(any(command[:2] in [["git", "add"], ["git", "commit"], ["git", "push"]] for command in commands))
            self.assertEqual(json.loads(snapshot.read_text()), previous)
            audits = list((root / "logs/weekly-v3/runs").glob("*.json"))
            self.assertEqual(len(audits), 1)
            self.assertEqual(json.loads(audits[0].read_text())["source_checks"], checks)
            self.assertIn('"committed": false', output.getvalue())

    def test_organizational_observation_does_not_disappear_for_lack_of_research_work(self):
        org = {"organization_id": "org:lab", "name": "Lab", "updates": []}
        hiring = {"event_id": "hiring", "organization_id": "org:lab", "work_id": None, "event_type": "hiring_signal", "attribution_grade": "G3", "title": "Official hiring page changed", "url": "https://example.edu/jobs", "published_at": None, "date_precision": "unknown", "observed_at": "2026-08-31T12:00:00Z"}
        with patch.object(weekly, "read_json", side_effect=[[org], [hiring]]):
            result = weekly.weekly_digest({"week": "2026-W36", "from": "2026-08-31", "until": "2026-09-06"}, datetime(2026, 9, 7, tzinfo=timezone.utc), write=False)
        self.assertIn("0 项研究发布与 1 项战略观察", result)
        self.assertIn("首次观测日期（发布日期待核验）", result)
        self.assertIn("本周无可升级信号", result)

    def test_digest_uses_shanghai_week_deduplicates_work_and_counts_all_groups(self):
        event = {"event_id": "joint", "work_id": "w", "title": "A result", "url": "https://example.test/work", "event_type": "technical_report", "published_at": "2026-08-30T16:10:00Z", "date_precision": "day"}
        old = {**event, "event_id": "old", "work_id": "old", "published_at": "2026-08-30T15:59:00Z"}
        groups = [{"organization_id": "a", "name": "Alpha", "updates": [event, old]}, {"organization_id": "b", "name": "Beta", "updates": [event]}]
        with patch.object(weekly, "read_json", return_value=groups):
            text = weekly.weekly_digest({"week": "2026-W36", "from": "2026-08-31", "until": "2026-09-06"}, datetime(2026, 9, 7, tzinfo=timezone.utc), write=False)
        self.assertIn("1 项研究发布", text)
        self.assertIn("2 个组织", text)
        self.assertIn("Alpha × Beta", text)
        self.assertIn("2026-08-31", text)
        self.assertNotIn("2026-08-30T", text)

    def test_digest_does_not_execute_metadata_or_guess_month_only_week(self):
        event = {"event_id": "unsafe", "work_id": "w", "title": "<script>alert(1)</script>", "summary_zh": "<img src=x onerror=evil()>", "url": "javascript:alert(1)", "event_type": "technical_report", "published_at": "2026-08-31", "date_precision": "day"}
        imprecise = {**event, "event_id": "month", "work_id": "month", "date_precision": "month"}
        with patch.object(weekly, "read_json", return_value=[{"organization_id": "a", "name": "Alpha", "updates": [event, imprecise]}]):
            text = weekly.weekly_digest({"week": "2026-W36", "from": "2026-08-31", "until": "2026-09-06"}, datetime(2026, 9, 7, tzinfo=timezone.utc), write=False)
        self.assertIn("1 项研究发布", text)
        self.assertNotIn("<script>", text)
        self.assertNotIn("<img", text)
        self.assertNotIn("javascript:", text)
        self.assertIn("来源链接待核验", text)

    def test_shanghai_monday_covers_previous_week_across_iso_year(self):
        value = weekly.week_context(datetime(2026, 1, 4, 16, tzinfo=timezone.utc))
        self.assertEqual(value["week"], "2026-W01")
        self.assertEqual(value["from"], "2025-12-29")
        self.assertEqual(value["until"], "2026-01-04")
        self.assertEqual(value["until_exclusive_utc"], "2026-01-04T16:00:00+00:00")

    def test_dry_run_never_collects_locks_or_writes(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(weekly, "ROOT", Path(directory)), patch.object(weekly, "git", side_effect=["feature", " M README.md"]), patch.object(weekly, "collect_sources") as collect, patch.object(weekly, "run") as run, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(weekly.main(["--dry-run"]), 0)
            self.assertFalse(json.loads(output.getvalue())["can_publish"])
            self.assertEqual(list(Path(directory).iterdir()), [])
            collect.assert_not_called()
            run.assert_not_called()

    def test_publish_refuses_dirty_or_non_main_before_external_actions(self):
        for branch, changes in [("feature", ""), ("main", " M README.md")]:
            with tempfile.TemporaryDirectory() as directory, patch.object(weekly, "ROOT", Path(directory)), patch.object(weekly, "git", side_effect=[branch, changes]), patch.object(weekly, "run") as run:
                with self.assertRaises(SystemExit): weekly.main(["--publish"])
                run.assert_not_called()

    def test_incremental_merge_preserves_missing_old_enrichment(self):
        rows = weekly.merge_records([{"id": "a", "abstract": "old", "title": "Before"}, {"id": "b", "title": "Keep"}], [{"id": "a", "title": "After", "abstract": ""}], "id")
        self.assertEqual(rows, [{"id": "a", "abstract": "old", "title": "After"}, {"id": "b", "title": "Keep"}])

    def test_fallback_rechecks_snapshot_after_pull_and_skips_collectors(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context = weekly.week_context(datetime.now(timezone.utc))
            snapshot = root / "data/weekly-v3" / (context["week"] + ".json")
            snapshot.parent.mkdir(parents=True)
            snapshot.write_text(json.dumps({"verified": True, "week": context["week"]}))
            with patch.object(weekly, "ROOT", root), patch.object(weekly, "git", side_effect=["main", "", str(root / "lock")]), patch.object(weekly, "run") as run, patch.object(weekly, "collect_sources") as collect, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(weekly.main(["--publish", "--fallback", "--data-only"]), 0)
                collect.assert_not_called()
                run.assert_called_once_with(["git", "pull", "--ff-only", "origin", "main"])

    def test_launchd_schedule_contains_no_secret_values(self):
        value = installer.build_plist(Path("/work/radar"), "/python", "/node", "/npm", Path("/private/runtime.env"))
        self.assertEqual(value["StartCalendarInterval"], {"Weekday": 1, "Hour": 0, "Minute": 0})
        self.assertNotIn("LLM_API_KEY", value["EnvironmentVariables"])
        self.assertFalse(value["RunAtLoad"])


class FeishuTests(unittest.TestCase):
    def test_content_failure_resumes_created_document_without_duplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            page = root / "docs/groups/weekly/2026-w35.md"
            page.parent.mkdir(parents=True)
            page.write_text("# Week\n\nOne finding.")
            deliveries = root / "data/deliveries.json"
            environment = {key: "fixture" for key in ["FEISHU_APP_ID", "FEISHU_APP_SECRET", "FEISHU_FOLDER_TOKEN", "FEISHU_INDEX_DOC_TOKEN"]}
            with patch.object(feishu, "ROOT", root), patch.object(feishu, "RADAR", root / "missing.json"), patch.object(feishu, "DELIVERIES", deliveries), patch.dict(feishu.os.environ, environment), patch.object(feishu.sys, "argv", ["publish", "--week", "2026-W35"]), patch.object(feishu, "tenant_token", return_value="fixture"), patch.object(feishu, "create_document", return_value=("doc-fixture", "https://example.test/doc")) as create, patch.object(feishu, "replace_document_blocks", side_effect=[RuntimeError("fixture failure"), None, None]), patch.object(feishu, "upsert_index", return_value="index-block") as append, contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit): feishu.main()
                self.assertEqual(json.loads(deliveries.read_text())["deliveries"][0]["document_id"], "doc-fixture")
                feishu.main()
                feishu.main()
                self.assertEqual(create.call_count, 1)
                self.assertEqual(append.call_count, 1)
                self.assertEqual(json.loads(deliveries.read_text())["deliveries"][0]["status"], "published")

    def test_ambiguous_creation_is_queued_without_blind_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            page = root / "docs/groups/weekly/2026-w35.md"
            page.parent.mkdir(parents=True)
            page.write_text("# Week\n\nOne finding.")
            deliveries = root / "deliveries.json"
            deliveries.write_text(json.dumps({"deliveries": [{"week": "2026-W35", "delivery_stage": "creating", "status": "queued"}]}))
            environment = {key: "fixture" for key in ["FEISHU_APP_ID", "FEISHU_APP_SECRET", "FEISHU_FOLDER_TOKEN", "FEISHU_INDEX_DOC_TOKEN"]}
            with patch.object(feishu, "ROOT", root), patch.object(feishu, "RADAR", root / "missing.json"), patch.object(feishu, "DELIVERIES", deliveries), patch.dict(feishu.os.environ, environment), patch.object(feishu.sys, "argv", ["publish", "--week", "2026-W35"]), patch.object(feishu, "create_document") as create:
                with self.assertRaises(SystemExit): feishu.main()
                create.assert_not_called()


if __name__ == "__main__":
    unittest.main()
