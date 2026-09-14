"""Weekly status integration uses temporary authority and injected fetchers only."""
from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from test_weekly_v3 import weekly
from test_research_status_watch import A, B, work, metadata, notice, known_notice
from research_status_watch import _metadata

NOW = datetime(2026, 9, 7, 0, 0, tzinfo=timezone.utc)
CUTOFF = date(2026, 9, 6)


def write(root, relative, value, *, lines=False):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in value) if lines else json.dumps(value, ensure_ascii=False))
    return path


class WeeklyStatusTests(unittest.TestCase):
    def test_baseline_allows_comment_clear_and_keeps_pending_without_downgrade(self):
        raw = [metadata(A, comment="Withdrawn by authors.")]
        updates = [{**metadata(A, comment=""), "status_check_pending": True}]
        before = copy.deepcopy((raw, updates))
        merged = weekly.research_status_baseline(raw, updates)
        self.assertEqual(merged[0]["comment_sha256"], _metadata(metadata(A, comment=""))["comment_sha256"])
        self.assertFalse(merged[0]["status_comment_hint"])
        self.assertTrue(merged[0]["status_check_pending"])
        self.assertEqual((raw, updates), before)
        raw[0] = metadata(A, version="v3", comment="Current metadata")
        newer = weekly.research_status_baseline(raw, [{**updates[0], "status_check_pending": False}])[0]
        self.assertEqual(newer["latest_version"], "v3")
        self.assertTrue(newer["status_check_pending"], "Newer collection is not a successful status-check receipt")
        cleared = [{**metadata(A, version="v3"), "status_check_pending": False}]
        self.assertFalse(weekly.research_status_baseline([], [*merged, *cleared])[0]["status_check_pending"])

    def test_preprints_without_watch_receipt_still_require_first_status_check(self):
        row = weekly.research_status_baseline([metadata(A)], [])[0]
        self.assertTrue(row["status_check_pending"])

    def test_arxiv_update_then_status_metadata_failure_is_retried_next_run(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write(root, "data/catalog/works.jsonl", [work(A)], lines=True)
            preprints = write(root, "data/preprints.json", [metadata(A, version="v1")])
            write(root, "data/weekly-v3/research-status/baseline.json", {"metadata_updates": [{**metadata(A, version="v1"), "status_check_pending": False}]})
            def arxiv(*_):
                preprints.write_text(json.dumps([metadata(A, version="v2")]))
                return {"status": "ok", "complete": True}
            def fail(_):
                raise OSError("metadata unavailable")
            pages = []
            with patch.object(weekly, "ROOT", root), patch.object(weekly, "collect_arxiv", side_effect=arxiv), patch.object(weekly, "collect_publications", return_value={"status": "ok", "complete": True}), patch.object(weekly, "run"), patch.object(weekly, "read_collector_check", side_effect=lambda name, now: {"source": name, "complete": True, "status": "ok"}):
                weekly.collect_sources(CUTOFF, NOW, status_metadata_fetcher=fail, status_fetcher=lambda *_: self.fail("No metadata yet"), status_sleeper=lambda _: None)
                weekly.collect_sources(CUTOFF, NOW + timedelta(hours=1), status_metadata_fetcher=lambda _: [metadata(A, version="v2")], status_fetcher=lambda url, *_: pages.append(url), status_sleeper=lambda _: None)
            self.assertEqual(pages, [f"https://arxiv.org/abs/{A}v2"])

    def test_arxiv_runs_first_but_status_compares_precollection_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write(root, "data/catalog/works.jsonl", [work(A)], lines=True)
            preprints = write(root, "data/preprints.json", [metadata(A, version="v1", comment="Old metadata")])
            order = []
            def arxiv(*_):
                order.append("arxiv")
                preprints.write_text(json.dumps([metadata(A)]))
                return {"status": "ok", "complete": True}
            def status(*_):
                order.append("status")
                return None
            def publications(*_):
                order.append("publications")
                return {"status": "ok", "complete": True}
            with patch.object(weekly, "ROOT", root), patch.object(weekly, "collect_arxiv", side_effect=arxiv), patch.object(weekly, "collect_publications", side_effect=publications), patch.object(weekly, "run"), patch.object(weekly, "read_collector_check", side_effect=lambda name, now: {"source": name, "complete": True, "status": "ok"}):
                checks = weekly.collect_sources(CUTOFF, NOW, status_metadata_fetcher=lambda _: [metadata(A)], status_fetcher=status, status_sleeper=lambda _: None)
            self.assertEqual(order, ["arxiv", "status", "publications"])
            status_check = next(row for row in checks if row["source"] == "arxiv_research_status")
            paths = list(status_check["_status_audit_hashes"])
            observations = next(root / path for path in paths if path.endswith("observations.jsonl"))
            rows = [json.loads(line) for line in observations.read_text().splitlines()]
            self.assertIn("latest_version_changed", rows[0]["reasons"])
            self.assertIsNone(status_check["source_data_through"])

    def test_authority_manual_notice_is_not_reimported_and_each_observation_is_saved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = notice(source_id="source:manual")
            original["notice_id"] = "notice:manual-athena"
            saved = {key: copy.deepcopy(value) for key, value in original.items() if key != "source_record"}
            source_work = work(A, research_status_notices=[saved], source_record_ids=["source:manual"])
            authority = write(root, "data/catalog/works.jsonl", [source_work], lines=True)
            stage = write(root, "data/research-status-additions.jsonl", [original], lines=True)
            original_bytes, authority_bytes = stage.read_bytes(), authority.read_bytes()
            with patch.object(weekly, "ROOT", root):
                first = weekly.collect_research_status(CUTOFF, NOW, [metadata(A)], metadata_fetcher=lambda _: [metadata(A)],
                                                       status_fetcher=lambda url, wid, when: notice(observed_at=when, source_id="source:new-observation"), sleeper=lambda _: None)
                second = weekly.collect_research_status(CUTOFF, NOW + timedelta(hours=1), [metadata(A)], metadata_fetcher=lambda _: [metadata(A)],
                                                        status_fetcher=lambda url, wid, when: notice(observed_at=when, source_id="source:another-observation"), sleeper=lambda _: None)
            self.assertEqual(stage.read_bytes(), original_bytes)
            self.assertEqual(authority.read_bytes(), authority_bytes)
            self.assertEqual(first["notice_candidates_staged"], 0)
            self.assertEqual(second["notice_candidates_staged"], 0)
            snapshot = json.loads((root / first["report_path"]).read_text())
            self.assertEqual(len(snapshot["run_ids"]), 2)
            observations = [json.loads(line) for path in (root / "data/weekly-v3/research-status").rglob("observations.jsonl") for line in path.read_text().splitlines()]
            pages = [row for row in observations if row["kind"] == "version_status"]
            self.assertEqual(len(pages), 2)
            self.assertTrue(all(row["notice_id"] == "notice:manual-athena" for row in pages))
            self.assertEqual({row["observed_source_record"]["source_record_id"] for row in pages}, {"source:new-observation", "source:another-observation"})

    def test_new_notice_stages_for_existing_ingest_without_changing_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            authority = write(root, "data/catalog/works.jsonl", [work(A)], lines=True)
            before = authority.read_bytes()
            with patch.object(weekly, "ROOT", root):
                checked = weekly.collect_research_status(CUTOFF, NOW, [], metadata_fetcher=lambda _: [metadata(A)],
                                                         status_fetcher=lambda url, wid, when: notice(observed_at=when), sleeper=lambda _: None)
            self.assertEqual(checked["notice_candidates_staged"], 1)
            rows = [json.loads(line) for line in (root / "data/research-status-additions.jsonl").read_text().splitlines()]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["event_type"], "withdrawn")
            self.assertEqual(authority.read_bytes(), before)
            self.assertIn("data/research-status-additions.jsonl", weekly.STAGED_PATHS)

    def test_same_version_staging_notice_keeps_first_source_and_conflicts_go_to_review(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write(root, "data/catalog/works.jsonl", [work(A)], lines=True)
            original = notice(source_id="source:first")
            original["notice_id"] = "notice:manual"
            path = write(root, "data/research-status-additions.jsonl", [original], lines=True)
            before = path.read_bytes()
            with patch.object(weekly, "ROOT", root):
                same = weekly.collect_research_status(CUTOFF, NOW, [], metadata_fetcher=lambda _: [metadata(A)], status_fetcher=lambda *_: notice(), sleeper=lambda _: None)
                conflict = weekly.collect_research_status(CUTOFF, NOW + timedelta(hours=1), [], metadata_fetcher=lambda _: [metadata(A)],
                                                          status_fetcher=lambda *_: notice(public_at="2026-08-25T00:00:00Z"), sleeper=lambda _: None)
            self.assertEqual(same["notice_candidates_staged"], 0)
            self.assertEqual(conflict["notice_candidates_staged"], 0)
            self.assertFalse(conflict["complete"])
            self.assertEqual(path.read_bytes(), before)
            queues = [json.loads(p.read_text()) for p in (root / "data/weekly-v3/research-status").rglob("review-queue.json")]
            self.assertTrue(any(row["error_code"] == "status_staging_identity_state_or_date_conflict" for rows in queues for row in rows))

    def test_same_notice_id_cannot_silently_rewrite_its_description(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = notice()
            path = write(root, "data/research-status-additions.jsonl", [original], lines=True)
            before = path.read_bytes()
            changed = copy.deepcopy(original)
            changed["summary_zh"] = "同一通知ID下改写的说明。"
            with patch.object(weekly, "ROOT", root):
                accepted, reviews = weekly._stage_status_candidates([changed], [work(A)])
            self.assertEqual(accepted, [])
            self.assertEqual(len(reviews), 1)
            self.assertEqual(path.read_bytes(), before)

    def test_missing_status_ids_failures_are_explicit_but_do_not_advance_corpus_cutoff(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write(root, "data/catalog/works.jsonl", [work(A), work(B)], lines=True)
            with patch.object(weekly, "ROOT", root):
                first = weekly.collect_research_status(CUTOFF, NOW, [], metadata_fetcher=lambda _: [metadata(A)], status_fetcher=lambda *_: None, sleeper=lambda _: None)
                second = weekly.collect_research_status(CUTOFF, NOW + timedelta(hours=1), [], metadata_fetcher=lambda _: [metadata(A)], status_fetcher=lambda *_: None, sleeper=lambda _: None)
                recovered = weekly.collect_research_status(CUTOFF, NOW + timedelta(hours=2), [], metadata_fetcher=lambda ids: [metadata(base) for base in ids], status_fetcher=lambda *_: None, sleeper=lambda _: None)
            self.assertEqual((first["missing_records"], second["consecutive_failures"], recovered["consecutive_failures"]), (1, 2, 0))
            self.assertTrue(recovered["complete"])
            primary_failed = [{"source": "arxiv", "status": "failed", "complete": False}, {"source": "publications", "status": "failed", "complete": False}, recovered]
            coverage = weekly.collection_coverage(primary_failed, CUTOFF, "2026-08-31")
            self.assertEqual(coverage["available_data_through"], "2026-08-31")
            self.assertNotIn("_status_audit_hashes", json.dumps(coverage))
            healthy = [{"source": name, "status": "ok", "complete": True} for name in weekly.EXPECTED_SOURCES if name != "arxiv_research_status"]
            incomplete = weekly.collection_coverage([*healthy, second], CUTOFF, "2026-08-31")
            self.assertTrue(incomplete["primary_corpora_complete"])
            self.assertFalse(incomplete["registered_scope_complete"])
            self.assertIsNone(incomplete["complete_through"])

    def test_status_network_failure_does_not_stop_other_collectors(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write(root, "data/catalog/works.jsonl", [work(A)], lines=True)
            def fail(_):
                raise OSError("private details must not leak")
            with patch.object(weekly, "ROOT", root), patch.object(weekly, "collect_arxiv", return_value={"status": "ok", "complete": True}), patch.object(weekly, "collect_publications", return_value={"status": "ok", "complete": True}) as publications, patch.object(weekly, "run"), patch.object(weekly, "read_collector_check", side_effect=lambda name, now: {"source": name, "status": "ok", "complete": True}):
                checks = weekly.collect_sources(CUTOFF, NOW, status_metadata_fetcher=fail, status_fetcher=lambda *_: self.fail("No page fetch"), status_sleeper=lambda _: None)
            self.assertTrue(publications.called)
            self.assertEqual({row["source"] for row in checks}, set(weekly.EXPECTED_SOURCES))
            self.assertEqual(next(row for row in checks if row["source"] == "arxiv_research_status")["status"], "failed")
            self.assertNotIn("private details", json.dumps(checks))

    def test_dry_run_still_has_no_status_imports_writes_network_or_lock(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(weekly, "ROOT", Path(directory)), patch.object(weekly, "git", side_effect=["main", ""]), patch.object(weekly, "collect_sources") as collect, patch.object(weekly, "collect_research_status") as status, patch.object(weekly.fcntl, "flock") as lock, patch.object(weekly, "run") as run, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(weekly.main(["--dry-run"]), 0)
            self.assertEqual(list(Path(directory).iterdir()), [])
            collect.assert_not_called(); status.assert_not_called(); lock.assert_not_called(); run.assert_not_called()

    def owned_fixture(self, root):
        context = weekly.week_context(NOW)
        relative = f"data/weekly-v3/research-status/{context['week']}/{NOW.strftime('%Y%m%dT%H%M%S%fZ')}/check.json"
        path = write(root, relative, {"observation": "fixture"})
        return context, {relative: hashlib.sha256(path.read_bytes()).hexdigest()}

    def test_owned_audit_commit_is_explicit_and_does_not_touch_research_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context, owned = self.owned_fixture(root)
            snapshot = write(root, f"data/weekly-v3/{context['week']}.json", {"week": context["week"], "revision": 7})
            before = snapshot.read_bytes()
            with patch.object(weekly, "ROOT", root), patch.object(weekly, "_status_git_changes", return_value=set(owned)), patch.object(weekly, "git", return_value="main"), patch.object(weekly, "run") as run, patch.object(weekly.subprocess, "run", return_value=SimpleNamespace(returncode=1)):
                result = weekly.publish_status_audit(context, owned, publish=True, revision=7)
            self.assertEqual(result["status"], "research_noop_with_status_observations")
            self.assertTrue(result["committed"])
            self.assertEqual(result["revision"], 7)
            self.assertEqual(snapshot.read_bytes(), before)
            commands = [call.args[0] for call in run.call_args_list]
            self.assertEqual(commands[0], ["git", "add", "--", *sorted(owned)])
            self.assertIn("metadata/status audit", commands[1][-1])
            self.assertFalse(any("v3:editorial" in command for command in commands))

    def test_local_audit_is_retained_without_publish_and_unknown_dirty_files_block_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context, owned = self.owned_fixture(root)
            with patch.object(weekly, "ROOT", root), patch.object(weekly, "_status_git_changes", return_value=set(owned)), patch.object(weekly, "run") as run:
                local = weekly.publish_status_audit(context, owned, publish=False)
                self.assertTrue(local["retained_locally"])
                run.assert_not_called()
            (root / "notes.md").write_text("user-owned change")
            with patch.object(weekly, "ROOT", root), patch.object(weekly, "_status_git_changes", return_value=set(owned) | {"notes.md"}), patch.object(weekly, "run") as run:
                blocked = weekly.publish_status_audit(context, owned, publish=True)
                self.assertEqual(blocked["status"], "unowned_changes_require_review")
                run.assert_not_called()
            self.assertEqual((root / "notes.md").read_text(), "user-owned change")

    def test_owned_file_changed_after_check_cannot_be_committed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context, owned = self.owned_fixture(root)
            (root / next(iter(owned))).write_text("concurrent edit")
            with patch.object(weekly, "ROOT", root), patch.object(weekly, "_status_git_changes", return_value=set(owned)), patch.object(weekly, "run") as run:
                result = weekly.publish_status_audit(context, owned, publish=True)
                self.assertEqual(result["status"], "status_audit_changed_during_verification")
                run.assert_not_called()

    def test_catalog_edit_during_collection_is_preserved_before_ingest(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as backup:
            root = Path(directory)
            source = write(root, "data/catalog/source-records.jsonl", [{"source_record_id": "original"}], lines=True)
            with patch.object(weekly, "ROOT", root):
                checkpoint = weekly.checkpoint_generated(["data/catalog/source-records.jsonl"], Path(backup))
                source.write_text('manual source edit\n')
                with self.assertRaisesRegex(RuntimeError, "Catalog changed during collection"):
                    weekly._verify_catalog_unchanged_before_ingest(checkpoint)
            self.assertEqual(source.read_text(), "manual source edit\n")

    def test_restore_uses_generation_receipt_not_hashes_taken_at_restore_time(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as backup:
            root = Path(directory)
            source = write(root, "data/catalog/source-records.jsonl", [{"source_record_id": "original"}], lines=True)
            with patch.object(weekly, "ROOT", root), patch.object(weekly, "publish_status_audit") as publish:
                checkpoint = weekly.checkpoint_generated(["data/catalog/source-records.jsonl"], Path(backup))
                source.write_text('generated metadata\n')
                generation_receipt = weekly.generated_hashes(checkpoint)
                source.write_text('manual edit after generation\n')
                with self.assertRaisesRegex(RuntimeError, "changed after verification"):
                    weekly._finish_status_audit(checkpoint, generation_receipt, {}, weekly.week_context(NOW), {"revision": 1}, {}, root / "audit.json", publish=True)
                publish.assert_not_called()
            self.assertEqual(source.read_text(), "manual edit after generation\n")

    def test_rename_from_foreign_path_remains_foreign_to_owned_audit(self):
        relative = "data/weekly-v3/research-status/baseline.json"
        with patch.object(weekly.subprocess, "check_output", return_value=f"R  {relative}\0notes.md\0"):
            self.assertEqual(weekly._status_git_changes(), {relative, "notes.md"})

    def test_metadata_audit_never_commits_from_non_main(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context, owned = self.owned_fixture(root)
            with patch.object(weekly, "ROOT", root), patch.object(weekly, "_status_git_changes", return_value=set(owned)), patch.object(weekly, "git", return_value="feature"), patch.object(weekly, "run") as run:
                result = weekly.publish_status_audit(context, owned, publish=True)
                self.assertEqual(result["status"], "status_audit_requires_main")
                run.assert_not_called()

    def test_status_only_main_skips_llm_report_and_research_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            now = datetime.now(timezone.utc)
            context = weekly.week_context(now)
            cutoff = now.astimezone(weekly.SHANGHAI).date() - timedelta(days=1)
            checks = [{"source": name, "status": "ok", "complete": True} for name in weekly.EXPECTED_SOURCES]
            coverage = weekly.collection_coverage(checks, cutoff, cutoff.isoformat())
            state = {"works": ["unchanged"], "calendar": {"month": "same"}}
            previous, _ = weekly.choose_snapshot({}, context, now, state, coverage, "llm_complete")
            snapshot = write(root, f"data/weekly-v3/{context['week']}.json", previous)
            original = snapshot.read_bytes()
            write(root, "data/catalog/manifest.json", {"data_through": cutoff.isoformat()})
            owned = {}
            def collect(*_):
                relative = f"data/weekly-v3/research-status/{context['week']}/{now.strftime('%Y%m%dT%H%M%S%fZ')}/check.json"
                path = write(root, relative, {"new_observation": True})
                owned[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
                return [{**row, **({"_status_audit_hashes": owned.copy()} if row["source"] == "arxiv_research_status" else {})} for row in checks]
            def git(*args):
                return "main" if args[:2] == ("branch", "--show-current") else str(root / "lock") if args[:2] == ("rev-parse", "--git-path") else ""
            with patch.object(weekly, "ROOT", root), patch.object(weekly, "git", side_effect=git), patch.object(weekly, "collect_sources", side_effect=collect), patch.object(weekly, "research_state", return_value=state), patch.object(weekly, "_status_git_changes", side_effect=lambda: set(owned) | {"data/weekly-v3/source-coverage.json"}), patch.object(weekly, "run") as run, patch.object(weekly.subprocess, "run", return_value=SimpleNamespace(returncode=1)), patch.object(weekly, "weekly_digest") as report, contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(weekly.main(["--publish"]), 0)
            self.assertEqual(snapshot.read_bytes(), original)
            self.assertEqual(len(list((root / "data/weekly-v3").glob("20*-W*.json"))), 1)
            commands = [call.args[0] for call in run.call_args_list]
            self.assertFalse(any("v3:editorial" in command for command in commands))
            report.assert_not_called()
            self.assertIn("research_noop_with_status_observations", output.getvalue())

    def test_status_audit_files_cannot_create_a_research_revision_on_rebuild(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write(root, "data/catalog/works.jsonl", [work(A)], lines=True)
            with patch.object(weekly, "ROOT", root):
                state = weekly.research_state()
                context = weekly.week_context(NOW)
                coverage = weekly.collection_coverage([], CUTOFF, "2026-08-31")
                previous, _ = weekly.choose_snapshot({}, context, NOW, state, coverage, "data_only")
                self.owned_fixture(root)
                rebuilt = weekly.research_state()
                result, changes = weekly.choose_snapshot(previous, context, NOW + timedelta(hours=1), rebuilt, coverage, "data_only")
            self.assertEqual(state, rebuilt)
            self.assertFalse(changes["research_changed"])
            self.assertEqual(result["revision"], previous["revision"])

    def test_stable_source_version_event_ids_are_evidence_not_clocks(self):
        for key in ("source_record_id", "source_record_ids", "first_public_date_source", "date_source_record_id",
                    "manifestation_id", "manifestation_ids", "snapshot_id", "event_id"):
            with self.subTest(key=key):
                self.assertNotEqual(weekly.content_hash({key: "old"}), weekly.content_hash({key: "new"}))

    def test_source_content_and_provenance_bindings_change_research_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            works = [{"work_id": "work:a", "source_record_ids": ["source:a"]}]
            sources = [{"source_record_id": "source:a", "url": "https://example.edu/paper", "source_excerpt": "Original evidence",
                        "payload_hash": "content-a", "raw_ref": "manifestation:original", "retrieved_at": "2026-09-01"}]
            provenance = [{"work_id": "work:a", "field": "title", "source_record_id": "source:a", "observed_at": "2026-09-01"}]
            write(root, "data/catalog/works.jsonl", works, lines=True)
            write(root, "data/catalog/source-records.jsonl", sources, lines=True)
            provenance_path = write(root, "data/catalog/field-provenance.jsonl", provenance, lines=True)
            with patch.object(weekly, "ROOT", root):
                original = weekly.content_hash(weekly.research_state())
                clock = copy.deepcopy(sources)
                clock[0]["retrieved_at"] = "2026-09-07"
                write(root, "data/catalog/source-records.jsonl", clock, lines=True)
                write(root, "data/catalog/field-provenance.jsonl", [*provenance, {**provenance[0], "observed_at": "2026-09-07"}], lines=True)
                self.assertEqual(weekly.content_hash(weekly.research_state()), original)
                self.assertEqual(len(provenance_path.read_text().splitlines()), 2, "Hash normalization must not delete the actual observation")
                for field in ("payload_hash", "raw_ref", "source_excerpt"):
                    changed = copy.deepcopy(sources)
                    changed[0][field] = "changed evidence"
                    write(root, "data/catalog/source-records.jsonl", changed, lines=True)
                    self.assertNotEqual(weekly.content_hash(weekly.research_state()), original)
                write(root, "data/catalog/source-records.jsonl", sources, lines=True)
                write(root, "data/catalog/field-provenance.jsonl", [{**provenance[0], "source_record_id": "source:different"}], lines=True)
                self.assertNotEqual(weekly.content_hash(weekly.research_state()), original)
                write(root, "data/catalog/field-provenance.jsonl", [{**provenance[0], "payload_hash": "new-proof-payload"}], lines=True)
                self.assertNotEqual(weekly.content_hash(weekly.research_state()), original)
                write(root, "data/catalog/field-provenance.jsonl", provenance, lines=True)
                write(root, "data/catalog/works.jsonl", [{**works[0], "source_record_ids": ["source:different"]}], lines=True)
                self.assertNotEqual(weekly.content_hash(weekly.research_state()), original)

    def test_operational_checks_survive_clock_audit_and_health_change_without_research_revision(self):
        for stale in (False, True):
            with self.subTest(stale=stale), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                now = datetime.now(timezone.utc)
                context = weekly.week_context(now)
                cutoff = now.astimezone(weekly.SHANGHAI).date() - timedelta(days=1)
                old_time, new_time = "2026-09-01T00:00:00Z", now.isoformat()
                health_path = write(root, "data/catalog/source-health.jsonl", [{"source_id": "source:a", "status": "healthy", "last_checked": old_time}], lines=True)
                org_path = write(root, "data/catalog/organizations.jsonl", [{"organization_id": "org:a", "source_health": "healthy", "last_checked": old_time}], lines=True)
                source_path = write(root, "data/catalog/source-records.jsonl", [{"source_record_id": "source:a", "url": "https://example.edu", "retrieved_at": old_time}], lines=True)
                manifest_path = write(root, "data/catalog/manifest.json", {"data_through": cutoff.isoformat(), "health_digest": hashlib.sha256(health_path.read_bytes()).hexdigest()})
                before_checks = [{"source": name, "status": "ok", "complete": True, "checked_at": old_time} for name in weekly.EXPECTED_SOURCES]
                with patch.object(weekly, "ROOT", root):
                    before_state = weekly.research_state()
                    before_coverage = weekly.collection_coverage(before_checks, cutoff, cutoff.isoformat())
                    previous, _ = weekly.choose_snapshot({}, context, now, before_state, before_coverage, "data_only")
                snapshot = write(root, f"data/weekly-v3/{context['week']}.json", previous)
                owned = {}
                def collect(*_):
                    relative = f"data/weekly-v3/research-status/{context['week']}/{now.strftime('%Y%m%dT%H%M%S%fZ')}/check.json"
                    path = write(root, relative, {"checked_at": new_time})
                    owned[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
                    checks = copy.deepcopy(before_checks)
                    for row in checks:
                        row["checked_at"] = new_time
                        if row["source"] == "arxiv_research_status": row["_status_audit_hashes"] = owned.copy()
                        if stale and row["source"] == "official_groups": row.update(status="failed", complete=False, consecutive_failures=2)
                    return checks
                commands = []
                def run(command, env=None):
                    commands.append(command)
                    if "v3:ingest" in command:
                        write(root, "data/catalog/source-health.jsonl", [{"source_id": "source:a", "status": "stale" if stale else "healthy", "last_checked": new_time}], lines=True)
                        write(root, "data/catalog/organizations.jsonl", [{"organization_id": "org:a", "source_health": "stale" if stale else "healthy", "last_checked": new_time}], lines=True)
                        write(root, "data/catalog/source-records.jsonl", [{"source_record_id": "source:a", "url": "https://example.edu", "retrieved_at": new_time}], lines=True)
                        write(root, "data/catalog/manifest.json", {"data_through": cutoff.isoformat(), "health_digest": hashlib.sha256(health_path.read_bytes()).hexdigest()})
                def git(*args):
                    return "main" if args[:2] == ("branch", "--show-current") else str(root / "lock") if args[:2] == ("rev-parse", "--git-path") else ""
                changed_paths = lambda: set(owned) | {"data/weekly-v3/source-coverage.json", "data/catalog/source-health.jsonl", "data/catalog/organizations.jsonl", "data/catalog/source-records.jsonl", "data/catalog/manifest.json"}
                with patch.object(weekly, "ROOT", root), patch.object(weekly, "git", side_effect=git), patch.object(weekly, "collect_sources", side_effect=collect), patch.object(weekly, "run", side_effect=run), patch.object(weekly, "_status_git_changes", side_effect=changed_paths), patch.object(weekly.subprocess, "run", return_value=SimpleNamespace(returncode=1)), patch.object(weekly, "weekly_digest"), contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(weekly.main(["--publish", "--data-only"]), 0)
                    self.assertEqual(weekly.content_hash(weekly.research_state()), weekly.content_hash(before_state))
                self.assertEqual(json.loads(snapshot.read_text())["revision"], previous["revision"])
                self.assertEqual(json.loads(health_path.read_text())["last_checked"], new_time)
                self.assertEqual(json.loads(org_path.read_text())["last_checked"], new_time)
                self.assertEqual(json.loads(source_path.read_text())["retrieved_at"], new_time)
                self.assertEqual(json.loads(manifest_path.read_text())["health_digest"], hashlib.sha256(health_path.read_bytes()).hexdigest())
                self.assertEqual(json.loads(org_path.read_text())["source_health"], "stale" if stale else "healthy")
                self.assertEqual(any(command == ["npm", "test"] for command in commands), stale, "Coverage changes must not use the early status-only path")
                if stale:
                    self.assertEqual(json.loads(snapshot.read_text())["collection_coverage"]["status"], "partial")


if __name__ == "__main__":
    unittest.main()
