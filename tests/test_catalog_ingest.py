import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from catalog_enrichment import finalize_facts, ingest_delta
from catalog_store import fingerprint, revision_snapshot
from prepare_catalog import audit_source_reconciliation
from ingest_attribution import ingest_attribution_additions
from test_catalog_rules import empty_payload, work


class CatalogIngestTest(unittest.TestCase):
    def test_new_attribution_creates_dated_group_activity_without_duplicate_release(self):
        payload = self.publication()
        payload["organizations"] = [{"organization_id": "org:lab", "tracking_unit": True}]
        payload["work-organization-links"] = [{"work_id": work()["work_id"], "organization_id": "org:lab", "evidence_grade": "G1", "evidence_url": "https://example.edu/lab/papers", "verified_at": "2026-09-05T12:00:00Z"}]
        result = finalize_facts(payload, "2026-09-05")
        releases = [event for event in result["evidence-events"] if event.get("semantic_role") == "canonical_first_publication"]
        self.assertEqual(len(releases), 1)
        self.assertEqual(releases[0]["published_at"], "2025-01-12")
        self.assertEqual(releases[0]["observed_at"], "2026-09-05T12:00:00Z")
        repeat = finalize_facts(copy.deepcopy(result), "2026-09-06")
        self.assertEqual(len(repeat["evidence-events"]), len(result["evidence-events"]))
        payload = self.publication()
        payload["organizations"], payload["work-organization-links"] = result["organizations"], result["work-organization-links"]
        payload["evidence-events"] = [{"event_id": "curated", "work_id": work()["work_id"], "organization_id": "org:lab", "event_type": "paper", "published_at": "2025-01-12", "attribution_grade": "G1"}]
        final = finalize_facts(payload, "2026-09-05")
        self.assertFalse(any(event.get("semantic_role") == "canonical_first_publication" for event in final["evidence-events"]))

    def test_monthly_revision_diff_and_revert_are_monotonic(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = {"month": "2026-08", "revision": 1, "coverage": {"included_works": 1}, "work_ids": ["a"]}
            second = {**first, "coverage": {"included_works": 2}, "work_ids": ["a", "b"]}
            revision_snapshot(root, "2026-08", first, persist=True)
            changed = revision_snapshot(root, "2026-08", second, persist=True)
            self.assertEqual(changed["revisions"][-1]["differences"]["added_work_ids"], ["b"])
            self.assertEqual(json.loads((root / "2026-08/r2.json").read_text())["revision"], 2)
            reverted = revision_snapshot(root, "2026-08", first, persist=True)
            self.assertEqual(reverted["revision"], 3)
            self.assertEqual(reverted["revisions"][-1]["differences"]["removed_work_ids"], ["b"])
            self.assertEqual(revision_snapshot(root, "2026-08", first, persist=False)["revision"], 3)
            preview = revision_snapshot(root, "2026-08", second, persist=False)
            self.assertFalse(preview["revision_persisted"])
            self.assertEqual(preview["revisions"][-1]["revision"], 4)
            self.assertFalse((root / "2026-08/r4.json").exists())

    def test_organization_can_have_official_project_channel_without_invented_home(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            org = {"organization_id": "org:official-project-group", "official_urls": {"projects": "https://example.edu/robot-project/"}}
            (root / "organization-additions.json").write_text(json.dumps({"organizations": [org]}))
            result = ingest_attribution_additions(empty_payload(), root)
            self.assertEqual(result["organizations"], [org])
            self.assertNotIn("home", result["organizations"][0]["official_urls"])
            org["official_urls"] = {"projects": "javascript:bad"}
            (root / "organization-additions.json").write_text(json.dumps({"organizations": [org]}))
            with self.assertRaises(ValueError):
                ingest_attribution_additions(empty_payload(), root)

    def test_reconciliation_cannot_hide_missing_row_with_extra_historical_mapping(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = {"title": "Actual public source row", "id": "source-work"}
            (root / "works.json").write_text(json.dumps([record]))
            sid = "source:works:" + fingerprint(record)[:24]
            sources = [{"source_record_id": sid, "payload_hash": fingerprint(record)}]
            unrelated = [{"source_record_id": "old-1", "work_id": "w"}, {"source_record_id": "old-2", "work_id": "w"}]
            self.assertEqual(audit_source_reconciliation(root, sources, unrelated, {"w"})["status"], "failed")
            valid = unrelated + [{"source_record_id": sid, "work_id": "w", "status": "mapped", "basis": "arxiv_id"}]
            self.assertEqual(audit_source_reconciliation(root, sources, valid, {"w"})["checked_rows"], 1)
            self.assertEqual(audit_source_reconciliation(root, sources, valid, {"w"})["status"], "ok")
            record["title"] = "Changed title requires a new payload record"
            (root / "works.json").write_text(json.dumps([record]))
            self.assertEqual(audit_source_reconciliation(root, sources, valid, {"w"})["status"], "failed")

    def publication(self):
        payload = empty_payload()
        payload["works"] = [work()]
        url = "https://proceedings.mlr.press/v270/old25.html"
        payload["source-records"] = [{"source_record_id": "official", "source_type": "official-proceedings", "url": url}]
        payload["manifestations"] = [{"manifestation_id": "published", "source_record_id": "official", "work_id": work()["work_id"], "kind": "conference", "status": "peer_reviewed_official_proceedings", "url": url, "published_at": "2025-01-12", "date_precision": "day", "venue": "CoRL", "year": 2024}]
        return payload

    def test_late_arxiv_upload_uses_earlier_verified_publication(self):
        payload = self.publication()
        result = finalize_facts(payload, "2026-09-05")
        current = result["works"][0]
        self.assertEqual(current["first_public_date"], "2025-01-12")
        self.assertEqual(current["date_history"][0]["previous_date"], "2026-05-01")
        self.assertEqual(current["first_public_date_source"], "official")
        self.assertTrue(any(row["field"] == "first_public_date" and row["source_record_id"] == "official" for row in result["field-provenance"]))
        repeated = finalize_facts(copy.deepcopy(result), "2026-09-06")
        self.assertEqual(len(repeated["works"][0]["date_history"]), 1)
        self.assertEqual(len(repeated["evidence-events"]), 1)

    def test_unverified_or_imprecise_publication_does_not_move_date(self):
        for change in [{"status": "discovered_needs_official_check"}, {"date_precision": "year"}, {"date_precision": "unknown"}]:
            payload = self.publication()
            payload["manifestations"][0].update(change)
            self.assertEqual(finalize_facts(payload, "2026-09-05")["works"][0]["first_public_date"], "2026-05-01")

    def test_manual_date_correction_is_not_overwritten(self):
        payload = self.publication()
        payload["works"][0]["_managed_field_hashes"] = {"first_public_date": fingerprint("2026-05-01")}
        payload["works"][0]["first_public_date"] = "2024-12-01"
        self.assertEqual(finalize_facts(payload, "2026-09-05")["works"][0]["first_public_date"], "2024-12-01")

    def test_source_updates_managed_fields_but_preserves_editorial_edits(self):
        current = finalize_facts(self.publication(), "2026-09-05")
        current["works"][0]["summary_zh"] = "人工审阅的摘要"
        current["works"][0]["abstract"] = "Manually corrected abstract"
        incoming = empty_payload()
        row = work()
        row.update(title="Corrected source title", abstract="New source abstract", summary_zh="New machine summary")
        incoming["works"] = [row]
        incoming["source-records"] = [{"source_record_id": "new"}]
        incoming["reconciliation"] = [{"source_record_id": "new", "work_id": row["work_id"]}]
        result = ingest_delta(current, incoming)["works"][0]
        self.assertEqual(result["title"], "Corrected source title")
        self.assertEqual(result["abstract"], "Manually corrected abstract")
        self.assertEqual(result["summary_zh"], "人工审阅的摘要")
        self.assertEqual(result["first_public_date"], "2025-01-12")

    def test_validation_event_refreshes_without_duplicate_or_lost_observation(self):
        payload = finalize_facts(self.publication(), "2026-09-05")
        payload["evidence-events"][0].update(date_precision="unknown", observed_at="2026-09-01T03:00:00Z")
        payload["manifestations"][0]["published_at"] = "2025-01-13"
        result = finalize_facts(payload, "2026-09-06")
        self.assertEqual(len(result["evidence-events"]), 1)
        self.assertEqual(result["evidence-events"][0]["published_at"], "2025-01-13")
        self.assertEqual(result["evidence-events"][0]["date_precision"], "day")
        self.assertEqual(result["evidence-events"][0]["observed_at"], "2026-09-01T03:00:00Z")


if __name__ == "__main__":
    unittest.main()
