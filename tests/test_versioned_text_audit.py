import copy
import json
import unittest
from pathlib import Path

from test_catalog_rules import work
from catalog_store import fingerprint
from audit_versioned_text import audit_versioned_text


class VersionTextAuditTest(unittest.TestCase):
    def fixture(self):
        schema = json.loads((Path(__file__).resolve().parents[1] / "config/versioned-text.schema.json").read_text())
        w = {**work(), "source_record_ids": ["source:version"]}
        text = {"snapshot_id": "text-snapshot:sample", "work_id": w["work_id"], "source_record_id": "source:version",
                "version": "v1", "title": "Robot learning", "abstract": "Robot experiment.", "authors": ["Ada"],
                "available_at": "2026-05-01", "date_precision": "day", "source_url": "https://arxiv.org/abs/2605.00001v1", "basis": "archived"}
        text["content_digest"] = fingerprint({key: text[key] for key in ["title", "abstract", "authors"]})
        source = {"source_record_id": "source:version", "source_type": "official_arxiv_version_metadata", "url": text["source_url"],
                  "published_at": text["available_at"], "version": "v1", "payload_hash": fingerprint(text)}
        return [text], [w], [source], schema

    def test_every_snapshot_and_source_is_checked(self):
        data = self.fixture()
        self.assertEqual(audit_versioned_text(*data)["status"], "passed")
        data[0].append(copy.deepcopy(data[0][0]))
        self.assertEqual(audit_versioned_text(*data)["errors"][0]["reason"], "duplicate_snapshot_id")

    def test_future_date_cannot_be_backdated_by_changing_only_archive(self):
        data = self.fixture()
        data[0][0]["available_at"] = "2026-04-01"
        self.assertIn("archived_snapshot_provenance_mismatch", [row["reason"] for row in audit_versioned_text(*data)["errors"]])

    def test_self_consistent_foreign_arxiv_identity_and_missing_origin_are_rejected(self):
        data = self.fixture()
        text, source = data[0][0], data[2][0]
        text["source_url"] = source["url"] = "https://arxiv.org/abs/2602.99999v2"
        source["source_origin_id"] = "missing-origin"
        source["payload_hash"] = fingerprint(text)
        reasons = {row["reason"] for row in audit_versioned_text(*data)["errors"]}
        self.assertIn("arxiv_identity_or_version_mismatch", reasons)
        self.assertIn("unresolved_or_foreign_origin_source", reasons)

    def test_orphan_invalid_url_and_changed_text_are_errors(self):
        data = self.fixture()
        data[0][0]["work_id"] = "unknown"
        self.assertEqual(audit_versioned_text(*data)["errors"][0]["reason"], "orphan_snapshot")
        data = self.fixture()
        data[0][0]["source_url"] = "not a URL"
        self.assertIn(audit_versioned_text(*data)["errors"][0]["reason"], {"schema", "invalid_source_url"})
        data = self.fixture()
        data[0][0]["abstract"] = "Unverified rewrite"
        self.assertEqual(audit_versioned_text(*data)["errors"][0]["reason"], "snapshot_content_hash_mismatch")


if __name__ == "__main__":
    unittest.main()
