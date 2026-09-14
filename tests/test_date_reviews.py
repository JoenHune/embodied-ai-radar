import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from catalog_store import TABLES, fingerprint
from catalog_enrichment import finalize_facts, ingest_delta
from ingest_date_reviews import apply_date_reviews, ingest_date_reviews, review_source_id
from generate_v3_editorial import build_evidence_packet
from signal_evidence import make_signal_draft, source_content_digest, validate_signal_record
from temporal_evidence import evidence_as_of


def fixture():
    payload = {name: [] for name in TABLES}
    url = "https://example.test/report"
    row = {"work_id": "report:fixture", "title": "World model report", "abstract": "Controlled robot experiments are described in this source.", "authors": [],
           "identifiers": {}, "first_public_date": "2026-08-15", "first_public_date_precision": "day", "relevance": {"status": "included", "score": 1, "classifier_version": "3"},
           "primary_direction": "D3", "directions": ["D3"], "questions": ["Q1"], "facets": {}, "source_record_ids": ["source:official", "source:legacy"],
           "manifestation_ids": ["manifest:report"], "aliases": [], "curated": True, "evidence_flags": {},
           "_managed_field_hashes": {"first_public_date": fingerprint("2026-08-15"), "first_public_date_precision": fingerprint("day")}}
    payload["works"] = [row]
    payload["source-records"] = [{"source_record_id": "source:official", "source_type": "official_company_report", "url": url, "published_at": "2026-08-15", "retrieved_at": "2026-08-26"},
                                  {"source_record_id": "source:legacy", "source_type": "group-updates", "url": url, "published_at": "2026-08-15", "date_precision": "day", "retrieved_at": "2026-08-26"}]
    payload["manifestations"] = [{"manifestation_id": "manifest:report", "work_id": row["work_id"], "url": url, "kind": "technical_report", "published_at": "2026-08-15", "date_precision": "day", "source_record_id": "source:official", "peer_reviewed": False}]
    payload["evidence-events"] = [{"event_id": "event:report", "work_id": row["work_id"], "url": url, "event_type": "technical_report", "published_at": "2026-08-15", "occurred_at": "2026-08-15", "date_precision": "day", "first_seen_at": "2026-08-26", "observed_at": "2026-08-26"}]
    payload["field-provenance"] = [{"work_id": row["work_id"], "field": "first_public_date", "source_record_id": "source:legacy", "observed_at": "2026-08-26", "basis": "exact_source_value"}]
    review = {"review_id": "date-review:fixture", "work_id": row["work_id"], "source_url": url, "source_record_ids": row["source_record_ids"][:],
              "publication_month": "2026-08", "source_excerpt": "August 2026", "review_status": "verified", "verified_by": "codex_source_audit",
              "verified_at": "2026-09-05T16:23:25Z", "reason": "Official page supports month only; preserve original observations.",
              "manifestation_ids": ["manifest:report"], "event_ids": ["event:report"], "superseded_date_values": ["2026-08-15"]}
    return payload, review


class DateReviewTests(unittest.TestCase):
    def test_month_correction_preserves_raw_dates_first_seen_and_provenance(self):
        payload, review = fixture()
        before = copy.deepcopy(payload)
        result = apply_date_reviews(payload, [review])
        work, version, event = result["works"][0], result["manifestations"][0], result["evidence-events"][0]
        sid = review_source_id(review)
        self.assertEqual((work["first_public_date"], work["first_public_date_precision"]), ("2026-08-01", "month"))
        self.assertEqual(work["date_history"][0]["previous_date"], "2026-08-15")
        self.assertEqual(work["first_public_date_source"], sid)
        self.assertIn(sid, work["source_record_ids"])
        self.assertEqual((version["published_at"], version["date_precision"]), ("2026-08-01", "month"))
        self.assertEqual((event["published_at"], event["occurred_at"], event["date_precision"]), ("2026-08-01", "2026-08-01", "month"))
        self.assertEqual(event["first_seen_at"], "2026-08-26")
        self.assertEqual(event["observed_at"], "2026-08-26")
        for old, current in zip(before["source-records"], result["source-records"]):
            self.assertTrue(all(current[key] == value for key, value in old.items()))
            self.assertEqual(current["date_supersession"]["source_record_id"], sid)
        self.assertIn(before["field-provenance"][0], result["field-provenance"])
        archived = result["source-records"][-1]
        self.assertEqual(archived["source_excerpt"], "August 2026")
        self.assertEqual(archived["published_at"], "2026-08-01")
        self.assertEqual(archived["date_precision"], "month")

    def test_repeated_ingest_is_byte_equivalent(self):
        payload, review = fixture()
        apply_date_reviews(payload, [review])
        before = json.dumps(payload, sort_keys=True)
        apply_date_reviews(payload, [review])
        self.assertEqual(json.dumps(payload, sort_keys=True), before)

    def test_unrelated_urls_versions_and_acceptance_are_untouched(self):
        payload, review = fixture()
        unrelated = {**payload["manifestations"][0], "manifestation_id": "manifest:other", "url": "https://example.test/other", "kind": "conference", "peer_reviewed": True, "accepted_at": "2026-08-11", "published_at": "2026-09-01"}
        event = {**payload["evidence-events"][0], "event_id": "event:accept", "event_type": "accepted", "accepted_at": "2026-08-11"}
        payload["manifestations"].append(copy.deepcopy(unrelated))
        payload["evidence-events"].append(copy.deepcopy(event))
        payload["manifestations"][0]["accepted_at"] = "2026-08-14"
        apply_date_reviews(payload, [review])
        self.assertEqual(payload["manifestations"][1], unrelated)
        self.assertEqual(payload["evidence-events"][1], event)
        self.assertEqual(payload["manifestations"][0]["accepted_at"], "2026-08-14")

    def test_other_canonical_date_source_is_not_overwritten(self):
        payload, review = fixture()
        payload["works"][0].update(first_public_date="2026-05-02", first_public_date_source="source:earlier")
        apply_date_reviews(payload, [review])
        self.assertEqual(payload["works"][0]["first_public_date"], "2026-05-02")
        self.assertEqual(payload["works"][0]["first_public_date_source"], "source:earlier")
        payload, review = fixture()
        payload["works"][0]["first_public_date_source"] = "source:unrelated-same-day"
        apply_date_reviews(payload, [review])
        self.assertEqual(payload["works"][0]["first_public_date"], "2026-08-15")

    def test_invalid_work_source_target_and_excerpt_fail_without_mutation(self):
        mutations = [{"source_record_ids": ["foreign"]}, {"source_url": "https://evil.test"}, {"manifestation_ids": ["missing"]},
                     {"event_ids": ["missing"]}, {"source_excerpt": "We published a report"}, {"publication_month": "2026-07"}, {"verified_at": "2026-09-05"}]
        for mutation in mutations:
            payload, review = fixture()
            before = copy.deepcopy(payload)
            review.update(mutation)
            with self.assertRaises(ValueError):
                apply_date_reviews(payload, [review])
            self.assertEqual(payload, before)

    def test_changed_review_id_cannot_overwrite_archived_evidence(self):
        payload, review = fixture()
        apply_date_reviews(payload, [review])
        before = copy.deepcopy(payload)
        review["reason"] = "Silently changed"
        with self.assertRaises(ValueError):
            apply_date_reviews(payload, [review])
        self.assertEqual(payload, before)

    def test_unknown_new_publication_date_requires_another_review(self):
        payload, review = fixture()
        payload["manifestations"][0]["published_at"] = "2026-09-02"
        with self.assertRaises(ValueError):
            apply_date_reviews(payload, [review])

    def test_month_evidence_not_available_halfway_through_month(self):
        payload, review = fixture()
        apply_date_reviews(payload, [review])
        self.assertEqual(evidence_as_of(payload["works"][0], payload["manifestations"], "2026-08-15")["manifestations"], [])
        self.assertEqual(len(evidence_as_of(payload["works"][0], payload["manifestations"], "2026-08-31")["manifestations"]), 1)

    def test_second_finalize_keeps_reviewed_month_and_no_duplicate_active_release(self):
        payload, review = fixture()
        payload["organizations"] = [{"organization_id": "org:fixture", "tracking_unit": True}]
        payload["work-organization-links"] = [{"work_id": "report:fixture", "organization_id": "org:fixture", "evidence_grade": "G1", "evidence_url": review["source_url"], "source_record_id": "source:official"}]
        payload["evidence-events"][0]["organization_id"] = "org:fixture"
        finalize_facts(payload, "2026-09-06")
        apply_date_reviews(payload, [review])
        finalize_facts(payload, "2026-09-06")
        self.assertEqual(payload["works"][0]["first_public_date_precision"], "month")
        releases = [row for row in payload["evidence-events"] if row.get("research_eligible") and not row.get("review_required")]
        self.assertEqual(len(releases), 1)
        self.assertEqual(releases[0]["date_precision"], "month")
        self.assertEqual(releases[0]["published_at"], "2026-08-01")

    def test_editorial_only_uses_review_source_month_not_superseded_days(self):
        payload, review = fixture()
        apply_date_reviews(payload, [review])
        packet = build_evidence_packet({"month": "2026-08", "status": "complete"}, payload)
        docs = [doc for card in packet["evidence_cards"] for doc in card["source_documents"]]
        self.assertTrue(docs)
        self.assertTrue(all(doc["source_record_id"] == review_source_id(review) and doc["public_at"] == "2026-08-01" and doc["public_at_precision"] == "month" for doc in docs))

    def test_signal_evidence_cannot_keep_using_old_precise_source_date(self):
        payload, review = fixture()
        card = build_evidence_packet({"month": "2026-08", "status": "complete"}, payload)["evidence_cards"][0]
        self.assertFalse(card["experimental_text_available"])
        # Reconstruct an already-stored historical synthetic draft, not a new
        # model request: the current packet correctly withholds mutable report
        # text. Date supersession must still invalidate old records too.
        card = {**card, "abstract": payload["works"][0]["abstract"],
                "source_content_digest": source_content_digest(payload["works"][0])}
        assessment = {"signal_id": "S1", "work_id": card["work_id"], "evidence_card_id": card["evidence_id"], "stance": "neutral", "statement": "实验设置仍需语义核查。",
                      "source_url": review["source_url"], "source_record_ids": ["source:official"], "public_at": "2026-08-15", "public_at_precision": "day", "research_scope": "in_scope",
                      "experiment": {"setting": None, "baseline": None, "metric": None, "limitations": []}, "source_spans": [{"field": "abstract", "start": 0, "end": len(card["abstract"]), "quote": card["abstract"]}]}
        draft = make_signal_draft(assessment, card, month="2026-08", model="gpt-5.6-sol", generated_at="2026-09-05T16:23:25Z", input_digest="a" * 64)
        self.assertEqual(validate_signal_record(draft, payload["works"][0], payload["source-records"]), [])
        apply_date_reviews(payload, [review])
        self.assertIn("source_public_date_superseded", validate_signal_record(draft, payload["works"][0], payload["source-records"]))

    def test_fresh_legacy_delta_cannot_restore_precise_dates(self):
        payload, review = fixture()
        incoming = copy.deepcopy(payload)
        apply_date_reviews(payload, [review])
        sid = "source:new-legacy-copy"
        incoming["works"][0]["source_record_ids"].append(sid)
        incoming["source-records"].append({**incoming["source-records"][0], "source_record_id": sid})
        incoming["reconciliation"] = [{"source_record_id": sid, "work_id": "report:fixture"}]
        ingest_delta(payload, incoming)
        finalize_facts(payload, "2026-09-06")
        apply_date_reviews(payload, [review])
        self.assertEqual(payload["works"][0]["first_public_date_precision"], "month")
        self.assertEqual(payload["works"][0]["first_public_date"], "2026-08-01")
        self.assertTrue(all(row["date_precision"] == "month" for row in payload["manifestations"]))
        fresh = next(row for row in payload["source-records"] if row["source_record_id"] == sid)
        self.assertIn("date_supersession", fresh)
        self.assertEqual(fresh["published_at"], "2026-08-15")

    def test_file_adapter_and_real_review_selector_validity(self):
        with tempfile.TemporaryDirectory() as directory:
            payload, review = fixture()
            path = Path(directory)
            (path / "date-evidence-additions.jsonl").write_text(json.dumps(review) + "\n")
            self.assertEqual(ingest_date_reviews(payload, path)["works"][0]["first_public_date_precision"], "month")
        reviews = [json.loads(line) for line in (ROOT / "data/date-evidence-additions.jsonl").read_text().splitlines()]
        self.assertEqual(len(reviews), 2)
        self.assertTrue(all(row["publication_month"] == "2026-08" and row["source_excerpt"] == "August 2026" for row in reviews))


if __name__ == "__main__":
    unittest.main()
