import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from collect_arxiv_v2 import metadata_time, parse_feed, merge_record
from versioned_text import build_versioned_text, digest, snapshot_from_payload, text_as_of, register_versioned_text_additions, validate_snapshot


def row(edition="v1", updated="2026-02-27", **extra):
    return {"arxiv_id": "2602.23721", "preprint_id": "arxiv:2602.23721", "title": "Original title" if edition == "v1" else "Revised title",
            "abstract": "Original experimental report." if edition == "v1" else "Changed experiment and results.", "authors": ["First Author"],
            "first_submitted": "2026-02-27", "updated": updated, "pdf_url": "https://arxiv.org/pdf/2602.23721" + edition,
            "arxiv_url": "https://arxiv.org/abs/2602.23721", "categories": ["cs.RO"], **extra}


def fixture(records):
    work = {"work_id": "doi:10.example/stable", "identifiers": {"arxiv": "2602.23721"}, "title": "Current canonical title", "abstract": "Current future content", "authors": [], "source_record_ids": []}
    sources = []
    for index, payload in enumerate(records):
        sid = f"source:{index}"
        work["source_record_ids"].append(sid)
        sources.append({"source_record_id": sid, "url": payload["arxiv_url"], "raw_ref": f"data/preprints.json#/{index}", "payload_hash": digest(payload), "published_at": payload["first_submitted"]})
    return work, sources


class VersionedTextTests(unittest.TestCase):
    def snapshots(self, records):
        work, sources = fixture(records)
        result = build_versioned_text([work], sources, raw_payloads={"data/preprints.json": records})
        self.assertEqual(result["issues"], [])
        return work, result["snapshots"]

    def test_cross_month_revision_uses_original_text_and_stable_canonical_id(self):
        records = [row(), row("v2", "2026-06-30")]
        work, snapshots = self.snapshots(records)
        old, revised = text_as_of(work, snapshots, "2026-02"), text_as_of(work, snapshots, "2026-06")
        self.assertEqual(old["abstract"], records[0]["abstract"])
        self.assertEqual(revised["abstract"], records[1]["abstract"])
        self.assertEqual({item["work_id"] for item in snapshots}, {"doi:10.example/stable"})
        self.assertEqual(work["abstract"], "Current future content")

    def test_only_v2_does_not_fabricate_v1_or_return_future_text(self):
        work, snapshots = self.snapshots([row("v2", "2026-06-30")])
        result = text_as_of(work, snapshots, "2026-02")
        self.assertEqual(result["status"], "retrospective_only")
        self.assertIsNone(result["title"])
        self.assertIsNone(result["abstract"])
        self.assertEqual(result["authors"], [])
        self.assertEqual(result["source_ids"], [])
        self.assertEqual(len(snapshots), 1)

    def test_same_day_versions_use_exact_instants(self):
        records = [row("v1", "2026-02-27", version="v1", submitted_at="2026-02-27T01:00:00Z", updated_at="2026-02-27T01:00:00Z"),
                   row("v2", "2026-02-27", version="v2", submitted_at="2026-02-27T01:00:00Z", updated_at="2026-02-27T02:00:00Z")]
        work, snapshots = self.snapshots(records)
        self.assertEqual(text_as_of(work, snapshots, "2026-02-27T01:30:00Z")["version"], "v1")
        self.assertEqual(text_as_of(work, snapshots, "2026-02-27T02:30:00Z")["version"], "v2")

    def test_utc_month_boundary_converts_to_shanghai(self):
        records = [row("v1", "2026-08-31", submitted_at="2026-08-31T15:00:00Z", updated_at="2026-08-31T15:00:00Z"),
                   row("v2", "2026-08-31", submitted_at="2026-08-31T15:00:00Z", updated_at="2026-08-31T17:00:00Z")]
        work, snapshots = self.snapshots(records)
        self.assertEqual(text_as_of(work, snapshots, "2026-08")["version"], "v1")
        self.assertEqual(text_as_of(work, snapshots, "2026-09")["version"], "v2")

    def test_date_only_is_not_fabricated_midnight(self):
        work, snapshots = self.snapshots([row()])
        self.assertEqual(snapshots[0]["date_precision"], "day")
        self.assertEqual(snapshots[0]["available_at"], "2026-02-27")
        self.assertEqual(text_as_of(work, snapshots, "2026-02-27T08:00:00Z")["status"], "retrospective_only")
        self.assertEqual(text_as_of(work, snapshots, "2026-02-27")["status"], "available")

    def test_unknown_updated_does_not_fall_back_to_first_submission(self):
        work, snapshots = self.snapshots([row("v2", "")])
        self.assertIsNone(snapshots[0]["available_at"])
        self.assertEqual(text_as_of(work, snapshots, "2026-08")["status"], "unavailable")

    def test_naive_timestamp_is_unknown_and_not_assumed_utc(self):
        self.assertEqual(metadata_time("2026-02-27T10:00:00"), (None, "unknown"))
        work, snapshots = self.snapshots([row("v2", "2026-02-27T10:00:00")])
        self.assertEqual(snapshots[0]["date_precision"], "unknown")

    def test_archived_observation_is_a_conservative_availability_bound(self):
        value = row("v2", "")
        work, sources = fixture([value])
        sources[0]["retrieved_at"] = "2026-09-05T12:00:00Z"
        result = build_versioned_text([work], sources, preprints=[value])
        self.assertIn("archived_observation_only", result["snapshots"][0]["basis"])
        self.assertEqual(text_as_of(work, result["snapshots"], "2026-08")["status"], "retrospective_only")

    def test_later_observation_of_old_version_does_not_replace_newer_edition(self):
        records = [row("v1", ""), row("v2", "2026-06-30")]
        work, sources = fixture(records)
        sources[0]["retrieved_at"] = "2026-09-05T12:00:00Z"
        built = build_versioned_text([work], sources, preprints=records)
        self.assertEqual(text_as_of(work, built["snapshots"], "2026-09")["version"], "v2")

    def test_mutated_array_pointer_is_not_misrepresented_as_old_archive(self):
        original = row()
        work, sources = fixture([original])
        result = build_versioned_text([work], sources, raw_payloads={"data/preprints.json": [row("v2", "2026-06-30")]})
        self.assertEqual(result["snapshots"], [])
        self.assertEqual(result["issues"][0]["reason"], "raw_payload_missing_or_hash_changed")
        sources[0]["raw_payload"] = original
        self.assertEqual(len(build_versioned_text([work], sources)["snapshots"]), 1)

    def test_hash_fallback_survives_moved_array_offsets(self):
        original = row()
        work, sources = fixture([original])
        result = build_versioned_text([work], sources, raw_payloads={"data/preprints.json": []}, preprints=[original])
        self.assertEqual(len(result["snapshots"]), 1)

    def test_embedded_archive_preserves_all_collector_history(self):
        latest = row("v2", "2026-06-30", metadata_history=[row()])
        work, sources = fixture([latest])
        result = build_versioned_text([work], sources, preprints=[latest])
        self.assertEqual({item["version"] for item in result["snapshots"]}, {"v1", "v2"})
        self.assertEqual(text_as_of(work, result["snapshots"], "2026-02")["version"], "v1")

    def test_unknown_or_foreign_history_never_enters_archive(self):
        latest = row("v2", "2026-06-30", metadata_history=[row(arxiv_id="2602.00001")])
        work, sources = fixture([latest])
        result = build_versioned_text([work], sources, preprints=[latest])
        self.assertEqual(len(result["snapshots"]), 1)
        self.assertEqual(result["issues"][0]["reason"], "historical_payload_identity_mismatch")

    def test_conflicting_same_version_same_time_is_not_arbitrarily_selected(self):
        work, snapshots = self.snapshots([row(), row(abstract="Conflicting text.")])
        result = text_as_of(work, snapshots, "2026-02")
        self.assertEqual(result["status"], "conflicting_snapshots")
        self.assertIsNone(result["abstract"])

    def test_atom_parser_preserves_version_and_full_utc_timestamps(self):
        xml = '''<feed xmlns="http://www.w3.org/2005/Atom" xmlns:o="http://a9.com/-/spec/opensearch/1.1/"><o:totalResults>1</o:totalResults><entry><id>http://arxiv.org/abs/2602.23721v2</id><title>Title</title><summary>Abstract</summary><published>2026-02-27T06:43:37Z</published><updated>2026-06-30T22:23:11+08:00</updated><author><name>Ada</name></author><category term="cs.RO"/><link title="pdf" href="https://arxiv.org/pdf/2602.23721v2"/></entry></feed>'''
        total, rows = parse_feed(xml)
        self.assertEqual(total, 1)
        value = rows[0]
        self.assertEqual(value["work_id"], "arxiv:2602.23721")
        self.assertEqual(value["arxiv_version_id"], "2602.23721v2")
        self.assertEqual(value["submitted_at"], "2026-02-27T06:43:37Z")
        self.assertEqual(value["updated_at"], "2026-06-30T14:23:11Z")
        self.assertEqual(value["updated_at_precision"], "second")
        self.assertEqual(value["first_submitted"], "2026-02-27")
        self.assertEqual(metadata_time("2026-02-27"), ("2026-02-27", "day"))

    def test_multiquery_merge_keeps_prior_version_text_and_latest_metadata(self):
        v1 = row(version="v1", discovery_queries=["cs_ro"])
        v2 = row("v2", "2026-06-30", version="v2")
        merged = merge_record(v1, v2, "robot_crosslist")
        self.assertEqual(merged["version"], "v2")
        self.assertEqual({value["version"] for value in merged["metadata_history"]}, {"v1", "v2"})
        self.assertEqual(merged["discovery_queries"], ["cs_ro", "robot_crosslist"])
        before = copy.deepcopy(merged)
        merge_record(merged, v2, "robot_crosslist")
        self.assertEqual(merged, before)

    def test_real_stemvla_archives_preserve_author_and_experiment_changes(self):
        from jsonschema import Draft202012Validator, FormatChecker
        schema = json.loads((ROOT / "config/versioned-text.schema.json").read_text())
        additions = [json.loads(line) for line in (ROOT / "data/versioned-text-additions.jsonl").read_text().splitlines()]
        self.assertEqual(len(additions), 2)
        for item in additions:
            self.assertEqual(list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(item)), [])
        work = {"work_id": "arxiv:2602.23721", "identifiers": {"arxiv": "2602.23721"}, "source_record_ids": [], "title": "Current title", "abstract": "Current abstract"}
        payload = {"works": [work], "source-records": [], "field-provenance": []}
        result = register_versioned_text_additions(payload, additions)
        self.assertEqual(payload["source-records"], [])
        self.assertEqual(register_versioned_text_additions(result, additions), result)
        self.assertEqual(result["works"][0]["work_id"], work["work_id"])
        self.assertEqual(result["works"][0]["abstract"], "Current abstract")
        built = build_versioned_text(result["works"], result["source-records"], additions=additions)
        self.assertEqual(built["issues"], [])
        old = text_as_of(result["works"][0], built["snapshots"], "2026-02")
        new = text_as_of(result["works"][0], built["snapshots"], "2026-06")
        self.assertIn("XXX", old["abstract"])
        self.assertNotIn("92.0%", old["abstract"])
        self.assertIn("92.0%", new["abstract"])
        self.assertEqual(len(old["authors"]), 6)
        self.assertEqual(len(new["authors"]), 5)
        self.assertIn("Ziang Tong", old["authors"])
        self.assertNotIn("Ziang Tong", new["authors"])

    def test_archived_source_dates_cannot_be_self_asserted_after_registration(self):
        additions = [json.loads(line) for line in (ROOT / "data/versioned-text-additions.jsonl").read_text().splitlines()]
        payload = {"works": [{"work_id": "arxiv:2602.23721", "source_record_ids": [], "identifiers": {"arxiv": "2602.23721"}}], "source-records": []}
        registered = register_versioned_text_additions(payload, additions)
        sources = {source["source_record_id"]: source for source in registered["source-records"]}
        forged = {**additions[1], "available_at": "2026-02-27T06:43:37Z"}
        self.assertIn("archived_snapshot_provenance_mismatch", validate_snapshot(forged, registered["works"][0], sources))
        with self.assertRaises(ValueError):
            register_versioned_text_additions(registered, [forged])


if __name__ == "__main__":
    unittest.main()
