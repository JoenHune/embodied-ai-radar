import copy
import json
import tempfile
import unittest
from pathlib import Path

from test_catalog_rules import empty_payload, work
from catalog_store import fingerprint, save_catalog, load_catalog
from archive_versioned_text import archive_versioned_text
from versioned_text import text_as_of


class ArchiveVersionedTextTest(unittest.TestCase):
    def source(self, raw, sid):
        return {"source_record_id": sid, "source_type": "preprints", "url": "https://arxiv.org/abs/2605.00001", "published_at": "2026-05-01", "payload_hash": fingerprint(raw), "raw_ref": "data/preprints.json#/0"}

    def test_archive_survives_mutable_feed_update_and_does_not_backdate_v2(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            original = {"arxiv_id": "2605.00001", "title": "Robot policy v1", "abstract": "Original experiment", "authors": ["Ada Researcher"], "pdf_url": "https://arxiv.org/pdf/2605.00001v1", "first_submitted": "2026-05-01", "updated": "2026-05-01"}
            payload = empty_payload()
            payload["works"] = [{**work(), "source_record_ids": ["original"]}]
            payload["source-records"] = [self.source(original, "original")]
            archive_versioned_text(payload, data, [original])
            self.assertEqual(len(payload["text-snapshots"]), 1)
            self.assertEqual(payload["text-snapshots"][0]["available_at"], "2026-05-01")
            frozen = copy.deepcopy(payload["text-snapshots"][0])
            revised = {**original, "title": "Robot policy v2", "abstract": "New experimental results", "pdf_url": "https://arxiv.org/pdf/2605.00001v2", "updated": "2026-06-03"}
            payload["source-records"].append(self.source(revised, "revision"))
            payload["works"][0]["source_record_ids"].append("revision")
            archive_versioned_text(payload, data, [revised])
            self.assertEqual(len(payload["text-snapshots"]), 2)
            self.assertIn(frozen, payload["text-snapshots"])
            self.assertEqual(text_as_of(payload["works"][0], payload["text-snapshots"], "2026-05")["title"], "Robot policy v1")
            self.assertEqual(text_as_of(payload["works"][0], payload["text-snapshots"], "2026-06")["title"], "Robot policy v2")
            self.assertEqual(payload["source-records"][1]["published_at"], "2026-05-01")
            before = fingerprint(payload)
            archive_versioned_text(payload, data, [revised])
            self.assertEqual(fingerprint(payload), before)
            save_catalog(data / "catalog", payload, {"data_through": "2026-06-30"})
            restored, _ = load_catalog(data / "catalog")
            self.assertEqual(restored["text-snapshots"], payload["text-snapshots"])
            self.assertEqual(len(list((data / "catalog/text-snapshots").glob("*.jsonl"))), 256)


if __name__ == "__main__":
    unittest.main()
