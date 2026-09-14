"""Offline fixture-only pilot tests; no source body or cache is accessed."""
import copy
import json
import random
import socket
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import prepare_fulltext_pilot as pilot

AS_OF = "2026-09-15"
DICT = {"schema_version": "1", "version": "1", "entries": [
    {"dictionary_id": "model:franka-panda", "name": "Franka Panda", "category": "robot_arm",
     "identity_level": "model_specified", "aliases": ["Franka Panda"], "hardware_ids": []}]}


def fixture(number, *, month="2026-01", direction="D1", state="included", length=20000, work_id=None):
    aid = f"2509.{number:05d}"
    wid = work_id or "arxiv:" + aid
    work = {"work_id": wid, "title": "Fixture study " + str(number), "abstract": "PRIVATE_METADATA_ABSTRACT",
            "authors": ["A. Author"], "first_public_date": month + "-10", "first_public_date_precision": "day",
            "primary_direction": direction, "directions": ["D15", direction], "relevance": {"status": state},
            "identifiers": {"arxiv": aid}}
    source = {"work_id": wid, "arxiv_id": aid, "version": "v1", "status": "full_text_available",
              "source_url": "https://arxiv.org/html/" + aid + "v1", "effective_url": "https://arxiv.org/html/" + aid + "v1",
              "observation_id": "hardware-source:" + pilot.fingerprint([wid, 1])[:32],
              "observed_at": "2026-09-01T00:00:00Z", "parser_version": pilot.PARSER_VERSION,
              "raw_sha256": pilot.fingerprint([wid, "raw"]), "text_sha256": pilot.fingerprint([wid, "body"]),
              "transport_complete": True, "body_characters": length, "section_count": 2}
    scan = {"work_id": wid, "source_url": source["source_url"], "observed_at": "2026-09-02T00:00:00Z",
            "scope": "body", "status": "scanned", "dictionary_hash": pilot.dictionary_hash(DICT),
            "content_hash": source["text_sha256"], "source_observation_hash": source["raw_sha256"],
            "parser_version": pilot.PARSER_VERSION, "matches": [], "review_status": "unverified_machine_mentions"}
    return work, source, scan


class FulltextPilotTests(unittest.TestCase):
    def setUp(self):
        self.works, self.observations, self.scans, self.links = [], [], [], []
        self.organizations = [{"organization_id": "org:core", "tier": "T0", "tracking_unit": True,
                               "active_from": "2015", "active_to": None},
                              {"organization_id": "org:uncovered", "tier": "T0", "tracking_unit": True},
                              {"organization_id": "org:not-core", "tier": "T1", "tracking_unit": True}]
        for target in ((socket, "socket"),):
            guard = patch.object(*target, side_effect=AssertionError("no network"))
            guard.start()
            self.addCleanup(guard.stop)
        for target in ("collect_hardware_sources.Collector.__init__", "snapshot_hardware_sources.verify_cache",
                       "snapshot_hardware_sources.read_active_log_once", "promote_hardware_snapshot.promote_snapshot"):
            guard = patch(target, side_effect=AssertionError("no cache, collector, log or publication"))
            guard.start()
            self.addCleanup(guard.stop)

    def add(self, number, **kwargs):
        work, source, scan = fixture(number, **kwargs)
        self.works.append(work)
        self.observations.append(source)
        self.scans.append(scan)
        return work, source, scan

    def plan(self, **changes):
        return pilot.plan_pilot(**{"works": self.works, "observations": self.observations, "scans": self.scans,
                                   "organizations": self.organizations, "links": self.links, "dictionary": DICT,
                                   "as_of": AS_OF, **changes})

    def link(self, work, grade="G1", **changes):
        row = {"work_id": work["work_id"], "organization_id": "org:core", "evidence_grade": grade,
               "evidence_url": "https://example.org/paper", "verified_at": "2026-09-01", **changes}
        self.links.append(row)
        return row

    def test_default_selects_100_unique_and_spreads_across_months_not_recent_or_shortest(self):
        months = [pilot.month_shift("2026-09", offset) for offset in range(-12, 1)]
        for number in range(260):
            self.add(number, month=months[number % 13], direction=f"D{number % 15 + 1}",
                     state=pilot.RELEVANCE[number % 4], length=[5000, 15000, 40000, 80000][number % 4])
        result = self.plan()
        selected = result["selected"]
        self.assertEqual(len(selected), 100)
        self.assertEqual(len({row["work_id"] for row in selected}), 100)
        self.assertEqual({row["month"] for row in selected}, set(months))
        counts = [row["selected"] for row in result["coverage"]["months"] if row["stratum"] != "unknown_date"]
        self.assertLessEqual(max(counts) - min(counts), 1)
        self.assertEqual({row["length_band"] for row in selected}, set(pilot.LENGTHS))
        self.assertEqual({row["relevance_status"] for row in selected}, set(pilot.RELEVANCE[:4]))
        self.assertFalse(result["manifest"]["reading_executed"])

    def test_reordering_all_inputs_keeps_identical_plan_and_hash(self):
        for number in range(130):
            work, _, _ = self.add(number, month=f"2026-{number % 8 + 1:02d}", direction=f"D{number % 15 + 1}")
            if number % 11 == 0:
                self.link(work)
        expected = self.plan()
        rng = random.Random(73)
        for rows in (self.works, self.observations, self.scans, self.organizations, self.links):
            rng.shuffle(rows)
        self.assertEqual(expected, self.plan())

    def test_different_seed_changes_order_and_batch(self):
        for number in range(120):
            self.add(number)
        first, second = self.plan(seed="seed-a"), self.plan(seed="seed-b")
        self.assertNotEqual(first["manifest"]["batch_hash"], second["manifest"]["batch_hash"])
        self.assertNotEqual([row["work_id"] for row in first["selected"]], [row["work_id"] for row in second["selected"]])

    def test_doi_mapping_retains_canonical_work_and_exact_source_binding(self):
        work, source, _ = self.add(1, work_id="doi:10.1109/lra.2026.3726328")
        selected = self.plan()["selected"][0]
        self.assertEqual(selected["work_id"], work["work_id"])
        self.assertEqual(selected["source_observation_id"], source["observation_id"])
        for key in ("source_url", "version", "raw_sha256", "text_sha256"):
            self.assertEqual(selected[key], source[key])

    def test_source_change_changes_batch_hash_even_when_same_work_selected(self):
        self.add(1)
        before = self.plan()
        self.observations[0]["body_characters"] += 1
        after = self.plan()
        self.assertNotEqual(before["manifest"]["batch_hash"], after["manifest"]["batch_hash"])
        self.assertEqual(before["selected"][0]["work_id"], after["selected"][0]["work_id"])

    def test_same_work_multiple_versions_and_duplicate_observations_do_not_duplicate_pilot(self):
        _, source, scan = self.add(1)
        current = {**source, "version": "v2", "source_url": source["source_url"][:-1] + "2",
                   "effective_url": source["effective_url"][:-1] + "2", "observation_id": "hardware-source:" + "b" * 32}
        self.observations += [source, current]
        self.scans += [scan, {**scan, "source_url": current["source_url"]}]
        result = self.plan()
        self.assertEqual(result["manifest"]["eligible_population_count"], 1)
        self.assertEqual(result["selected"][0]["version"], "v2")
        self.assertEqual(result["selected"][0]["eligible_source_count"], 2)

    def test_latest_failure_never_falls_back_to_older_available_same_url(self):
        _, source, _ = self.add(1)
        self.observations.append({**source, "observed_at": "2026-09-03T00:00:00Z", "status": "blocked",
                                  "observation_id": "hardware-source:" + "b" * 32})
        result = self.plan()
        self.assertEqual(result["selected"], [])
        self.assertEqual(result["exclusions"][0]["reasons"], ["latest_source_blocked"])

    def test_latest_failed_scan_missing_dictionary_or_stale_parser_are_ineligible(self):
        for number in range(3):
            self.add(number)
        self.scans.append({**self.scans[0], "status": "failed", "observed_at": "2026-09-03T00:00:00Z"})
        self.scans[1]["dictionary_hash"] = "c" * 64
        self.observations[2]["parser_version"] = "arxiv-html-body-v1"
        result = self.plan()
        self.assertEqual(result["manifest"]["eligible_population_count"], 0)
        self.assertEqual(set(result["manifest"]["exclusion_reason_counts"]),
                         {"latest_current_dictionary_scan_failed", "current_dictionary_scan_missing", "latest_source_parser_not_current"})

    def test_date_window_boundaries_month_precision_and_unknown_dates(self):
        months = ["2025-08", "2025-09", "2026-08", "2026-09", "2026-10"]
        for number, month in enumerate(months):
            self.add(number, month=month)
        work, _, _ = self.add(10)
        work.update(first_public_date="2026-01", first_public_date_precision="month")
        work, _, _ = self.add(11)
        work.update(first_public_date="2026", first_public_date_precision="year")
        work, _, _ = self.add(12)
        work.update(first_public_date=None, first_public_date_precision="unknown")
        work, _, _ = self.add(13)
        work.update(first_public_date="2026-09-16")
        result = self.plan()
        rows = {row["work_id"]: row for row in result["selected"]}
        self.assertNotIn(self.works[0]["work_id"], rows)
        self.assertNotIn(self.works[4]["work_id"], rows)
        self.assertNotIn(work["work_id"], rows)
        self.assertEqual(rows[self.works[5]["work_id"]]["date_precision"], "month")
        self.assertEqual(rows[self.works[5]["work_id"]]["first_public_date"], "2026-01")
        self.assertEqual(sum(row["month"] == "unknown_date" for row in rows.values()), 2)
        self.assertEqual(len(result["manifest"]["complete_months"]), 12)

    def test_as_of_excludes_future_source_fetch_and_scan_but_accepts_same_day(self):
        for number in range(4):
            self.add(number)
        self.observations[0]["observed_at"] = "2026-09-16T00:00:00Z"
        self.scans[0]["observed_at"] = "2026-09-16T00:00:00Z"
        self.observations[1]["fetched_at"] = "2026-09-16T00:00:00Z"
        self.scans[2]["observed_at"] = "2026-09-16T00:00:00Z"
        self.scans[3]["observed_at"] = "2026-09-15T23:59:59Z"
        self.assertEqual([row["work_id"] for row in self.plan()["selected"]], [self.works[3]["work_id"]])

    def test_primary_direction_is_not_inferred_from_first_multilabel_or_relevance(self):
        work, _, _ = self.add(1, direction="D3", state="excluded")
        selected = self.plan()["selected"][0]
        self.assertEqual(selected["primary_direction"], "D3")
        self.assertEqual(selected["relevance_status"], "excluded")
        work.update(primary_direction=None, relevance=None)
        selected = self.plan()["selected"][0]
        self.assertEqual(selected["primary_direction"], "unassigned")
        self.assertEqual(selected["relevance_status"], "unknown")

    def test_g1_g2_organizations_require_flags_dates_author_and_full_membership_interval(self):
        for number in range(5):
            work, _, _ = self.add(number)
            if number == 0:
                self.link(work)
            elif number == 1:
                self.link(work, date_review_required=True)
            elif number == 2:
                self.link(work, verified_at="2026-09-16")
            else:
                self.link(work, "G2", membership_evidence={"author": "A. Author" if number == 3 else "Other Author",
                                                          "valid_from": "2025-01-01", "valid_to": "2026-12-31",
                                                          "source_url": "https://example.org/member"})
        rows = {row["work_id"]: row for row in self.plan()["eligible_population"]}
        self.assertEqual(rows[self.works[0]["work_id"]]["organization_evidence"], "G1")
        self.assertEqual(rows[self.works[3]["work_id"]]["organization_evidence"], "G2")
        self.assertTrue(all(rows[self.works[number]["work_id"]]["organization_evidence"] == "none" for number in (1, 2, 4)))

    def test_month_precision_membership_must_cover_entire_month(self):
        work, _, _ = self.add(1)
        work.update(first_public_date="2026-01", first_public_date_precision="month")
        self.link(work, "G2", membership_evidence={"author": "A. Author", "valid_from": "2026-01-15",
                                                  "source_url": "https://example.org/member"})
        self.assertEqual(self.plan()["selected"][0]["organization_evidence"], "none")

    def test_insufficient_population_reports_shortfall_and_gaps_without_padding(self):
        self.add(1)
        result = self.plan()
        self.assertEqual(result["manifest"]["shortfall"], 99)
        self.assertEqual(result["manifest"]["selected_count"], 1)
        self.assertTrue(result["manifest"]["uncovered_months"])
        self.assertTrue(result["manifest"]["uncovered_directions"])
        self.assertEqual(len(result["manifest"]["uncovered_core_organizations"]), 2)
        self.assertNotIn("org:not-core", [row["stratum"] for row in result["coverage"]["core_organizations"]])

    def test_prior_reading_hardware_controls_are_source_bound_and_never_independent_gold(self):
        work, source, _ = self.add(1)
        readings = [{"work_id": work["work_id"], "reading_id": "reading:fixture", "reading_status": "completed",
                     "read_completed_at": "2026-09-10", "source_url": source["source_url"], "raw_sha256": source["raw_sha256"], "version": source["version"]}]
        self.observations.append({**source, "raw_sha256": "b" * 64, "observed_at": "2026-08-31T00:00:00Z",
                                  "observation_id": "hardware-source:" + "b" * 32})
        reviews = [{"work_id": work["work_id"], "usage_id": "usage:fixture", "review_status": "verified", "reviewed_at": "2026-09-11",
                    "source_url": source["source_url"], "raw_sha256": "b" * 64, "source_version": "v1", "statement": "PRIVATE_REVIEW_STATEMENT"}]
        result = self.plan(readings=readings, hardware_reviews=reviews)
        control = result["selected"][0]["control"]
        self.assertEqual(control["labels"], ["prior_hardware_review_other_source", "prior_reading_same_source"])
        self.assertFalse(control["independent_gold"])
        self.assertFalse(result["manifest"]["controls_independent_gold"])
        self.assertNotIn("PRIVATE_", pilot.encode(result))

    def test_unknown_and_future_control_status_do_not_count_as_completed_reading(self):
        work, source, _ = self.add(1)
        readings = [{"work_id": work["work_id"], "reading_status": "completed", "read_completed_at": "2026-09-16"},
                    {"work_id": work["work_id"], "reading_status": "prepared", "read_completed_at": "2026-09-01"}]
        self.assertEqual(self.plan(readings=readings)["selected"][0]["control"]["labels"], [])

    def test_same_timestamp_ambiguous_sources_are_not_hash_selected_but_lineage_is_resolved(self):
        _, source, _ = self.add(1)
        other = {**source, "observation_id": "hardware-source:" + "b" * 32}
        self.observations.append(other)
        self.assertEqual(self.plan()["selected"], [])
        other["parent_observation_id"] = source["observation_id"]
        self.assertEqual(self.plan()["selected"][0]["source_observation_id"], other["observation_id"])

    def test_partial_source_is_explicit_quality_stratum_not_full_promotion(self):
        self.add(1)
        self.observations[0].update(status="partial_text", transport_complete=False)
        row = self.plan()["selected"][0]
        self.assertEqual(row["source_status"], "partial_text")
        self.assertEqual(row["status"], "partial_text")

    def test_input_conflicts_or_incorrect_canonical_identity_fail_closed(self):
        _, source, _ = self.add(1)
        self.observations.append({**source, "body_characters": 100})
        with self.assertRaisesRegex(pilot.SnapshotError, "id_conflict"):
            self.plan()
        self.observations.pop()
        source["arxiv_id"] = "2509.99999"
        with self.assertRaisesRegex(pilot.SnapshotError, "identity_mismatch"):
            self.plan()

    def test_prepare_only_writes_new_private_output_and_repeat_bytes_are_identical(self):
        self.add(1)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            catalog, public = root / "catalog", root / "public"
            catalog.mkdir()
            public.mkdir()
            rows_by_path = {catalog / "works.jsonl": self.works, catalog / "organizations.jsonl": self.organizations,
                            catalog / "work-organization-links.jsonl": self.links,
                            public / "source-observations.jsonl": self.observations, public / "source-scans.jsonl": self.scans}
            for path, rows in rows_by_path.items():
                path.write_text("".join(pilot.encode(row) + "\n" for row in rows))
            dictionary = root / "dictionary.json"
            dictionary.write_text(pilot.encode(DICT))
            before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in [*rows_by_path, dictionary]}
            def run(output):
                return pilot.prepare_pilot(catalog=catalog, published_dir=public, dictionary=dictionary,
                                           output_dir=output, as_of=AS_OF)
            manifest = run(root / "first")
            run(root / "second")
            self.assertEqual(before, {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in before})
            self.assertEqual({path.name: path.read_bytes() for path in (root / "first").iterdir()},
                             {path.name: path.read_bytes() for path in (root / "second").iterdir()})
            self.assertEqual((root / "first").stat().st_mode & 0o777, 0o700)
            self.assertEqual(manifest["selected_count"], 1)
            with self.assertRaisesRegex(pilot.SnapshotError, "must_be_new"):
                run(root / "first")
            with self.assertRaisesRegex(pilot.SnapshotError, "overlaps_inputs"):
                run(public / "nested")
            for path in (root / "first").iterdir():
                self.assertNotIn("PRIVATE_", path.read_text())

    def test_equal_instant_different_timestamp_spelling_cannot_hide_failed_scan(self):
        self.add(1)
        other = {**self.scans[0], "observed_at": "2026-09-02T00:00:00.000Z", "status": "failed"}
        self.scans.append(other)
        with self.assertRaisesRegex(pilot.SnapshotError, "scan_event_conflict"):
            self.plan()
        self.scans.reverse()
        with self.assertRaisesRegex(pilot.SnapshotError, "scan_event_conflict"):
            self.plan()

    def test_equal_instant_equivalent_scans_are_order_independent(self):
        self.add(1)
        self.scans.append({**self.scans[0], "observed_at": "2026-09-02T00:00:00.000Z"})
        before = self.plan()
        self.scans.reverse()
        self.assertEqual(self.plan(), before)

    def test_scan_cannot_precede_its_earliest_exact_source_binding(self):
        self.add(1)
        self.observations[0]["observed_at"] = "2026-09-03T00:00:00Z"
        with self.assertRaisesRegex(pilot.SnapshotError, "precedes_bound_source"):
            self.plan()

    def test_older_scan_parser_is_explicitly_ineligible(self):
        self.add(1)
        self.scans[0]["parser_version"] = "arxiv-html-body-v1"
        result = self.plan()
        self.assertEqual(result["selected"], [])
        self.assertEqual(result["exclusions"][0]["reasons"], ["latest_current_dictionary_scan_parser_not_current"])

    def test_same_body_historical_raw_scan_is_disclosed_not_claimed_reverified(self):
        _, source, scan = self.add(1)
        new = {**source, "raw_sha256": "b" * 64, "observed_at": "2026-09-03T00:00:00Z",
               "observation_id": "hardware-source:" + "b" * 32}
        self.observations.append(new)
        row = self.plan()["selected"][0]
        self.assertEqual(row["source_observation_id"], new["observation_id"])
        self.assertEqual(row["scan_binding"], "historical_raw_same_body")
        self.assertEqual(row["scan_raw_sha256"], source["raw_sha256"])
        self.assertNotEqual(row["raw_sha256"], row["scan_raw_sha256"])

    def test_empty_or_version_conflicting_control_receipts_do_not_gain_priority(self):
        work, source, _ = self.add(1)
        readings = [{"work_id": work["work_id"], "reading_status": "completed", "observed_at": "2026-09-01"},
                    {"work_id": work["work_id"], "reading_id": "reading:fixture", "reading_status": "completed",
                     "read_completed_at": "2026-09-10", "source_url": source["source_url"], "raw_sha256": source["raw_sha256"], "version": "v999"}]
        result = self.plan(readings=readings)
        self.assertEqual(result["selected"][0]["control"]["labels"], [])
        self.assertEqual(result["manifest"]["control_selected"], 0)
        self.assertEqual(result["manifest"]["as_of_timezone"], "UTC")


if __name__ == "__main__":
    unittest.main()
