import copy
import json
import tempfile
import unittest
from pathlib import Path

from test_catalog_rules import empty_payload, work
from catalog_store import fingerprint
from merge_reviewed_identities import merge_reviewed_identities


class IdentityReviewTest(unittest.TestCase):
    def test_checked_company_card_merges_without_promoting_an_unrelated_paper(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, review = self.fixture()
            target, old = payload["works"]
            old_id = old["work_id"]
            old["work_id"] = "artifact:card"
            old["authors"] = []
            old["relevance"]["status"] = "manual_review"
            review["work_ids"] = [target["work_id"], old["work_id"]]
            url = "https://example.edu/blog/unique-report"
            review["duplicate_release"] = {"url": url, "organization_id": "org:lab", "same_release_evidence": "Official article and report identity reviewed"}
            for version in payload["manifestations"]:
                version["url"] = url
                version["kind"] = "project" if version["work_id"] == old_id else "preprint"
                if version["work_id"] == old_id:
                    version["work_id"] = old["work_id"]
            payload["work-organization-links"] = [{"work_id": row["work_id"], "organization_id": "org:lab", "evidence_grade": "G1"} for row in payload["works"]]
            (root / "identity-reviews.jsonl").write_text(json.dumps(review) + "\n")
            result = merge_reviewed_identities(copy.deepcopy(payload), root)
            self.assertEqual(len(result["works"]), 1)
            self.assertEqual(result["works"][0]["relevance"]["status"], "included")
            self.assertEqual(result["work-relations"][0]["prior_canonical_record"]["relevance"]["status"], "manual_review")
            payload["manifestations"][1]["kind"] = "preprint"
            with self.assertRaises(ValueError):
                merge_reviewed_identities(payload, root)

    def fixture(self):
        payload = empty_payload()
        a, b = work("arxiv:2502.01465"), work("title:later-name")
        a.update(title="Original title", first_public_date="2025-02-03", source_record_ids=["a"])
        b.update(title="Later proceedings title", first_public_date="2025-10-07", source_record_ids=["b"])
        payload["works"] = [a, b]
        payload["manifestations"] = [{"manifestation_id": "a", "work_id": a["work_id"], "source_record_id": "a", "published_at": "2025-02-03"}, {"manifestation_id": "b", "work_id": b["work_id"], "source_record_id": "b", "published_at": "2025-10-07"}]
        payload["reconciliation"] = [{"source_record_id": "b", "work_id": b["work_id"], "status": "mapped"}]
        payload["work-organization-links"] = [{"work_id": b["work_id"], "organization_id": "org:lab", "evidence_grade": "G1"}]
        review = {"review_id": "explicit-review", "review_status": "verified", "canonical_work_id": a["work_id"], "work_ids": [a["work_id"], b["work_id"]], "reviewed_at": "2026-09-05T16:13:19Z", "reason": "Official lab links the title variants to one project", "source_urls": ["https://example.edu/lab", "https://arxiv.org/abs/2502.01465"]}
        return payload, review

    def test_merge_preserves_original_sources_titles_and_all_reference_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, review = self.fixture()
            (root / "identity-reviews.jsonl").write_text(json.dumps(review) + "\n")
            result = merge_reviewed_identities(payload, root)
            self.assertEqual(len(result["works"]), 1)
            self.assertEqual(result["works"][0]["first_public_date"], "2025-02-03")
            self.assertEqual(result["works"][0]["title_aliases"], ["Later proceedings title"])
            self.assertEqual(result["manifestations"][1]["title"], "Later proceedings title")
            self.assertEqual(result["reconciliation"][0]["work_id"], "arxiv:2502.01465")
            self.assertEqual(result["work-organization-links"][0]["work_id"], "arxiv:2502.01465")
            self.assertEqual(result["work-relations"][0]["prior_canonical_record"]["title"], "Later proceedings title")
            self.assertEqual(fingerprint(merge_reviewed_identities(copy.deepcopy(result), root)), fingerprint(result))

    def test_unreviewed_records_do_not_merge_and_author_conflicts_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, review = self.fixture()
            (root / "identity-reviews.jsonl").write_text(json.dumps({**review, "review_status": "draft"}) + "\n")
            self.assertEqual(len(merge_reviewed_identities(payload, root)["works"]), 2)
            (root / "identity-reviews.jsonl").write_text(json.dumps(review) + "\n")
            payload["works"][1]["authors"] = ["Different author"]
            with self.assertRaises(ValueError):
                merge_reviewed_identities(payload, root)


if __name__ == "__main__":
    unittest.main()
