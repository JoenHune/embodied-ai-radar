"""Synthetic release-clock and identity fixtures; no real acceptance claims."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from conference_changes import build_conference_changes

EDITION = {"edition_id": "fixture-corl-2026", "venue": "CoRL", "year": 2026, "scope": "main",
           "accepted_venue_id": "robot-learning.org/CoRL/2026/Conference",
           "notification_date": "2026-09-04", "notification_date_source": "https://conference.example/official-notification"}
STATUS = {"edition_id": EDITION["edition_id"], "source_kind": "official_openreview", "source_url": "https://api2.openreview.net/notes?content.venueid=robot-learning.org%2FCoRL%2F2026%2FConference",
          "complete": True, "expected_count": 1, "fetched_count": 1, "status": "complete", "checked_at": "2026-09-06T00:00:00Z"}


def fixture(public="2026-05-12", first_seen="2026-05-13", *, precision="day", wid="arxiv:fixture+one/part"):
    work = {"work_id": wid, "title": "Synthetic robot fixture", "first_public_date": public, "first_public_date_precision": precision,
            "source_record_ids": ["source:public", "source:decision"], "relevance": {"status": "included"}}
    if first_seen is not None:
        work["first_seen_at"] = first_seen
    version = {"manifestation_id": "manifest:decision", "work_id": wid, "kind": "conference", "venue": "CoRL", "year": 2026,
               "track": "main_conference", "peer_reviewed": True, "status": "accepted_peer_reviewed", "accepted_at": "2026-09-04T12:00:00Z",
               "date_precision": "day", "observed_at": "2026-09-05T00:00:00Z", "url": "https://openreview.net/forum?id=fixture-a", "source_record_id": "source:decision"}
    sources = [{"source_record_id": "source:public", "source_type": "official_preprint", "url": "https://arxiv.org/abs/fixture", "published_at": public, "date_precision": precision},
               {"source_record_id": "source:decision", "source_type": "official_openreview_decision", "url": version["url"], "retrieved_at": "2026-09-05T00:00:00Z"}]
    return [work], [version], sources


def main_track(result):
    return next(row for row in result["tracks"] if row["track"] == "main")


class ConferenceChangeTests(unittest.TestCase):
    def run_case(self, data=None, status=None, **kwargs):
        data = data or fixture()
        return build_conference_changes(EDITION, *data, source_status=STATUS if status is None else status, **kwargs)

    def category(self, result):
        return main_track(result)["items"][0]["category"]

    def test_existing_work_acceptance_never_moves_first_publication(self):
        data = fixture(); before = copy.deepcopy(data)
        result = self.run_case(data)
        self.assertEqual(self.category(result), "existing_work_accepted")
        self.assertEqual(main_track(result)["items"][0]["first_public_date"], "2026-05-12")
        self.assertEqual(result["events"][0]["local_acceptance_date"], "2026-09-04")
        self.assertEqual(data, before)

    def test_late_discovery_is_not_a_new_research_publication(self):
        self.assertEqual(self.category(self.run_case(fixture(first_seen="2026-09-05"))), "newly_discovered_prior_publication")

    def test_genuine_first_publication_can_follow_private_acceptance(self):
        self.assertEqual(self.category(self.run_case(fixture(public="2026-09-05", first_seen="2026-09-05"))), "first_publication_in_release_window")

    def test_no_first_discovery_does_not_infer_existing_from_old_public_date(self):
        data = fixture(first_seen=None)
        data[0][0]["updated_at"] = "2026-01-01"
        data[2][0].update(retrieved_at="2026-05-12", first_seen_at="2026-05-12")
        result = self.run_case(data)
        self.assertEqual(self.category(result), "identity_or_date_review")
        self.assertIn("first_discovery_or_prior_catalog_baseline_unknown", main_track(result)["items"][0]["reasons"])

    def test_dated_baseline_and_reviewed_lineage_resolve_old_id(self):
        data = fixture(first_seen=None)
        wid = data[0][0]["work_id"]
        result = self.run_case(data, historical_baseline={"as_of": "2026-09-03", "work_ids": ["old:fixture"], "snapshot_id": "snapshot:before"},
                               work_relations=[{"relation": "merged_into", "previous_id": "old:fixture", "work_id": wid, "review_id": "review:explicit"}])
        self.assertEqual(self.category(result), "existing_work_accepted")
        self.assertEqual(main_track(result)["items"][0]["discovery_basis"], "historical_baseline")

    def test_late_or_undated_baseline_is_not_prior_membership(self):
        data = fixture(first_seen=None); wid = data[0][0]["work_id"]
        for baseline in [{"as_of": "2026-09-05", "snapshot_id": "late", "work_ids": [wid]}, {"work_ids": [wid]}]:
            self.assertEqual(self.category(self.run_case(data, historical_baseline=baseline)), "identity_or_date_review")

    def test_month_precision_crossing_release_date_stays_unknown(self):
        self.assertEqual(self.category(self.run_case(fixture(public="2026-09-01", precision="month"))), "identity_or_date_review")

    def test_unknown_acceptance_date_is_not_filled_from_global_notification(self):
        data = fixture(); data[1][0]["accepted_at"] = None
        result = self.run_case(data)
        self.assertEqual(self.category(result), "identity_or_date_review")
        self.assertIsNone(result["events"][0]["accepted_at"])

    def test_first_publication_requires_dated_source_not_bare_field(self):
        data = fixture(); data[2][0].pop("published_at")
        self.assertEqual(self.category(self.run_case(data)), "identity_or_date_review")

    def test_blocked_empty_source_has_unknown_counters_not_zero_acceptances(self):
        result = build_conference_changes(EDITION, [], [], [], {"status": "access_blocked", "complete": False, "fetched_count": 0, "expected_count": None, "checked_at": STATUS["checked_at"]})
        track = main_track(result)
        self.assertEqual(track["coverage_status"], "unknown")
        self.assertIsNone(track["display_work_count"])
        self.assertTrue(all(row["item_count"] is None for row in track["categories"]))
        self.assertFalse(track["allow_conference_share"])

    def test_retained_sample_is_partial_and_does_not_claim_conference_shares(self):
        result = self.run_case(status={**STATUS, "complete": False, "expected_count": None, "status": "access_blocked"})
        self.assertEqual(main_track(result)["coverage_status"], "partial")
        self.assertEqual(main_track(result)["display_work_count"], 1)
        self.assertFalse(main_track(result)["allow_conference_share"])

    def test_duplicate_snapshots_of_one_forum_are_one_acceptance_event(self):
        data = fixture(); other = copy.deepcopy(data[1][0]); other.update(manifestation_id="manifest:second", decision_note_id="decision:new-detail")
        data[1].append(other)
        result = self.run_case(data)
        self.assertEqual(main_track(result)["observed_event_count"], 1)
        self.assertEqual(main_track(result)["observed_work_count"], 1)

    def test_two_forums_of_one_work_count_one_work_two_events(self):
        data = fixture(); other = copy.deepcopy(data[1][0]); other.update(manifestation_id="manifest:second", url="https://openreview.net/forum?id=fixture-b", source_record_id="source:second")
        data[1].append(other); data[2].append({**data[2][1], "source_record_id": "source:second", "url": other["url"]}); data[0][0]["source_record_ids"].append("source:second")
        result = self.run_case(data, status={**STATUS, "expected_count": 2, "fetched_count": 2})
        self.assertEqual(main_track(result)["observed_event_count"], 2)
        self.assertEqual(main_track(result)["observed_work_count"], 1)
        self.assertEqual(main_track(result)["coverage_status"], "complete")

    def test_source_url_without_owned_relation_is_not_acceptance_evidence(self):
        data = fixture(); data[0][0]["source_record_ids"].remove("source:decision")
        result = self.run_case(data)
        self.assertEqual(result["events"], [])
        self.assertEqual(result["acceptance_review_queue"][0]["reason"], "acceptance_source_not_owned_by_work")

    def test_wrong_edition_year_or_official_query_cannot_claim_complete(self):
        for changes in [{"edition_id": "wrong-edition"}, {"year": 2025}, {"fetched_count": 2},
                        {"source_url": "https://api2.openreview.net/notes?content.venueid=robot-learning.org%2FCoRL%2F2025%2FConference"},
                        {"source_url": "https://mirror.example/notes?content.venueid=robot-learning.org%2FCoRL%2F2026%2FConference"}]:
            with self.subTest(changes=changes):
                self.assertEqual(main_track(self.run_case(status={**STATUS, **changes}))["coverage_status"], "partial")

    def test_workshop_never_enters_main_counts(self):
        data = fixture(); data[1][0]["track"] = "workshop"
        result = self.run_case(data)
        self.assertEqual(main_track(result)["observed_work_count"], 0)
        workshop = next(t for t in result["tracks"] if t["track"] == "workshop")
        self.assertEqual(workshop["observed_work_count"], 1)
        self.assertEqual(workshop["coverage_status"], "partial")

    def test_author_claim_does_not_become_official_acceptance(self):
        data = fixture(); data[2][1]["source_type"] = "author_homepage"
        result = self.run_case(data)
        self.assertEqual(result["events"], [])
        self.assertEqual(result["acceptance_review_queue"][0]["reason"], "acceptance_not_supported_by_official_source")

    def test_same_forum_ambiguous_canonical_is_not_merged(self):
        data = fixture(); second = copy.deepcopy(data[0][0]); second["work_id"] = "work:ambiguous"; data[0].append(second)
        other = {**data[1][0], "work_id": second["work_id"], "manifestation_id": "manifest:ambiguous"}; data[1].append(other)
        result = self.run_case(data)
        self.assertIsNone(result["events"][0]["work_id"])
        self.assertTrue(result["events"][0]["identity_conflict"])

    def test_identity_urls_are_encoded_and_relevance_not_promoted(self):
        data = fixture(); data[0][0]["relevance"]["status"] = "manual_review"
        item = main_track(self.run_case(data))["items"][0]
        self.assertEqual(item["relevance"], "manual_review")
        self.assertEqual(item["database_path"], "/database/?ids=arxiv%3Afixture%2Bone%2Fpart&relevance=all")

    def test_utc_acceptance_rolls_into_shanghai_calendar_day(self):
        data = fixture(); data[1][0]["accepted_at"] = "2026-09-03T20:00:00Z"
        self.assertEqual(self.run_case(data)["events"][0]["local_acceptance_date"], "2026-09-04")

    def test_order_invariant_and_inputs_serializable(self):
        data = fixture()
        self.assertEqual(self.run_case(data), self.run_case([list(reversed(rows)) for rows in data]))
        json.dumps(self.run_case(data))


if __name__ == "__main__":
    unittest.main()
