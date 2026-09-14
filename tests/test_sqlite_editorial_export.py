import copy
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sqlite_editorial_export import build_editorial_archive, audit_editorial_archive, read_editorial_artifacts


class EditorialSQLiteTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.addCleanup(self.connection.close)
        self.month = {"month": "2026-08", "status": "complete", "model": "fixture", "response_id": "resp:fixture",
                      "claims": [{"summary": "世界模型 π0", "supporting_ids": ["work:1"], "future_field": None}],
                      "direction_summaries": [{"direction": "D1", "summary": "中文", "numeric_claims": []}],
                      "question_summaries": [], "organization_changes": [], "counterevidence": [], "watchlist": [],
                      "post_edit_reviews": [{"reviewer_kind": "ai", "edits": [{"before": None, "after": "保留"}]}]}
        self.artifacts = {"monthly/2026-08.json": self.month,
                          "monthly/2026-09.json": {"month": "2026-09", "status": "data_only", "claims": []},
                          "revisions/2026-08/" + "a" * 64 + ".json": {**self.month, "post_edit_reviews": []},
                          "reviews/2026-08-fixture.json": {"month": "2026-08", "edits": []},
                          "work-localizations.jsonl": [{"work_id": "work:1", "summary_zh": "两条相同也保留"}] * 2,
                          "signal-evidence.jsonl": []}

    def test_round_trip_all_sections_history_localizations_and_future_fields(self):
        original = copy.deepcopy(self.artifacts)
        manifest = build_editorial_archive(self.connection, self.artifacts)
        self.assertEqual(manifest["artifact_count"], 6)
        self.assertEqual(audit_editorial_archive(self.connection, self.artifacts)["status"], "passed")
        self.assertEqual(self.artifacts, original)
        restored = {path: json.loads(raw) for path, raw in self.connection.execute("SELECT path,payload_json FROM editorial_artifacts")}
        self.assertEqual(restored, original)
        self.assertEqual(self.connection.execute("SELECT status FROM monthly_editorial WHERE month='2026-09'").fetchone()[0], "data_only")
        self.assertEqual(self.connection.execute("SELECT count(*) FROM editorial_narratives").fetchone()[0], 2)

    def test_all_six_narrative_sections_are_queryable_including_duplicate_rows(self):
        from sqlite_editorial_export import SECTIONS
        for section in SECTIONS:
            self.month[section] = [{"text": "same", "optional": None}] * 2
        build_editorial_archive(self.connection, self.artifacts)
        self.assertEqual(dict(self.connection.execute("SELECT section,count(*) FROM editorial_narratives GROUP BY section")), dict.fromkeys(SECTIONS, 2))
        self.assertEqual(audit_editorial_archive(self.connection, self.artifacts)["narrative_count"], 12)

    def test_same_count_value_corruption_is_detected(self):
        build_editorial_archive(self.connection, self.artifacts)
        self.connection.execute("UPDATE editorial_artifacts SET payload_json=json_set(payload_json,'$.claims[0].summary','wrong') WHERE path='monthly/2026-08.json'")
        self.assertEqual(audit_editorial_archive(self.connection, self.artifacts)["status"], "failed")

    def test_repeated_build_has_stable_manifest_and_does_not_commit_caller(self):
        self.connection.execute("CREATE TABLE caller(value)")
        self.connection.execute("INSERT INTO caller VALUES(1)")
        one = build_editorial_archive(self.connection, self.artifacts)
        two = build_editorial_archive(self.connection, self.artifacts)
        self.assertEqual(one, two)
        self.connection.rollback()
        self.assertEqual(self.connection.execute("SELECT count(*) FROM caller").fetchone()[0], 0)

    def test_empty_archive_works(self):
        self.assertEqual(build_editorial_archive(self.connection, {})["artifact_count"], 0)
        self.assertEqual(audit_editorial_archive(self.connection, {})["status"], "passed")

    def test_idle_connection_keeps_transaction_uncommitted(self):
        self.assertFalse(self.connection.in_transaction)
        build_editorial_archive(self.connection, self.artifacts)
        self.assertTrue(self.connection.in_transaction)
        self.connection.rollback()
        self.assertFalse(self.connection.execute("SELECT name FROM sqlite_master WHERE name='editorial_artifacts'").fetchall())

    def test_invalid_input_rejected_without_mutating_previous_archive(self):
        build_editorial_archive(self.connection, self.artifacts)
        with self.assertRaises(ValueError):
            build_editorial_archive(self.connection, {".env": {"key": "never publish"}})
        self.assertEqual(audit_editorial_archive(self.connection, self.artifacts)["status"], "passed")

    def test_reader_excludes_diagnostics_attempts_status_and_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path, value in self.artifacts.items():
                dest = root / path
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text("\n".join(json.dumps(row) for row in value) if dest.suffix == ".jsonl" else json.dumps(value))
            (root / "status.json").write_text('{"transient": true}')
            (root / "monthly/2026-08.attempt.json").write_text('{"transient": true}')
            (root / "monthly/2026-10.json").symlink_to(root / "monthly/2026-08.json")
            self.assertEqual(read_editorial_artifacts(root), self.artifacts)


if __name__ == "__main__":
    unittest.main()
