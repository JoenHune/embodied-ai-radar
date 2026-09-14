"""Synthetic API fixtures. None of these titles are real conference claims."""

from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("collect_corl", ROOT / "scripts" / "collect_corl_openreview.py")
collector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(collector)
EDITION = json.loads((ROOT / "config" / "conference-editions.json").read_text())["editions"][0]
GROUP_ID = EDITION["openreview_group_id"]
CHECKED = "2026-09-05T12:00:00Z"


def wrap(data: dict) -> dict:
    return {key: {"value": value} for key, value in data.items()}


def fixture() -> dict:
    group = {"id": GROUP_ID, "readers": ["everyone"], "content": wrap({
        "title": "CoRL 2026 synthetic test fixture", "decision_field_name": "decision",
        "review_name": "Official_Review", "review_rating": "overall_score", "review_confidence": "confidence_score",
        "meta_review_name": "Meta_Review", "decision_name": "Decision",
        "accept_decision_options": ["Accept", "Accept (Poster)", "Accept (Oral)"],
    })}
    notes = [{"id": "fixture-forum-a", "forum": "fixture-forum-a", "readers": ["everyone"], "cdate": 1770000000000,
              "invitations": [GROUP_ID + "/-/Submission"], "content": wrap({
                  "title": "Synthetic fixture: closed-loop robot world model", "authors": ["Fixture Author"],
                  "abstract": "Only a collector test; this is not an actual accepted paper.",
                  "venueid": GROUP_ID, "venue": "CoRL 2026 Poster", "arxiv_id": "2605.00001v2"})},
             {"id": "fixture-forum-b", "forum": "fixture-forum-b", "readers": ["everyone"], "cdate": 1770000000000,
              "invitations": [GROUP_ID + "/-/Submission"], "content": wrap({
                  "title": "Synthetic fixture with no public decision timestamp", "authors": ["Fixture Author B"],
                  "abstract": "No invented acceptance time.", "venueid": GROUP_ID, "venue": "CoRL 2026"})}]
    review_invitation = GROUP_ID + "/Submission1/-/Official_Review"
    review = {"id": "fixture-review", "forum": "fixture-forum-a", "replyto": "fixture-forum-a", "readers": ["everyone"],
              "invitations": [review_invitation], "cdate": 1785500000000,
              "content": wrap({"summary": "Synthetic review.", "weaknesses": "Limited hardware evidence.",
                               "overall_score": "6: Weak Accept", "confidence_score": "3: Fairly confident"})}
    decision = {"id": "fixture-decision", "forum": "fixture-forum-a", "readers": ["everyone"], "cdate": 1788523200000,
                "invitations": [GROUP_ID + "/Submission1/-/Decision"], "content": wrap({"decision": "Accept (Poster)"})}
    rebuttal = {"id": "fixture-rebuttal", "forum": "fixture-forum-a", "readers": ["everyone"], "cdate": 1785600000000,
                "invitations": [GROUP_ID + "/Submission1/-/Rebuttal"], "content": wrap({"response": "Synthetic author response."})}
    invitation = {"id": review_invitation, "edit": {"note": {"content": {
        "overall_score": {"value": {"param": {"type": "string", "enum": ["1: Reject", "6: Weak Accept", "10: Strong Accept"]}}},
        "confidence_score": {"value": {"param": {"type": "string", "enum": ["1: Low", "3: Fairly confident", "5: High"]}}},
    }}}}
    return {"schema_version": "openreview-public-export-v1", "source_url": collector.endpoint(EDITION, "notes", **{"content.venueid": GROUP_ID}),
            "exported_at": CHECKED, "group": group, "notes": notes, "count": 2, "complete": True,
            "forum_notes": {"fixture-forum-a": {"notes": [notes[0], review, decision, rebuttal], "count": 4, "complete": True},
                            "fixture-forum-b": {"notes": [notes[1]], "count": 1, "complete": True}},
            "invitations": [invitation]}


class CorlCollectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory(prefix="corl-public-fixture-")
        self.output = Path(self.directory.name) / "out"
        self.export = Path(self.directory.name) / "fixture.json"
        self.data = fixture()

    def tearDown(self) -> None:
        self.directory.cleanup()

    def run_export(self, data=None, checked=CHECKED):
        self.export.write_text(json.dumps(data if data is not None else self.data))
        return collector.run_collection(EDITION, self.output, official_export=self.export, checked_at=checked)

    def records(self):
        return [json.loads(line) for line in (self.output / "records.jsonl").read_text().splitlines() if line]

    def test_export_keeps_original_review_scale_and_unknown_acceptance_date(self):
        status = self.run_export()
        self.assertTrue(status["complete"])
        self.assertEqual(status["expected_count"], 2)
        first, second = self.records()
        self.assertEqual(first["arxiv_id"], "2605.00001")
        self.assertEqual(first["accepted_at"], "2026-09-04T12:00:00.000Z")
        self.assertEqual(first["accepted_at_basis"], "decision_note_cdate")
        self.assertIsNone(second["accepted_at"])
        self.assertEqual(second["accepted_at_precision"], "unknown")
        self.assertIsNone(second["published_at"])
        self.assertIsNone(second["first_public_at"])
        self.assertEqual(second["first_public_at_basis"], "unknown")
        review = next(row for row in first["review_records"] if row["kind"] == "review")
        score = review["native_scores"]["rating"]
        self.assertEqual(score["field"], "overall_score")
        self.assertEqual(score["value"], "6: Weak Accept")
        self.assertEqual(score["scale_status"], "official_schema")
        self.assertFalse(score["normalized"])
        self.assertIn("weaknesses", review["fields"])
        self.assertEqual({row["kind"] for row in first["review_records"]}, {"review", "decision", "rebuttal"})

    def test_public_root_pdate_is_distinct_from_private_creation_and_acceptance(self):
        self.data["notes"][0]["pdate"] = 1788571200000
        self.assertTrue(self.run_export()["complete"])
        first = self.records()[0]
        self.assertTrue(first["root_note_public"])
        self.assertEqual(first["root_note_id"], "fixture-forum-a")
        self.assertEqual(first["first_public_at"], first["published_at"])
        self.assertEqual(first["first_public_at_basis"], "public_root_note_pdate")
        self.assertEqual(first["first_public_at_precision"], "millisecond")
        self.assertNotEqual(first["first_public_at"], first["accepted_at"])

    def test_missing_scale_is_explicit(self):
        self.data["invitations"] = []
        status = self.run_export()
        self.assertTrue(status["complete"])
        self.assertFalse(status["review_scale_complete"])
        review = next(row for row in self.records()[0]["review_records"] if row["kind"] == "review")
        self.assertEqual(review["native_scores"]["rating"]["scale_status"], "unavailable")

    def test_private_reply_content_is_never_persisted(self):
        forum = self.data["forum_notes"]["fixture-forum-a"]
        secret = copy.deepcopy(forum["notes"][1])
        secret.update(id="private-fixture", readers=[GROUP_ID + "/Program_Chairs"])
        secret["content"] = wrap({"summary": "private-sentinel-never-publish"})
        forum["notes"].append(secret)
        forum["count"] += 1
        self.assertTrue(self.run_export()["complete"])
        self.assertNotIn("private-sentinel", (self.output / "records.jsonl").read_text())

    def test_workshop_and_author_claim_do_not_become_main_acceptances(self):
        for scope, venueid in [("workshop", "robot-learning.org/CoRL/2026/Workshop/Example"), ("author_claim", "")]:
            with self.subTest(scope=scope):
                data = fixture()
                data["notes"][0]["content"]["venueid"]["value"] = venueid
                self.assertEqual(collector.scope_of(data["notes"][0], EDITION), scope)
                self.assertFalse(self.run_export(data)["complete"])
                self.assertEqual(self.records(), [])

    def test_403_preserves_existing_snapshot_and_first_seen(self):
        self.assertTrue(self.run_export()["complete"])
        original = (self.output / "records.jsonl").read_bytes()
        def blocked(url):
            raise collector.CollectionError("access_blocked", "Official API returned HTTP 403.", endpoint=url)
        first = collector.run_collection(EDITION, self.output, getter=blocked, checked_at="2026-09-06T12:00:00Z")
        self.assertEqual(first["status"], "access_blocked")
        self.assertFalse(first["complete"])
        self.assertIsNone(first["expected_count"])
        self.assertEqual(first["records_retained"], 2)
        self.assertEqual((self.output / "records.jsonl").read_bytes(), original)
        second = collector.run_collection(EDITION, self.output, getter=blocked, checked_at="2026-09-07T12:00:00Z")
        self.assertTrue(second["stale_warning"])
        self.run_export(checked="2026-09-08T12:00:00Z")
        self.assertTrue(all(row["observed_at"] == CHECKED and row["last_observed_at"] == "2026-09-08T12:00:00Z" for row in self.records()))

    def test_partial_export_and_empty_response_cannot_replace_snapshot(self):
        self.run_export()
        original = (self.output / "records.jsonl").read_bytes()
        for bad in [dict(self.data, count=3), dict(self.data, complete=False), dict(self.data, count=0, notes=[], forum_notes={})]:
            status = self.run_export(bad)
            self.assertFalse(status["complete"])
            self.assertEqual((self.output / "records.jsonl").read_bytes(), original)

    def test_forum_reply_coverage_required(self):
        self.data["forum_notes"]["fixture-forum-a"]["count"] = 6
        self.assertEqual(self.run_export()["status"], "incomplete")

    def test_duplicate_or_missing_forum_root_is_incomplete(self):
        for mode in ("duplicate", "root_missing"):
            data = fixture()
            forum = data["forum_notes"]["fixture-forum-a"]
            if mode == "duplicate":
                forum["notes"][1] = forum["notes"][0]
            else:
                forum["notes"] = forum["notes"][1:]
                forum["count"] -= 1
            self.assertEqual(self.run_export(data)["status"], "incomplete")

    def test_metadata_remains_available_when_notes_challenged(self):
        def getter(url):
            if urlsplit(url).path == "/groups":
                return {"groups": [self.data["group"]]}
            raise collector.CollectionError("access_blocked", "Official API returned HTTP 403.", endpoint=url)
        status = collector.run_collection(EDITION, self.output, getter=getter, checked_at=CHECKED)
        self.assertEqual(status["status"], "access_blocked")
        self.assertIsNone(status["expected_count"])
        metadata = json.loads((self.output / "group-metadata.json").read_text())
        self.assertEqual(metadata["content"]["review_rating"], "overall_score")

    def test_wrong_source_or_group_cannot_supply_acceptance(self):
        wrong_source = copy.deepcopy(self.data)
        wrong_source["source_url"] = "https://mirror.example/accepted-corl-2026"
        self.assertEqual(self.run_export(wrong_source)["status"], "invalid_export")
        wrong_group = copy.deepcopy(self.data)
        wrong_group["group"]["id"] = "robot-learning.org/CoRL/2026/Workshop"
        self.assertEqual(self.run_export(wrong_group)["status"], "invalid_metadata")

    def test_conflicting_official_decision_never_publishes(self):
        self.data["forum_notes"]["fixture-forum-a"]["notes"][2]["content"]["decision"]["value"] = "Reject"
        self.assertEqual(self.run_export()["status"], "conflicting_decision")
        self.assertEqual(self.records(), [])

    def test_pagination_exhausts_verified_count_and_handles_incomplete_pages(self):
        calls = []
        def getter(url):
            params = parse_qs(urlsplit(url).query)
            offset = int(params["offset"][0])
            calls.append(offset)
            return {"notes": self.data["notes"][offset:offset + 1], "count": 2}
        notes, count = collector.paginate(EDITION, {"content.venueid": GROUP_ID}, getter, page_size=1)
        self.assertEqual((count, len(notes), calls), (2, 2, [0, 1]))
        def short(url):
            offset = int(parse_qs(urlsplit(url).query)["offset"][0])
            return {"notes": self.data["notes"][:1] if offset == 0 else [], "count": 2}
        with self.assertRaises(collector.CollectionError) as caught:
            collector.paginate(EDITION, {}, short, page_size=1)
        self.assertEqual(caught.exception.status, "incomplete")

    def test_changing_count_and_duplicate_pages_are_incomplete(self):
        for mode in ("changing", "duplicate"):
            def getter(url):
                offset = int(parse_qs(urlsplit(url).query)["offset"][0])
                return {"notes": self.data["notes"][:1], "count": 3 if mode == "changing" and offset else 2}
            with self.assertRaises(collector.CollectionError) as caught:
                collector.paginate(EDITION, {}, getter, page_size=1)
            self.assertEqual(caught.exception.status, "incomplete")

    def test_live_path_validates_group_then_all_forums(self):
        calls = []
        def getter(url):
            route, params = urlsplit(url).path, parse_qs(urlsplit(url).query)
            calls.append(route)
            if route == "/groups":
                return {"groups": [self.data["group"]]}
            if route == "/invitations":
                return {"invitations": [item for item in self.data["invitations"] if item["id"] == params["id"][0]]}
            if "content.venueid" in params:
                return {"notes": self.data["notes"], "count": 2}
            return self.data["forum_notes"][params["forum"][0]]
        status = collector.run_collection(EDITION, self.output, getter=getter, checked_at=CHECKED)
        self.assertTrue(status["complete"])
        self.assertEqual(calls[0], "/groups")
        self.assertEqual(calls.count("/notes"), 3)


if __name__ == "__main__":
    unittest.main()
