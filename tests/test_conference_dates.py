"""Synthetic ingestion fixtures; private creation is not public release."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from catalog_enrichment import ingest_conferences
from catalog_rules import eligible_month


def record():
    return {"forum_id": "synthetic-publication", "note_id": "synthetic-publication", "venue_scope": "main", "source_kind": "official_openreview",
            "title": "Synthetic generalist robot policy learning fixture", "authors": ["Fixture Researcher"], "abstract": "Robot learning for manipulation with a vision language action policy.",
            "observed_at": "2026-09-05T00:00:00Z", "accepted_at": "2026-09-04T12:00:00Z", "accepted_at_precision": "millisecond",
            "decision_status": "accepted", "forum_url": "https://openreview.net/forum?id=synthetic-publication", "arxiv_id": None, "doi": None,
            "root_note_public": True, "root_note_id": "synthetic-publication", "published_at": None, "published_at_basis": "unknown",
            "first_public_at": None, "first_public_at_precision": "unknown", "first_public_at_basis": "unknown"}


def published(row, instant="2026-09-03T20:00:00Z"):
    return {**row, "published_at": instant, "published_at_basis": "pdate", "first_public_at": instant,
            "first_public_at_precision": "millisecond", "first_public_at_basis": "public_root_note_pdate"}


def payload():
    return {key: [] for key in ["works", "manifestations", "source-records", "work-aliases", "reconciliation", "field-provenance"]}


class ConferencePublicationDateTests(unittest.TestCase):
    def ingest(self, row, data=None):
        with tempfile.TemporaryDirectory(prefix="conference-date-fixture-") as folder:
            directory = Path(folder) / "edition"
            directory.mkdir()
            (directory / "records.jsonl").write_text(json.dumps(row) + "\n")
            return ingest_conferences(data if data is not None else payload(), Path(folder))

    def test_missing_publication_does_not_use_acceptance_or_observation(self):
        row = record(); row.update(cdate=1770000000000, tcdate=1770000000000)
        result = self.ingest(row)
        work = result["works"][0]
        self.assertIsNone(work["first_public_date"])
        self.assertEqual(work["first_public_date_precision"], "unknown")
        self.assertEqual(work["relevance"]["status"], "manual_review")
        self.assertIsNone(eligible_month(work))
        self.assertEqual(result["manifestations"][0]["accepted_at"], row["accepted_at"])
        self.assertEqual(work["first_seen_at"], row["observed_at"])

    def test_actual_public_pdate_gets_own_source_and_manuscript_version(self):
        row = published(record())
        result = self.ingest(row); work = result["works"][0]
        self.assertEqual(work["first_public_date"], "2026-09-04")
        source = next(s for s in result["source-records"] if s["source_record_id"] == work["first_public_date_source"])
        self.assertEqual(source["published_at"], row["first_public_at"])
        self.assertEqual(source["public_date_basis"], "public_root_note_pdate")
        self.assertIn(source["source_record_id"], work["source_record_ids"])
        kinds = {v["kind"]: v for v in result["manifestations"]}
        self.assertFalse(kinds["preprint"]["peer_reviewed"])
        self.assertIsNone(kinds["conference"]["published_at"])
        self.assertEqual(kinds["conference"]["accepted_at"], row["accepted_at"])

    def test_unproven_legacy_first_public_field_is_not_trusted(self):
        row = record(); row["first_public_at"] = "2026-02-01"
        self.assertIsNone(self.ingest(row)["works"][0]["first_public_date"])

    def test_wrong_root_private_or_bad_date_cannot_supply_publication(self):
        for changes in [{"root_note_public": False}, {"root_note_id": "not-this-forum"}, {"first_public_at_basis": "submission_cdate"},
                        {"published_at_basis": "tcdate"}, {"first_public_at": "2026-09-03T20:00:00"}]:
            with self.subTest(changes=changes):
                row = {**published(record()), **changes}
                self.assertIsNone(self.ingest(row)["works"][0]["first_public_date"])

    def test_existing_arxiv_and_doi_first_publication_is_not_rewritten(self):
        for kind, identifier in [("arxiv", "2605.00001"), ("doi", "10.5555/synthetic")]:
            with self.subTest(kind=kind):
                row = published(record()); row["arxiv_id" if kind == "arxiv" else "doi"] = identifier
                existing = {"work_id": f"{kind}:{identifier}", "title": row["title"], "authors": row["authors"], "identifiers": {kind: identifier},
                            "first_public_date": "2026-05-12", "first_public_date_precision": "day", "source_record_ids": ["source:older"], "relevance": {"status": "included"}}
                data = payload(); data["works"] = [existing]
                result = self.ingest(row, data)
                self.assertEqual(len(result["works"]), 1)
                self.assertEqual(result["works"][0]["first_public_date"], "2026-05-12")
                self.assertEqual(result["works"][0]["relevance"]["status"], "included")

    def test_later_pdate_can_fill_unknown_date_without_promoting_relevance(self):
        initial = self.ingest(record())
        result = self.ingest(published(record()), initial)
        self.assertEqual(len(result["works"]), 1)
        self.assertEqual(result["works"][0]["first_public_date"], "2026-09-04")
        self.assertEqual(result["works"][0]["relevance"]["status"], "manual_review")

    def test_author_claim_and_workshop_do_not_become_official_main_records(self):
        for changes in [{"source_kind": "author_homepage"}, {"venue_scope": "workshop"}, {"venue_scope": "author_claim"}]:
            self.assertEqual(self.ingest({**published(record()), **changes})["works"], [])

    def test_utc_month_boundary_uses_shanghai_calendar_without_losing_instant(self):
        row = published(record(), "2026-08-31T20:00:00Z")
        result = self.ingest(row)
        self.assertEqual(result["works"][0]["first_public_date"], "2026-09-01")
        self.assertTrue(any(s.get("published_at") == "2026-08-31T20:00:00Z" for s in result["source-records"]))


if __name__ == "__main__":
    unittest.main()
