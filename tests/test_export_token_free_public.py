import gzip
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from export_token_free_public import export_public


def record(work_id="arxiv:2609.00001", observed_at="2026-09-22T02:30:00Z"):
    return {
        "schema_version": "1", "work_id": work_id, "observation_id": "hardware-source:fixture",
        "observed_at": observed_at, "source_url": "https://arxiv.org/html/2609.00001v1",
        "source_state": "full_text_available", "raw_sha256": "a" * 64,
        "text_sha256": "b" * 64, "process_state": "extracted_not_read",
        "processing_key": "c" * 64,
        "matches": [{"dictionary_id": "unitree-g1", "name": "Unitree G1", "category": "robot_platform",
                     "context_only": False, "source_locator": "https://arxiv.org/html/2609.00001v1#S2.p1",
                     "simulation_word_present": False, "negation_word_present": False}],
        "article_read_complete": False, "usage_verified": False,
    }


class PublicExportTests(unittest.TestCase):
    def test_exports_only_unverified_records_and_exact_source_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "records.jsonl"
            rows = [record(), record("arxiv:2609.00002", "2026-09-22T03:00:00Z")]
            rows[1]["matches"].append({**rows[1]["matches"][0], "context_only": True})
            payload = b"".join((json.dumps(row) + "\n").encode() for row in rows)
            source.write_bytes(payload)
            summary = export_public(source, root / "api", root / "downloads", latest_limit=1)
            self.assertEqual(summary["records_sha256"], hashlib.sha256(payload).hexdigest())
            self.assertEqual(summary["total_records"], 2)
            self.assertEqual(summary["candidate_work_count"], 2)
            self.assertEqual(summary["candidate_mention_count"], 2)
            self.assertEqual(summary["candidate_frequency"][0]["candidate_work_count"], 2)
            latest = json.loads((root / "api/latest.json").read_text())
            self.assertEqual([row["work_id"] for row in latest["rows"]], ["arxiv:2609.00002"])
            with gzip.open(root / "downloads/records.jsonl.gz", "rt") as archive:
                exported = [json.loads(line) for line in archive]
            self.assertEqual(len(exported), 2)
            self.assertTrue(all(row["usage_verified"] is False and row["article_read_complete"] is False
                                for row in exported))

    def test_rejects_pretend_verification_and_extra_body_field(self):
        for change in ({"usage_verified": True}, {"article_read_complete": True},
                       {"body": "Private article text"}):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                source = root / "records.jsonl"
                source.write_text(json.dumps({**record(), **change}) + "\n")
                with self.assertRaises(ValueError):
                    export_public(source, root / "api", root / "downloads")
                self.assertFalse((root / "downloads/records.jsonl.gz").exists())

    def test_missing_input_exports_explicit_empty_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            summary = export_public(root / "missing.jsonl", root / "api", root / "downloads")
            self.assertEqual(summary["total_records"], 0)
            self.assertEqual(summary["records_sha256"], hashlib.sha256(b"").hexdigest())
            self.assertEqual(json.loads((root / "api/latest.json").read_text())["rows"], [])


if __name__ == "__main__":
    unittest.main()
