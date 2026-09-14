import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from catalog_rules import publication_verified, eligible_month, attribution_valid, independent_clusters
from catalog_store import save_catalog, load_catalog, revision_snapshot
from catalog_enrichment import finalize_facts, ingest_delta


def empty_payload():
    return {name: [] for name in ["works", "manifestations", "organizations", "work-organization-links", "source-records", "field-provenance", "work-aliases", "evidence-events", "editorial-claims", "work-relations", "reconciliation", "taxonomy-assignments"]}


def work(wid="arxiv:2605.00001"):
    return {"work_id": wid, "title": "A robot policy", "authors": ["Ada Researcher"], "identifiers": {"arxiv": "2605.00001", "doi": None}, "first_public_date": "2026-05-01", "first_public_date_precision": "day", "relevance": {"status": "included", "score": 3, "classifier_version": "3.1"}, "primary_direction": "D1", "directions": ["D1"], "questions": [], "facets": {}, "manifestation_ids": [], "source_record_ids": [], "aliases": [], "evidence_flags": {"real_robot": True}}


class CatalogRulesTest(unittest.TestCase):
    def test_peer_review_is_not_broadcast(self):
        official = {"https://proceedings.mlr.press/v305/paper25.html"}
        proven = {"kind": "conference", "url": next(iter(official)), "status": "peer_reviewed_official_proceedings"}
        discovered = {**proven, "status": "discovered_needs_official_check"}
        self.assertTrue(publication_verified(proven, official))
        self.assertFalse(publication_verified(discovered, official))
        self.assertFalse(publication_verified({**proven, "url": "https://proceedings.mlr.press/"}, {"https://proceedings.mlr.press/"}))

    def test_year_precision_does_not_create_january_work(self):
        self.assertIsNone(eligible_month({**work(), "first_public_date_precision": "year"}))
        self.assertIsNone(eligible_month(work(), "2026-04-30"))
        self.assertEqual(eligible_month(work(), "2026-05-31"), "2026-05")

    def test_g2_needs_temporal_membership(self):
        link = {"evidence_grade": "G2", "evidence_url": "https://example.edu/papers"}
        self.assertFalse(attribution_valid(link, work()))
        link["membership_evidence"] = {"author": "Ada Researcher", "valid_from": "2026-06-01", "valid_to": None, "source_url": "https://example.edu/people"}
        self.assertFalse(attribution_valid(link, work()))
        link["membership_evidence"]["valid_from"] = "2025-01-01"
        self.assertTrue(attribution_valid(link, work()))

    def test_common_title_words_are_not_project_identity(self):
        a = {**work("a"), "title": "Learning Robust Locomotion", "authors": []}
        b = {**work("b"), "title": "Learning Robust Grasping", "authors": []}
        result = independent_clusters([a, b])
        self.assertNotEqual(result["a"], result["b"])
        a["project_series_ids"] = b["project_series_ids"] = ["official-project-series"]
        result = independent_clusters([a, b])
        self.assertEqual(result["a"], result["b"])

    def test_acceptance_does_not_move_first_publication(self):
        payload = empty_payload()
        payload["works"] = [work()]
        payload["source-records"] = [{"source_record_id": "src", "source_type": "official_openreview_decision", "url": "https://openreview.net/forum?id=official"}]
        payload["manifestations"] = [{"manifestation_id": "m", "work_id": work()["work_id"], "source_record_id": "src", "kind": "conference", "status": "accepted_peer_reviewed", "url": "https://openreview.net/forum?id=official", "venue": "CoRL", "year": 2026, "accepted_at": "2026-09-04T12:00:00Z", "date_precision": "day"}]
        result = finalize_facts(payload, "2026-09-05")
        self.assertEqual(result["works"][0]["first_public_date"], "2026-05-01")
        self.assertEqual(result["evidence-events"][0]["published_at"], "2026-09-04T12:00:00Z")
        self.assertEqual(result["works"][0]["evidence_grade"], "E3", "Coauthorship is not independent replication")

    def test_persistent_store_preserves_edits_and_partitions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = empty_payload()
            payload["works"] = [work()]
            first = save_catalog(root, payload, {"data_through": "2026-08-31"})
            restored, metadata = load_catalog(root)
            second = save_catalog(root, restored, metadata)
            self.assertEqual(first["catalog_hash"], second["catalog_hash"])
            self.assertEqual(len(list((root / "works").glob("*.jsonl"))), 256)
            self.assertFalse((root / "works.jsonl").exists())

    def test_new_doi_does_not_change_existing_canonical_id(self):
        current = empty_payload()
        current["works"] = [work()]
        current["works"][0]["summary_zh"] = "人工核验后的摘要"
        incoming = empty_payload()
        added = work("doi:10.1234/new")
        added["identifiers"]["doi"] = "10.1234/new"
        added["summary_zh"] = "模型新摘要"
        incoming["works"] = [added]
        incoming["source-records"] = [{"source_record_id": "new-source"}]
        incoming["reconciliation"] = [{"source_record_id": "new-source", "work_id": added["work_id"]}]
        result = ingest_delta(current, incoming)
        self.assertEqual(len(result["works"]), 1)
        self.assertEqual(result["works"][0]["work_id"], work()["work_id"])
        self.assertEqual(result["works"][0]["summary_zh"], "人工核验后的摘要")
        self.assertEqual(result["works"][0]["identifiers"]["doi"], "10.1234/new")

    def test_late_revision_and_readonly_export(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = {"month": "2026-08", "data_through": "2026-08-31", "count": 10}
            self.assertEqual(revision_snapshot(root, "2026-08", original, persist=True)["revision"], 1)
            self.assertEqual(revision_snapshot(root, "2026-08", {**original, "data_through": "2026-09-03"}, persist=True)["revision"], 1)
            changed = {**original, "count": 11}
            self.assertEqual(revision_snapshot(root, "2026-08", changed, persist=True)["revision"], 2)
            history_before = (root / "2026-08/history.json").read_bytes()
            revision_snapshot(root, "2026-08", {**changed, "count": 12}, persist=False)
            self.assertEqual((root / "2026-08/history.json").read_bytes(), history_before)


if __name__ == "__main__":
    unittest.main()
