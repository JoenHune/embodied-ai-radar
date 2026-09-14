"""Coverage denominators and strict affiliation/promotion boundaries."""
from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("coverage", ROOT / "scripts/organization_coverage.py")
coverage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(coverage)


def org(oid, name, kind="research_group", tier="T0", tracking=True, home=None, parents=None, aliases=None):
    return {"organization_id": oid, "display_name": name, "entity_type": kind, "tier": tier,
            "tracking_unit": tracking, "official_urls": {"home": home} if home else {},
            "parent_relations": parents or [], "aliases": aliases or []}


def work(wid, affiliations=None, grade="E2", when="2026-08-01", relevance="included"):
    return {"work_id": wid, "title": wid, "authors": ["Fixture Author"], "institutions": affiliations or [],
            "first_public_date": when, "first_public_date_precision": "day", "relevance": {"status": relevance},
            "evidence_grade": grade, "directions": ["D1"], "identifiers": {"arxiv": "2608.00001"}, "source_record_ids": ["source:work"]}


def link(wid, oid, grade="G1", **extra):
    return {"work_id": wid, "organization_id": oid, "evidence_grade": grade, "evidence_url": "https://research.example/paper", **extra}


class OrganizationCoverageTests(unittest.TestCase):
    def setUp(self):
        self.organizations = [
            org("org:nvidia", "NVIDIA", "company", "T2", False, "https://www.nvidia.com"),
            org("org:gear", "NVIDIA GEAR", parents=[{"parent_id": "org:nvidia", "evidence_url": "https://research.nvidia.com/labs/gear"}]),
            org("org:cmu", "Carnegie Mellon University", "university", "T2", False),
            org("org:ri", "CMU Robotics Institute", "research_institute", parents=[{"parent_id": "org:cmu", "evidence_url": "https://www.ri.cmu.edu"}]),
            org("org:pi", "Physical Intelligence", "research_company", aliases=["PI"]),
            org("org:mpi-pi", "MPI-IS Physical Intelligence", "laboratory", aliases=["Physical Intelligence"]),
            org("org:new", "New Research Group", tier="T2", home="https://new.example/research"),
        ]
        self.works = [work("work:first", ["NVIDIA", "CMU", "Physical Intelligence", "New Unregistered Lab"]), work("work:second")]
        self.links = []
        self.sources = [{"source_id": "source:new", "organization_id": "org:new", "url": "https://new.example/research",
                         "status": "healthy", "last_checked": "2026-09-04", "consecutive_failures": 0, "source_type": "official_group_publications"}]

    def build(self):
        return coverage.build_organization_coverage(self.works, self.organizations, self.links, self.sources, "2026-09-05")

    def test_parent_affiliation_never_becomes_gear_or_ri_link(self):
        result = self.build()
        observations = {row["affiliation"]: row for row in result["affiliation_observations"]}
        self.assertEqual(observations["NVIDIA"]["parent_organization_ids"], ["org:nvidia"])
        self.assertEqual(observations["CMU"]["parent_organization_ids"], ["org:cmu"])
        self.assertTrue(all(row["evidence_grade"] == "G0" for row in observations.values()))
        self.assertEqual(result["metrics"]["high_signal_attributed_works"], 0)
        self.assertEqual(result["tier_changes"], [])

    def test_exact_lab_affiliation_still_only_maps_to_verified_parent(self):
        self.works[0]["institutions"] = ["NVIDIA GEAR", "CMU Robotics Institute"]
        result = self.build()
        ids = {value for row in result["affiliation_observations"] for value in row["parent_organization_ids"]}
        self.assertEqual(ids, {"org:nvidia", "org:cmu"})
        self.assertEqual(result["metrics"]["high_signal_attributed_works"], 0)

    def test_pi_and_mpi_physical_intelligence_remain_ambiguous(self):
        result = self.build()
        row = next(row for row in result["t2_candidates"] if row["name"] == "Physical Intelligence")
        self.assertEqual(row["existing_parent_organization_ids"], [])
        self.assertIn("physical_intelligence_company_vs_mpi_is", row["ambiguity_flags"])
        self.assertEqual(row["matched_label_organization_ids"], ["org:mpi-pi", "org:pi"])

    def test_unknown_affiliation_does_not_invent_homepage_or_leader(self):
        candidate = next(row for row in self.build()["t2_candidates"] if row["name"] == "New Unregistered Lab")
        self.assertEqual(candidate["status"], "discovery_only")
        self.assertIsNone(candidate["official_homepage"])
        self.assertEqual(candidate["leaders"], [])
        self.assertEqual(candidate["evidence_work_ids"], ["work:first"])

    def test_corrupt_numeric_affiliation_is_retained_as_cleanup_not_group(self):
        self.works[0]["institutions"] = ["1991"]
        result = self.build()
        self.assertEqual(result["t2_candidates"], [])
        self.assertEqual(result["affiliation_observations"][0]["status"], "invalid_label")
        self.assertEqual(result["metrics"]["affiliation_labels_requiring_cleanup"], 1)

    def test_t0_with_no_activity_or_sources_is_retained_and_visible(self):
        result = self.build()
        core = [row for row in result["organization_coverage"] if row["tier"] == "T0"]
        self.assertEqual(len(core), 4)
        self.assertTrue(all(row["effective_tier"] == "T0" and row["tier_policy"] == "core_retained" for row in core))
        self.assertEqual(result["metrics"]["core_groups_visible"], 4)

    def test_two_distinct_verified_works_and_official_source_promote_t2(self):
        for row in self.works:
            row["evidence_grade"] = "E0"
            self.links.append(link(row["work_id"], "org:new"))
        result = self.build()
        self.assertEqual(result["tier_changes"][0]["to"], "T1")
        self.assertEqual(result["tier_changes"][0]["evidence_work_ids"], ["work:first", "work:second"])

    def test_one_e2_work_qualifies_but_company_e1_alone_does_not(self):
        self.links = [link("work:first", "org:new")]
        self.assertEqual(len(self.build()["tier_changes"]), 1)
        self.works[0]["evidence_grade"] = "E1"
        self.assertEqual(self.build()["tier_changes"], [])

    def test_duplicate_links_and_works_do_not_inflate_counts(self):
        self.works[0]["evidence_grade"] = "E0"
        self.links = [link("work:first", "org:new"), link("work:first", "org:new")]
        self.works.append(copy.deepcopy(self.works[0]))
        result = self.build()
        self.assertEqual(result["metrics"]["relevant_works_in_window"], 2)
        self.assertEqual(result["tier_changes"], [])
        row = next(row for row in result["organization_coverage"] if row["organization_id"] == "org:new")
        self.assertEqual(row["verified_work_count"], 1)

    def test_unverified_homepage_or_stale_check_does_not_promote(self):
        self.links = [link("work:first", "org:new")]
        self.sources[0]["last_checked"] = None
        self.assertEqual(self.build()["tier_changes"], [])
        self.sources[0]["last_checked"] = "2026-06-01"
        self.assertEqual(self.build()["tier_changes"], [])

    def test_source_registration_and_health_have_separate_denominators(self):
        result = self.build()
        self.assertEqual(result["metrics"]["registered_sources"], 2)
        self.assertEqual(result["metrics"]["verified_healthy_sources"], 1)
        self.assertEqual(result["metrics"]["source_verification_rate"], .5)
        nvidia = next(row for row in result["source_status"] if row["organization_id"] == "org:nvidia")
        self.assertEqual(nvidia["status"], "unverified")

    def test_two_failures_show_stale_and_retain_registered_source(self):
        self.sources[0].update(status="error", consecutive_failures=2)
        result = self.build()
        self.assertEqual(result["metrics"]["registered_sources"], 2)
        self.assertEqual(result["metrics"]["stale_sources"], 1)
        self.assertTrue(next(row for row in result["organization_coverage"] if row["organization_id"] == "org:new")["stale_warning"])

    def test_g3_g0_and_invalid_g2_do_not_count_as_group_attribution(self):
        for grade in ("G0", "G3", "G2"):
            self.links = [link("work:first", "org:gear", grade)]
            result = self.build()
            self.assertEqual(result["metrics"]["high_signal_attributed_works"], 0)
            self.assertEqual(len(result["high_signal_unattributed"]), 2)

    def test_g2_requires_author_and_overlapping_date_bounded_membership(self):
        member = {"author": "Fixture Author", "valid_from": "2025-01-01", "valid_to": "2026-12-31", "source_url": "https://research.example/people/archive"}
        self.links = [link("work:first", "org:gear", "G2", membership_evidence=member)]
        self.assertEqual(self.build()["metrics"]["high_signal_attributed_works"], 1)
        member["valid_from"] = "2026-09-01"
        self.assertEqual(self.build()["metrics"]["high_signal_attributed_works"], 0)
        member["valid_from"], member["author"] = "2025-01-01", "Different Author"
        self.assertEqual(self.build()["metrics"]["high_signal_attributed_works"], 0)

    def test_rates_count_canonical_work_not_number_of_joint_group_links(self):
        self.links = [link("work:first", "org:gear"), link("work:first", "org:ri")]
        result = self.build()
        self.assertEqual(result["metrics"]["high_signal_works"], 2)
        self.assertEqual(result["metrics"]["high_signal_attributed_works"], 1)
        self.assertEqual(result["metrics"]["high_signal_attribution_rate"], .5)

    def test_global_release_recall_is_unmeasured_not_fabricated_95_percent(self):
        result = self.build()
        self.assertIsNone(result["metrics"]["official_release_recall"])
        self.assertEqual(result["metrics"]["recall_status"], "not_measured")
        self.assertIsNone(result["metrics"]["gold_release_set_size"])

    def test_source_records_supply_queue_links_without_creating_org_sources(self):
        self.sources = {"registered": self.sources, "records": [{"source_record_id": "source:work", "url": "https://arxiv.org/abs/2608.00001"}]}
        result = self.build()
        self.assertEqual(result["metrics"]["registered_sources"], 2)
        self.assertIn("https://arxiv.org/abs/2608.00001", result["high_signal_unattributed"][0]["source_urls"])

    def test_window_at_month_end_is_twelve_full_months_not_one_extra_day(self):
        result = coverage.build_organization_coverage([], [], [], [], "2026-08-31")
        self.assertEqual(result["window"]["from"], "2025-09-01")
        self.assertEqual(result["window"]["to"], "2026-08-31")
        leap = coverage.build_organization_coverage([], [], [], [], "2024-02-29")
        self.assertEqual(leap["window"]["from"], "2023-03-01")

    def test_nonincluded_unknown_precision_outside_window_and_future_excluded(self):
        self.works += [work("work:candidate", relevance="candidate"), work("work:old", when="2024-01-01"), work("work:future", when="2026-10-01")]
        self.works[0]["first_public_date_precision"] = "year"
        self.assertEqual(self.build()["metrics"]["relevant_works_in_window"], 1)

    def test_pure_function_does_not_mutate_input_and_empty_rates_are_null(self):
        before = copy.deepcopy((self.works, self.organizations, self.links, self.sources))
        self.build()
        self.assertEqual((self.works, self.organizations, self.links, self.sources), before)
        empty = coverage.build_organization_coverage([], [], [], [], "2026-09-05")
        self.assertIsNone(empty["metrics"]["high_signal_attribution_rate"])
        self.assertIsNone(empty["metrics"]["source_verification_rate"])


if __name__ == "__main__":
    unittest.main()
