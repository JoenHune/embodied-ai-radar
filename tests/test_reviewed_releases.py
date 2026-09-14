"""Release gaps must not destroy versions or manufacture review evidence."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from catalog_store import TABLES, read_table
from ingest_reviewed_releases import ingest_reviewed_releases
from catalog_rules import publication_verified

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    payload = {key: [] for key in TABLES}
    payload["organizations"] = [{"organization_id": "org:example", "tracking_unit": True}]
    work = {"work_id": "arxiv:2604.23073", "title": "User corrected title", "authors": ["Author"], "abstract": "User abstract",
            "first_public_date": "2026-04-24", "first_public_date_precision": "day", "first_public_date_source": "source:old",
            "relevance": {"status": "included", "score": 2, "classifier_version": "human-v1"}, "primary_direction": "D8", "directions": ["D8"],
            "questions": [], "facets": {}, "strict_peer_reviewed": False, "evidence_grade": "E0", "evidence_flags": {},
            "manifestation_ids": ["manifest:arxiv"], "source_record_ids": ["source:old"], "aliases": [], "summary_zh": "人工摘要"}
    payload["works"] = [work]
    payload["source-records"] = [{"source_record_id": "source:old", "source_type": "arxiv", "url": "https://arxiv.org/abs/2604.23073", "published_at": "2026-04-24"}]
    payload["manifestations"] = [{"manifestation_id": "manifest:arxiv", "work_id": work["work_id"], "kind": "preprint", "url": "https://arxiv.org/abs/2604.23073", "published_at": "2026-04-24", "date_precision": "day", "peer_reviewed": False, "source_record_id": "source:old", "version": "v1"}]
    row = {"review_id": "review:rlt", "work_id": work["work_id"], "mode": "existing", "review_status": "verified", "reviewed_by": "source auditor", "reviewed_at": "2026-09-05T17:00:00Z",
           "identity_evidence": {"review_status": "verified", "statement": "Same official title and all authors; direct arXiv link.", "source_keys": ["report"], "basis": "same_title_all_authors_official_chain", "confirmed_work_id": work["work_id"]},
           "sources": [{"source_key": "report", "url": "https://example.org/rlt", "title": "Earlier RL report", "published_at": "2026-03-19", "date_precision": "day", "retrieved_at": "2026-09-05T16:00:00Z", "raw_sha256": "a" * 64, "hash_scope": "http_response_body_bytes", "byte_count": 1024, "excerpt": "March 19, 2026. Robot policy optimization with RL tokens.", "original_id": "official:rlt"}],
           "manifestations": [{"key": "report", "kind": "technical_report", "source_key": "report", "evidence_layer": "R"}],
           "organization_links": [{"organization_id": "org:example", "evidence_grade": "G1", "source_key": "report", "statement": "Official lab research release."}],
           "relevance_review": {"review_status": "verified", "statement": "Research report, preserve existing work classification.", "source_keys": ["report"], "scope": "research_release", "status": "preserve_existing"},
           "earlier_date_review": {"review_status": "verified", "statement": "The inspected report predates arXiv.", "source_keys": ["report"], "date_source_key": "report", "expected_previous_date": "2026-04-24"}}
    return payload, row


class ReviewedReleaseTests(unittest.TestCase):
    def test_pure_and_idempotent(self):
        payload, row = fixture()
        before = copy.deepcopy(payload)
        after = ingest_reviewed_releases(payload, [row])
        self.assertEqual(payload, before)
        self.assertEqual(after, ingest_reviewed_releases(after, [row]))

    def test_earlier_report_preserves_arxiv_version_and_date_lineage(self):
        payload, row = fixture()
        original_version = copy.deepcopy(payload["manifestations"][0])
        after = ingest_reviewed_releases(payload, [row])
        self.assertEqual(after["manifestations"][0], original_version)
        self.assertEqual(after["works"][0]["first_public_date"], "2026-03-19")
        self.assertEqual(after["works"][0]["date_history"][0]["previous_date"], "2026-04-24")
        self.assertEqual(after["works"][0]["date_history"][0]["previous_source_record_id"], "source:old")
        self.assertTrue(any(r["relation"] == "publication_date_revised" for r in after["work-relations"]))
        self.assertEqual(len(after["manifestations"]), 2)

    def test_does_not_clear_manual_fields(self):
        payload, row = fixture()
        after = ingest_reviewed_releases(payload, [row])
        for key in ["title", "abstract", "summary_zh", "relevance", "primary_direction", "evidence_flags"]:
            self.assertEqual(after["works"][0][key], payload["works"][0][key])
        after["works"][0]["summary_zh"] = "后续人工修订"
        self.assertEqual(ingest_reviewed_releases(after, [row])["works"][0]["summary_zh"], "后续人工修订")

    def test_cannot_manufacture_peer_review(self):
        payload, row = fixture()
        after = ingest_reviewed_releases(payload, [row])
        self.assertFalse(after["works"][0]["strict_peer_reviewed"])
        self.assertTrue(all(not v["peer_reviewed"] and not publication_verified(v, {v["url"]}) for v in after["manifestations"]))
        for injected in [{"peer_reviewed": True}, {"kind": "conference"}, {"accepted_at": "2026-01-01"}, {"status": "accepted_official"}]:
            forged = copy.deepcopy(row)
            forged["manifestations"][0].update(injected)
            with self.assertRaises(ValueError):
                ingest_reviewed_releases(payload, [forged])

    def test_observation_linked_to_included_work_remains_s(self):
        payload, row = fixture()
        row.pop("earlier_date_review")
        row["identity_evidence"]["basis"] = "same_project_followup"
        row["relevance_review"]["scope"] = "observation_only"
        row["manifestations"][0].update(kind="demo", evidence_layer="S", asset_id="youtube:different-video")
        after = ingest_reviewed_releases(payload, [row])
        self.assertEqual(after["works"][0]["relevance"]["status"], "included")
        event = after["evidence-events"][0]
        self.assertEqual(event["work_id"], payload["works"][0]["work_id"])
        self.assertEqual(event["evidence_layer"], "S")
        self.assertFalse(event["research_eligible"])
        self.assertFalse(event["peer_reviewed"])
        self.assertEqual(event["direction_codes"], [])

    def test_observations_cannot_gain_research_lane(self):
        payload, row = fixture()
        row["manifestations"][0]["kind"] = "deployment"
        with self.assertRaises(ValueError):
            ingest_reviewed_releases(payload, [row])

    def test_existing_candidate_is_not_upgraded_by_g1(self):
        payload, row = fixture()
        payload["works"][0]["relevance"]["status"] = "manual_review"
        after = ingest_reviewed_releases(payload, [row])
        self.assertEqual(after["works"][0]["relevance"]["status"], "manual_review")
        self.assertFalse(after["evidence-events"][0]["research_eligible"])

    def test_unknown_source_dates_do_not_backfill_precision(self):
        payload, row = fixture()
        row.pop("earlier_date_review")
        row["sources"][0].update(published_at=None, date_precision="unknown")
        after = ingest_reviewed_releases(payload, [row])
        self.assertIsNone(after["manifestations"][-1]["published_at"])
        self.assertEqual(after["manifestations"][-1]["date_precision"], "unknown")
        self.assertEqual(after["works"][0]["first_public_date"], "2026-04-24")

    def test_bad_batch_does_not_partially_mutate(self):
        payload, row = fixture()
        bad = copy.deepcopy(row)
        bad["review_id"] = "review:bad"
        bad["organization_links"][0]["organization_id"] = "org:missing"
        before = copy.deepcopy(payload)
        with self.assertRaises(ValueError):
            ingest_reviewed_releases(payload, [row, bad])
        self.assertEqual(payload, before)

    def test_changed_review_requires_new_revision(self):
        payload, row = fixture()
        after = ingest_reviewed_releases(payload, [row])
        row["sources"][0]["excerpt"] += " changed"
        with self.assertRaises(ValueError):
            ingest_reviewed_releases(after, [row])

    def test_manual_date_conflict_is_not_overwritten(self):
        payload, row = fixture()
        payload["works"][0]["first_public_date"] = "2026-04-15"
        with self.assertRaises(ValueError):
            ingest_reviewed_releases(payload, [row])
        self.assertEqual(payload["works"][0]["first_public_date"], "2026-04-15")

    def test_existing_earlier_date_wins(self):
        payload, row = fixture()
        payload["works"][0]["first_public_date"] = "2026-02-01"
        after = ingest_reviewed_releases(payload, [row])
        self.assertEqual(after["works"][0]["first_public_date"], "2026-02-01")
        self.assertFalse(any(p["field"] == "first_public_date" for p in after["field-provenance"]))

    def test_alias_target_resolves_without_merging(self):
        payload, row = fixture()
        payload["work-aliases"] = [{"alias": "report:old", "work_id": "arxiv:2604.23073"}]
        row["work_id"] = row["identity_evidence"]["confirmed_work_id"] = "report:old"
        after = ingest_reviewed_releases(payload, [row])
        self.assertEqual(len(after["works"]), 1)
        self.assertEqual(after["manifestations"][-1]["work_id"], "arxiv:2604.23073")

    def test_duplicate_url_under_other_work_is_not_merged(self):
        payload, row = fixture()
        payload["manifestations"].append({"work_id": "arxiv:other", "url": "https://example.org/rlt"})
        with self.assertRaises(ValueError):
            ingest_reviewed_releases(payload, [row])

    def test_staging_seven_release_scope_and_new_work_reviews(self):
        rows = read_table(ROOT / "data", "release-additions")
        self.assertEqual(len(rows), 7)
        new = [r for r in rows if r["mode"] == "create_if_missing"]
        self.assertEqual({r["work_id"] for r in new}, {"arxiv:2603.04553", "official:gemini-robotics-er-2"})
        payload = {key: [] for key in TABLES}
        payload["organizations"] = [{"organization_id": link["organization_id"], "tracking_unit": True} for r in rows for link in r["organization_links"]]
        for rid in {r["work_id"] for r in rows if r["mode"] == "existing"} | {"artifact:be0e6d9f58324b6c783a"}:
            work = fixture()[0]["works"][0]
            work["work_id"] = rid
            if rid != "arxiv:2604.23073":
                work["first_public_date"] = "2025-01-01"
            work["manifestation_ids"] = []
            work["source_record_ids"] = []
            payload["works"].append(work)
        after = ingest_reviewed_releases(payload, rows)
        self.assertEqual(len(after["works"]), len(payload["works"]) + 2)
        self.assertEqual(len(after["manifestations"]), 13)
        self.assertEqual(after, ingest_reviewed_releases(after, rows))
        self.assertTrue(all(not v["peer_reviewed"] for v in after["manifestations"]))
        self.assertEqual(sum(e["evidence_layer"] == "S" for e in after["evidence-events"]), 2)

    def test_new_included_without_technical_excerpt_or_d_is_rejected(self):
        row = read_table(ROOT / "data", "release-additions")[0]
        payload = {key: [] for key in TABLES}
        payload["organizations"] = [{"organization_id": "org:cmu-pathak-research-group", "tracking_unit": True}]
        for key, value in [("contribution_excerpt", "unsupported claim"), ("primary_direction", None), ("scope", "observation_only")]:
            bad = copy.deepcopy(row)
            bad["relevance_review"][key] = value
            with self.assertRaises(ValueError):
                ingest_reviewed_releases(payload, [bad])

    def test_source_hash_time_and_identity_are_required(self):
        payload, row = fixture()
        for field, value in [("raw_sha256", "bad"), ("retrieved_at", "2026-09-05"), ("published_at", "2027-01-01")]:
            bad = copy.deepcopy(row)
            bad["sources"][0][field] = value
            with self.assertRaises(ValueError):
                ingest_reviewed_releases(payload, [bad])
        row["identity_evidence"]["basis"] = "similar_title"
        with self.assertRaises(ValueError):
            ingest_reviewed_releases(payload, [row])

    def test_existing_peer_version_is_preserved_not_relabelled(self):
        payload, row = fixture()
        payload["works"][0]["strict_peer_reviewed"] = True
        peer = {"manifestation_id": "manifest:journal", "work_id": row["work_id"], "kind": "journal", "url": "https://publisher.example/paper", "peer_reviewed": True,
                "published_at": "2026-07-01", "accepted_at": "2026-06-01", "source_record_id": "source:publisher", "status": "published_journal"}
        payload["manifestations"].append(peer)
        after = ingest_reviewed_releases(payload, [row])
        self.assertEqual(next(v for v in after["manifestations"] if v["manifestation_id"] == "manifest:journal"), peer)
        self.assertTrue(after["works"][0]["strict_peer_reviewed"])
        self.assertFalse(after["manifestations"][-1]["peer_reviewed"])

    def test_create_if_missing_does_not_replace_existing_manual_work(self):
        payload, _ = fixture()
        row = read_table(ROOT / "data", "release-additions")[0]
        payload["organizations"] = [{"organization_id": "org:cmu-pathak-research-group", "tracking_unit": True}]
        work = payload["works"][0]
        work["work_id"] = row["work_id"]
        work["relevance"]["status"] = "manual_review"
        after = ingest_reviewed_releases(payload, [row])
        self.assertEqual(len(after["works"]), 1)
        self.assertEqual(after["works"][0]["title"], "User corrected title")
        self.assertEqual(after["works"][0]["relevance"]["status"], "manual_review")
        self.assertFalse(any(p["field"] == "title" for p in after["field-provenance"]))


if __name__ == "__main__":
    unittest.main()
