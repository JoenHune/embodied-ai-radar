import json
import tempfile
import unittest
from pathlib import Path

from test_catalog_rules import empty_payload, work
from ingest_capability_evidence import ingest_capability_additions
from temporal_evidence import evidence_as_of
from catalog_enrichment import finalize_facts
from catalog_rules import event_eligible


class CapabilityEvidenceTest(unittest.TestCase):
    def test_strategic_events_stay_outside_research_after_finalization(self):
        payload, _ = self.fixture()
        row = payload["works"][0]
        payload["evidence-events"] = [{"event_id": "demo", "work_id": row["work_id"], "event_type": "company_demo", "evidence_layer": "S", "attribution_grade": "G1", "review_required": False, "published_at": "2026-08-01"}]
        result = finalize_facts(payload, "2026-08-31")
        event = result["evidence-events"][0]
        self.assertFalse(event["research_eligible"])
        self.assertFalse(event["review_required"], "Known strategic observations do not become attribution errors")
        self.assertFalse(event_eligible(event, row))
        version = {"kind": "model", "work_id": row["work_id"], "evidence_layer": "S", "published_at": "2026-08-01", "date_precision": "day", "status": "released", "url": "https://example.org/demo"}
        self.assertFalse(evidence_as_of(row, [version], "2026-08-31")["evidence_flags"]["open_model"])

    def fixture(self):
        payload = empty_payload()
        row = work()
        row["source_record_ids"] = ["source"]
        payload["works"] = [row]
        payload["source-records"] = [{"source_record_id": "source", "url": "https://example.edu/paper", "published_at": None}]
        checked = {"work_id": row["work_id"], "flag": "real_robot", "value": True, "source_url": "https://example.edu/paper", "source_record_ids": ["source"], "public_at": "2026-08", "date_precision": "month", "source_excerpt": "real robot experiments", "review_status": "verified", "verified_by": "codex_source_audit", "verified_at": "2026-09-05T12:00:00Z", "observation_scope": "Source-content check, not independent replication; month from inspected paper header."}
        return payload, checked

    def test_month_precision_is_conservative_and_import_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, checked = self.fixture()
            (root / "capability-evidence-additions.jsonl").write_text(json.dumps(checked) + "\n")
            result = ingest_capability_additions(payload, root)
            ingest_capability_additions(result, root)
            row = result["works"][0]
            self.assertEqual(len(row["evidence_flag_evidence"]), 1)
            self.assertFalse(evidence_as_of(row, [], "2026-08-15", result["source-records"])["evidence_flags"]["real_robot"])
            self.assertTrue(evidence_as_of(row, [], "2026-08-31", result["source-records"])["evidence_flags"]["real_robot"])
            self.assertFalse(evidence_as_of(row, [], "2026-08-31", result["source-records"])["independent_replication_evidence_ids"])
            self.assertIsNone(result["source-records"][0]["published_at"])

    def test_foreign_sources_and_future_dates_are_rejected(self):
        for change in [{"source_record_ids": ["not-owned"]}, {"source_url": "https://wrong.example/paper"}, {"public_at": "2027-01"}, {"observation_scope": ""}]:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                payload, checked = self.fixture()
                checked.update(change)
                (root / "capability-evidence-additions.jsonl").write_text(json.dumps(checked) + "\n")
                with self.assertRaises(ValueError):
                    ingest_capability_additions(payload, root)


if __name__ == "__main__":
    unittest.main()
