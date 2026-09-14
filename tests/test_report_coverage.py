import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
from report_coverage import build_report_coverage
from test_report_text import fixture as archive_fixture
from versioned_text import snapshot_from_payload


NAMES = {"genesis-ai": "Genesis AI", "generalist-ai": "Generalist AI", "figure-ai": "Figure AI",
         "dyna-robotics": "Dyna Robotics", "sunday-robotics": "Sunday Robotics"}


def org(key, *, tier="T0", kind="research_company", parent=None):
    return {"organization_id": "org:" + key, "display_name": NAMES.get(key, key), "tier": tier,
            "slug": key, "tracking_unit": kind == "research_company" or kind == "laboratory", "entity_type": kind,
            "official_urls": {"home": "https://" + key + ".example/"},
            "parent_relations": [{"parent_id": "org:" + parent, "evidence_url": "https://example.test/organization", "valid_from": None, "valid_to": None}] if parent else []}


def fixture():
    payload, snapshot = archive_fixture()
    payload["works"][0]["relevance"] = {"status": "included"}
    payload["report-text-snapshots"] = [snapshot]
    payload["organizations"] = [org(key) for key in NAMES]
    payload["work-organization-links"] = [{"work_id": snapshot["work_id"], "organization_id": "org:generalist-ai",
                                           "evidence_grade": "G1", "evidence_url": snapshot["report_url"], "attribution_basis": "official report"}]
    return payload


def add_report(payload, key, organization, *, relevance="included", grade="G1", published="2026-08-19"):
    wid, sid = "report:" + key, "source:" + key
    payload["works"].append({"work_id": wid, "title": key, "aliases": [], "abstract": "Unversioned latest report text.",
                              "authors": ["A Researcher"], "source_record_ids": [sid], "relevance": {"status": relevance},
                              "first_public_date": published, "first_public_date_precision": "day"})
    payload["source-records"].append({"source_record_id": sid, "url": "https://example.test/reports/" + key})
    payload["manifestations"].append({"manifestation_id": "manifest:" + key, "work_id": wid, "kind": "technical_report",
                                      "url": "https://example.test/reports/" + key, "published_at": published, "date_precision": "day", "source_record_id": sid})
    payload["work-organization-links"].append({"work_id": wid, "organization_id": "org:" + organization,
                                               "evidence_grade": grade, "evidence_url": "https://example.test/reports/" + key})
    return payload["works"][-1]


def by_org(result):
    return {row["organization_id"]: row for row in result["organizations"]}


class ReportCoverageTests(unittest.TestCase):
    def test_all_five_core_companies_visible_absence_means_not_registered(self):
        payload = fixture()
        before = copy.deepcopy(payload)
        result = build_report_coverage(payload, "2026-08-31")
        groups = by_org(result)
        self.assertEqual(set(groups), {"org:" + key for key in NAMES})
        self.assertEqual(groups["org:sunday-robotics"]["status"], "not_registered")
        self.assertEqual(groups["org:generalist-ai"]["counts"]["report_canonical_count"], 1)
        self.assertEqual(result["scope"]["absence_meaning"], "not_registered_not_evidence_of_no_reports")
        self.assertIsNone(result["scope"]["official_release_recall"])
        self.assertEqual(result["scope"]["recall_status"], "not_measured")
        self.assertEqual(payload, before)
        self.assertEqual(result, build_report_coverage(payload, "2026-08-31"))

    def test_canonical_dedup_across_manifestations_and_coauthors(self):
        payload = fixture()
        first = payload["manifestations"][0]
        payload["manifestations"].append({**first, "manifestation_id": "manifest:second", "url": "https://generalistai.com/report2"})
        payload["work-organization-links"].append({**payload["work-organization-links"][0], "organization_id": "org:genesis-ai"})
        payload["work-organization-links"].append(copy.deepcopy(payload["work-organization-links"][0]))
        result = build_report_coverage(payload, "2026-08-31")
        self.assertEqual(result["global_summary"]["report_canonical_count"], 1)
        self.assertEqual(result["global_summary"]["report_manifestation_count"], 2)
        for oid in ["org:generalist-ai", "org:genesis-ai"]:
            self.assertEqual(by_org(result)[oid]["counts"]["report_canonical_count"], 1)

    def test_all_relevance_strata_are_counted_separately(self):
        payload = fixture()
        for state in ["included", "candidate", "manual_review", "excluded"]:
            add_report(payload, state, "dyna-robotics", relevance=state)
        result = build_report_coverage(payload, "2026-08-31")
        dyna = by_org(result)["org:dyna-robotics"]
        self.assertEqual(dyna["counts"]["report_canonical_count"], 4)
        self.assertEqual({state: counts["report_canonical_count"] for state, counts in dyna["by_relevance"].items()}, {"included": 1, "candidate": 1, "review": 1, "excluded": 1})

    def test_g0_g3_and_invalid_g2_do_not_become_lab_facts(self):
        payload = fixture()
        for grade in ["G0", "G3", "G2"]:
            add_report(payload, grade, "figure-ai", grade=grade)
        result = build_report_coverage(payload, "2026-08-31")
        figure = by_org(result)["org:figure-ai"]
        self.assertEqual(figure["counts"]["report_canonical_count"], 0)
        self.assertEqual(len(figure["attribution_review_queue"]), 3)
        self.assertEqual(len(result["unattributed_reports"]), 3)
        self.assertTrue(all(row["urls"] and row["attribution"]["evidence_url"] for row in figure["attribution_review_queue"]))

    def test_valid_g2_needs_whole_uncertain_month_covered(self):
        payload = fixture()
        work = add_report(payload, "dated-g2", "figure-ai", grade="G2", published="2026-08-01")
        work["first_public_date_precision"] = "month"
        link = payload["work-organization-links"][-1]
        link["membership_evidence"] = {"author": "A Researcher", "source_url": "https://example.test/historical-roster", "valid_from": "2026-01-01", "valid_to": "2026-08-15"}
        self.assertEqual(by_org(build_report_coverage(payload, "2026-08-31"))["org:figure-ai"]["counts"]["report_canonical_count"], 0)
        link["membership_evidence"]["valid_to"] = "2026-08-31"
        self.assertEqual(by_org(build_report_coverage(payload, "2026-08-31"))["org:figure-ai"]["counts"]["report_canonical_count"], 1)

    def test_nvidia_root_rollup_does_not_infer_gear_or_sibling(self):
        payload = fixture()
        payload["organizations"] += [org("nvidia", tier=None, kind="company"), org("gear", kind="laboratory", parent="nvidia"), org("cosmos", kind="laboratory", parent="nvidia")]
        work = add_report(payload, "lab-report", "gear")
        add_report(payload, "parent-only", "nvidia", grade="G0")
        result = build_report_coverage(payload, "2026-08-31")
        groups = by_org(result)
        self.assertEqual(groups["org:nvidia"]["counts"]["report_canonical_count"], 1)
        self.assertEqual(groups["org:gear"]["counts"]["report_canonical_count"], 1)
        self.assertEqual(groups["org:cosmos"]["counts"]["report_canonical_count"], 0)
        root_item = groups["org:nvidia"]["reports"][0]
        self.assertEqual(root_item["work_id"], work["work_id"])
        self.assertEqual(root_item["attribution_evidence"][0]["scope"], "registered_descendant_aggregation")
        self.assertEqual(root_item["attribution_evidence"][0]["parent_path"][0]["evidence_url"], "https://example.test/organization")

    def test_parent_aggregation_respects_explicit_historical_relationship(self):
        payload = fixture()
        payload["organizations"] += [org("cmu", tier=None, kind="university"), org("lecar", kind="laboratory", parent="cmu")]
        payload["organizations"][-1]["parent_relations"][0]["valid_from"] = "2026-09-01"
        add_report(payload, "old-lab-report", "lecar")
        groups = by_org(build_report_coverage(payload, "2026-08-31"))
        self.assertEqual(groups["org:lecar"]["counts"]["report_canonical_count"], 1)
        self.assertEqual(groups["org:cmu"]["counts"]["report_canonical_count"], 0)

    def test_report_date_and_historical_text_availability_are_distinct(self):
        payload = fixture()
        result = build_report_coverage(payload, "2026-08-19", observed_through="2026-09-06")
        group = by_org(result)["org:generalist-ai"]
        self.assertEqual(group["counts"]["text_available_as_of"], 0)
        self.assertEqual(group["counts"]["text_available_current"], 1)
        self.assertEqual(group["reports"][0]["text"]["as_of"]["status"], "retrospective_only")
        self.assertFalse(group["reports"][0]["text"]["current"]["full_report_text_covered"])
        self.assertEqual(group["reports"][0]["manifestations"][0]["published_at"], "2026-08-19")

    def test_latest_unversioned_abstract_does_not_authenticate_history(self):
        payload = fixture()
        add_report(payload, "raw-body", "genesis-ai")
        group = by_org(build_report_coverage(payload, "2026-08-31"))["org:genesis-ai"]
        self.assertEqual(group["counts"]["text_unknown_current"], 1)
        self.assertEqual(group["counts"]["text_available_as_of"], 0)

    def test_valid_arxiv_abstract_is_distinguished_from_report_fulltext(self):
        payload = fixture()
        work = add_report(payload, "arxiv-report", "genesis-ai", published="2026-08-10")
        work["identifiers"] = {"arxiv": "2608.12345"}
        source = {"source_record_id": "source:arxiv", "url": "https://arxiv.org/abs/2608.12345v1"}
        payload["source-records"].append(source)
        work["source_record_ids"].append(source["source_record_id"])
        payload["text-snapshots"] = [snapshot_from_payload(work, source, {"version": "v1", "title": "Original report", "abstract": "Original abstract.", "authors": ["A Researcher"], "first_submitted": "2026-08-10", "updated": "2026-08-10"})]
        group = by_org(build_report_coverage(payload, "2026-08-31"))["org:genesis-ai"]
        self.assertEqual(group["counts"]["arxiv_abstract_available_as_of"], 1)
        self.assertEqual(group["counts"]["report_excerpt_available_as_of"], 0)
        payload["source-records"][-1]["url"] = "https://arxiv.org/abs/another-id"
        group = by_org(build_report_coverage(payload, "2026-08-31"))["org:genesis-ai"]
        self.assertEqual(group["counts"]["text_available_as_of"], 0)
        self.assertIn("arxiv_text_source_validation_failed", {gap["code"] for gap in group["reports"][0]["gaps"]})

    def test_report_observations_and_capability_facts_never_imply_independent_review(self):
        payload = fixture()
        work = add_report(payload, "robot", "dyna-robotics")
        work["evidence_flags"] = {"real_robot": True}
        groups = by_org(build_report_coverage(payload, "2026-08-31"))
        self.assertEqual(groups["org:dyna-robotics"]["counts"]["experiment_fact_work_count_as_of"], 0)
        self.assertEqual(groups["org:generalist-ai"]["counts"]["experiment_fact_work_count_as_of"], 1)
        self.assertEqual(groups["org:generalist-ai"]["counts"]["strict_peer_reviewed_current"], 0)
        work["evidence_flag_evidence"] = [{"flag": "real_robot", "value": True, "review_status": "verified",
                                          "source_url": "https://example.test/reports/robot", "source_record_ids": ["source:robot"], "public_at": "2026-08", "date_precision": "month"}]
        groups = by_org(build_report_coverage(payload, "2026-08-31"))
        fact = groups["org:dyna-robotics"]["reports"][0]["experiment_facts"]["as_of"]
        self.assertTrue(fact["has_fact"])
        self.assertEqual(fact["scope"], "source_reported_not_independent_validation")
        self.assertFalse(by_org(build_report_coverage(payload, "2026-08-20"))["org:dyna-robotics"]["reports"][0]["experiment_facts"]["as_of"]["has_fact"])

    def test_strict_peer_review_needs_dated_official_per_work_source(self):
        payload = fixture()
        work = add_report(payload, "reviewed", "figure-ai")
        work["strict_peer_reviewed"] = True
        self.assertEqual(by_org(build_report_coverage(payload, "2026-08-31"))["org:figure-ai"]["counts"]["strict_peer_reviewed_current"], 0)
        source = {"source_record_id": "source:decision", "url": "https://openreview.net/forum?id=abc"}
        payload["source-records"].append(source)
        work["source_record_ids"].append(source["source_record_id"])
        payload["manifestations"].append({"manifestation_id": "manifest:decision", "work_id": work["work_id"], "kind": "conference", "url": source["url"], "source_record_id": source["source_record_id"],
                                          "status": "accepted_official", "publication_status": "accepted_official", "peer_reviewed": True, "accepted_at": "2026-09-04", "accepted_date_precision": "day"})
        group = by_org(build_report_coverage(payload, "2026-08-31", observed_through="2026-09-06"))["org:figure-ai"]
        self.assertEqual(group["counts"]["strict_peer_reviewed_as_of"], 0)
        self.assertEqual(group["counts"]["strict_peer_reviewed_current"], 1)
        self.assertEqual(group["counts"]["report_manifestation_count"], 1)

    def test_source_unknown_failure_stale_and_partial_remain_separate(self):
        payload = fixture()
        checks = {"sources": [{"organization_id": "org:generalist-ai", "url": "https://generalist-ai.example/", "status": "healthy", "last_checked": "2026-09-06T01:00:00Z", "parser_status": "partial"},
                              {"organization_id": "org:dyna-robotics", "url": "https://dyna-robotics.example/", "status": "error", "last_checked": "2026-09-06", "consecutive_failures": 2}]}
        groups = by_org(build_report_coverage(payload, "2026-08-31", checks))
        self.assertEqual(groups["org:generalist-ai"]["source_checks"]["healthy"], 0)
        self.assertEqual(groups["org:generalist-ai"]["source_checks"]["partial"], 1)
        self.assertEqual(groups["org:dyna-robotics"]["source_checks"]["failed"], 1)
        self.assertEqual(groups["org:dyna-robotics"]["source_checks"]["stale"], 1)
        self.assertEqual(groups["org:sunday-robotics"]["source_checks"]["unknown"], 1)

    def test_clock_never_derived_from_future_publication(self):
        payload = fixture()
        add_report(payload, "future-report", "genesis-ai", published="2030-01-01")
        result = build_report_coverage(payload, "2026-08-31")
        self.assertEqual(result["current_as_of"], "2026-09-06")
        self.assertEqual(result["current_as_of_basis"], "latest_registered_observation_not_live_now")
        with self.assertRaisesRegex(ValueError, "predates"):
            build_report_coverage(payload, "2026-08-31", observed_through="2026-08-20")

    def test_future_failed_source_check_not_backdated_into_current_state(self):
        payload = fixture()
        checks = [{"organization_id": "org:dyna-robotics", "url": "https://dyna-robotics.example/", "status": "error", "last_checked": "2026-09-06", "consecutive_failures": 2}]
        group = by_org(build_report_coverage(payload, "2026-08-31", checks, observed_through="2026-08-31"))["org:dyna-robotics"]
        self.assertEqual(group["source_checks"]["failed"], 0)
        self.assertEqual(group["source_checks"]["stale"], 0)
        self.assertEqual(group["source_checks"]["unknown"], 1)
        checks.append({"organization_id": "org:dyna-robotics", "url": "https://dyna-robotics.example/", "status": "healthy", "last_checked": "2026-08-31", "consecutive_failures": 0})
        group = by_org(build_report_coverage(payload, "2026-08-31", checks, observed_through="2026-08-31"))["org:dyna-robotics"]
        self.assertEqual(group["source_checks"]["healthy"], 1)

    def test_post_merge_report_keeps_one_canonical_target(self):
        payload = fixture()
        work = payload["works"][0]
        original_id = work["work_id"]
        work.update(work_id="doi:10.example/merged", aliases=[original_id])
        payload["manifestations"][0]["work_id"] = work["work_id"]
        result = build_report_coverage(payload, "2026-08-31")
        reports = by_org(result)["org:generalist-ai"]["reports"]
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0]["work_id"], work["work_id"])
        self.assertEqual(reports[0]["text"]["as_of"]["report_snapshot_ids"], [payload["report-text-snapshots"][0]["snapshot_id"]])

    def test_t1_and_unranked_root_preserved_without_reports(self):
        payload = fixture()
        payload["organizations"] += [org("frontier", tier="T1", kind="laboratory", parent="university"), org("university", tier=None, kind="university")]
        groups = by_org(build_report_coverage(payload, "2026-08-31"))
        self.assertIn("org:frontier", groups)
        self.assertTrue(groups["org:university"]["is_root"])
        self.assertEqual(groups["org:university"]["status"], "not_registered")

    def test_known_t2_lab_outside_matrix_not_mislabeled_unattributed(self):
        payload = fixture()
        payload["organizations"].append(org("discovery-lab", tier="T2", kind="laboratory"))
        work = add_report(payload, "discovered", "discovery-lab")
        result = build_report_coverage(payload, "2026-08-31")
        self.assertNotIn("org:discovery-lab", by_org(result))
        self.assertEqual(result["global_summary"]["unattributed_report_works"], 0)
        self.assertEqual(result["global_summary"]["reliably_attributed_outside_matrix_works"], 1)
        self.assertEqual(result["outside_matrix_reports"][0]["work_id"], work["work_id"])

    def test_unknown_report_work_and_ambiguous_alias_are_not_silently_lost(self):
        payload = fixture()
        payload["manifestations"].append({"manifestation_id": "manifest:orphan", "work_id": "unknown", "kind": "technical_report", "url": "https://example.test/orphan"})
        result = build_report_coverage(payload, "2026-08-31")
        self.assertEqual(result["global_summary"]["unresolved_report_manifestations"], 1)
        self.assertEqual(result["unresolved_report_manifestations"][0]["url"], "https://example.test/orphan")

    def test_source_tampering_fails_full_report_audit(self):
        payload = fixture()
        payload["source-records"][0]["report_text_attestations"][0]["proof"]["observations_digest"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "invalid_report_archive"):
            build_report_coverage(payload, "2026-08-31")

    def test_hierarchy_cycles_rejected(self):
        payload = fixture()
        payload["organizations"] += [org("a", kind="laboratory", parent="b"), org("b", kind="laboratory", parent="a")]
        with self.assertRaisesRegex(ValueError, "organization_cycle"):
            build_report_coverage(payload, "2026-08-31")


if __name__ == "__main__":
    unittest.main()
