import copy
import json
import sqlite3
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from people_radar import (author_label_kind, build_people_radar, ingest_people_reviews,
                          load_people_authority, save_people_authority, export_people_files,
                          build_people_sqlite, audit_people_exports, people_window)
from versioned_text import snapshot_from_payload


def work(number, *, authors=None, published="2026-08-15", relevance="included", precision="day"):
    key = f"arxiv:2608.{number:05d}"
    return {"work_id": key, "title": "Research " + str(number), "abstract": "Study.",
            "authors": authors if authors is not None else ["Alex Chen"], "aliases": [],
            "identifiers": {"arxiv": key[6:]}, "source_record_ids": [],
            "relevance": {"status": relevance}, "first_public_date": published,
            "first_public_date_precision": precision, "primary_direction": "D5", "directions": ["D5", "D12"], "questions": ["Q2"]}


def person(slug="alex-chen", name="Alex Chen", ids=(1,)):
    return {"person_id": "person:" + slug, "slug": slug, "name": name,
            "identity_status": "profile_verified", "official_profiles": [{"url": "https://university.example/alex", "label": "Official homepage", "observed_at": "2026-09-06T02:00:00Z"}],
            "authorships": [{"work_id": f"arxiv:2608.{number:05d}", "status": "verified", "matched_author_name": name,
                "evidence": [{"kind": "official_publications", "url": "https://university.example/alex/publications", "work_url": f"https://arxiv.org/abs/2608.{number:05d}v1",
                              "observed_at": "2026-09-06T02:00:00Z", "statement": "The official person page links this exact work."}], "roles": None} for number in ids]}


def fixture(people=None):
    payload = {"works": [work(1), work(2)], "manifestations": [], "source-records": [], "text-snapshots": [], "work-aliases": []}
    reviews = [{"schema_version": "1", "review_id": "fixture", "people": people or [person()]}]
    return payload, reviews


def build(payload, reviews):
    authority = ingest_people_reviews(payload, reviews)
    return build_people_radar(payload, authority, "2026-09-06")


class PeopleRadarTests(unittest.TestCase):
    def test_window_uses_actual_builder_complete_months_at_month_end(self):
        from build_v3_catalog import complete_months
        for cut in ["2026-08-31", "2026-09-06", "2026-08-30", "2026-01-31", "2024-02-29", "2024-03-01"]:
            self.assertEqual(people_window(cut)["months"], complete_months(date.fromisoformat(cut), 12), cut)
        self.assertEqual(people_window("2026-08-31"), people_window("2026-09-06"))
        self.assertEqual(people_window("2026-08-31")["from"], "2025-09")
        self.assertEqual(people_window("2026-08-31")["cutoff"], "2026-08-31")

    def test_august_month_end_counts_august_without_advancing_source_cutoff(self):
        payload, reviews = fixture()
        authority = ingest_people_reviews(payload, reviews)
        result = build_people_radar(payload, authority, "2026-08-31", research_status_as_of="2026-09-06")
        self.assertEqual(result["index"]["counts"]["verified_included_works_window"], 1)
        self.assertEqual(result["index"]["window"]["to"], "2026-08")
        self.assertEqual(result["index"]["research_status_as_of"], "2026-09-06")
        self.assertEqual(result["details"]["alex-chen"]["verified_works"][0]["historical_evidence_as_of"], "2026-08-31")

    def test_verified_identity_does_not_promote_same_name_bucket(self):
        payload, reviews = fixture()
        result = build(payload, reviews)
        profile = result["details"]["alex-chen"]
        self.assertEqual(profile["metrics"]["verified_works_window"], 1)
        self.assertEqual(profile["metrics"]["candidate_works_window"], 1)
        self.assertEqual(profile["verified_work_ids"], [payload["works"][0]["work_id"]])
        self.assertEqual(len(result["tables"]["authorship-reviews"]), 1)
        self.assertEqual(profile["candidate_works"][0]["authorship_evidence"]["basis"], "exact_name_label_not_disambiguated")

    def test_no_case_or_short_name_automatic_merge(self):
        payload, reviews = fixture()
        payload["works"].extend([work(3, authors=["alex chen"]), work(4, authors=["A. Chen"]), work(5, authors=["Alex  Chen"])])
        result = build(payload, reviews)["details"]["alex-chen"]
        self.assertEqual(result["candidate_work_ids"], [payload["works"][1]["work_id"]])

    def test_explicit_alias_only_adds_candidate(self):
        payload, reviews = fixture()
        payload["works"].append(work(3, authors=["A. Chen"]))
        reviews[0]["people"][0]["aliases"] = ["A. Chen"]
        result = build(payload, reviews)["details"]["alex-chen"]
        self.assertEqual(result["metrics"]["verified_works_window"], 1)
        self.assertEqual(result["metrics"]["candidate_works_window"], 2)

    def test_same_names_remain_separate_people(self):
        payload, reviews = fixture([person(), person("alex-chen-other", ids=())])
        result = build(payload, reviews)
        self.assertEqual(result["index"]["counts"]["persons"], 2)
        self.assertEqual(result["details"]["alex-chen-other"]["metrics"]["verified_works_window"], 0)

    def test_profile_only_explicit_gap(self):
        payload, reviews = fixture([person(ids=())])
        result = build(payload, reviews)["details"]["alex-chen"]
        self.assertIn("profile_verified_but_no_verified_authorship", result["data_gaps"])
        self.assertEqual(result["metrics"]["verified_works_all"], 0)

    def test_candidate_identity_cannot_become_verified_via_work_or_name(self):
        payload, reviews = fixture([person(ids=())])
        reviews[0]["people"][0].update(identity_status="candidate", official_profiles=[])
        result = build(payload, reviews)
        self.assertEqual(result["index"]["counts"]["profile_verified_persons"], 0)
        self.assertEqual(result["index"]["counts"]["candidate_identity_persons"], 1)
        self.assertEqual(result["index"]["counts"]["verified_authorships"], 0)
        reviews[0]["people"][0]["authorships"] = person()["authorships"]
        with self.assertRaisesRegex(ValueError, "candidate_identity_cannot"):
            build(payload, reviews)

    def test_complete_month_window_and_included_only(self):
        payload, reviews = fixture([person(ids=range(1, 7))])
        payload["works"] = [work(1), work(2, published="2026-09-01"), work(3, published="2025-08-31"),
                            work(4, relevance="candidate"), work(5, precision="unknown"), work(6, published="2025-09-01")]
        result = build(payload, reviews)["details"]["alex-chen"]
        self.assertEqual(result["metrics"]["verified_works_all"], 6)
        self.assertEqual(result["metrics"]["verified_works_window"], 2)
        self.assertEqual(result["metrics"]["active_months"], 2)
        self.assertEqual(result["window"]["months"][0], "2025-09")
        self.assertEqual(result["window"]["months"][-1], "2026-08")

    def test_global_unique_canonical_and_both_verified_coauthorship(self):
        payload, reviews = fixture([person(), person("taylor-wu", "Taylor Wu")])
        payload["works"][0]["authors"] = ["Alex Chen", "Taylor Wu"]
        result = build(payload, reviews)
        self.assertEqual(result["index"]["counts"]["verified_authorships"], 2)
        self.assertEqual(result["index"]["counts"]["verified_included_works_window"], 1)
        self.assertEqual(len(result["index"]["coauthorships"]), 1)
        reviews[0]["people"][1]["authorships"] = []
        self.assertEqual(build(payload, reviews)["index"]["coauthorships"], [])

    def test_primary_direction_counts_not_multi_tag_double_count(self):
        payload, reviews = fixture()
        counts = {row["code"]: row["count"] for row in build(payload, reviews)["details"]["alex-chen"]["directions"]}
        self.assertEqual(counts["D5"], 1)
        self.assertEqual(counts["D12"], 0)
        self.assertEqual(sum(counts.values()), 1)

    def test_official_source_and_hard_work_link_required(self):
        payload, reviews = fixture()
        reviews[0]["people"][0]["authorships"][0]["evidence"][0]["work_url"] = "https://arxiv.org/abs/2608.99999"
        with self.assertRaisesRegex(ValueError, "work_url_mismatch"):
            build(payload, reviews)
        reviews[0]["people"][0]["authorships"][0]["evidence"] = []
        with self.assertRaisesRegex(ValueError, "evidence_required"):
            build(payload, reviews)

    def test_alias_hard_id_resolves_after_canonical_merge(self):
        payload, reviews = fixture()
        old = payload["works"][0]["work_id"]
        payload["works"][0].update(work_id="doi:10.1234/research", aliases=[old])
        result = build(payload, reviews)["details"]["alex-chen"]
        self.assertEqual(result["verified_work_ids"], ["doi:10.1234/research"])

    def test_existing_authority_alias_resolves_without_rewriting_authority(self):
        payload, reviews = fixture()
        authority = ingest_people_reviews(payload, reviews)
        old = payload["works"][0]["work_id"]
        payload["works"][0].update(work_id="doi:10.1234/research", aliases=[old])
        before = copy.deepcopy(authority)
        result = build_people_radar(payload, authority, "2026-09-06")
        self.assertEqual(result["details"]["alex-chen"]["verified_work_ids"], ["doi:10.1234/research"])
        self.assertEqual(authority, before)
        self.assertEqual(result["tables"], authority)
        self.assertEqual(ingest_people_reviews(payload, reviews, authority), authority)
        connection = sqlite3.connect(":memory:")
        build_people_sqlite(connection, result)
        self.assertEqual(connection.execute("SELECT work_id,canonical_work_id FROM people_authorship_reviews").fetchone(), (old, "doi:10.1234/research"))
        connection.close()

    def test_ambiguous_alias_and_unknown_work_rejected(self):
        payload, reviews = fixture()
        payload["works"][1]["aliases"] = [payload["works"][0]["work_id"]]
        with self.assertRaisesRegex(ValueError, "identity_unresolved"):
            build(payload, reviews)

    def test_shared_project_homepage_is_not_unique_work_evidence(self):
        payload, reviews = fixture()
        shared = "https://lab.example/projects"
        payload["manifestations"] = [{"manifestation_id": str(index), "work_id": w["work_id"], "kind": "project", "url": shared} for index, w in enumerate(payload["works"])]
        reviews[0]["people"][0]["authorships"][0]["evidence"][0]["work_url"] = shared
        with self.assertRaisesRegex(ValueError, "work_url_ambiguous"):
            build(payload, reviews)

    def test_raw_collective_punctuation_not_people_or_contribution(self):
        payload, reviews = fixture()
        payload["works"][0]["authors"] = ["NVIDIA", ":", "Alex Chen", "Member IEEE"]
        row = build(payload, reviews)["details"]["alex-chen"]["verified_works"][0]
        self.assertEqual(row["raw_authors"], payload["works"][0]["authors"])
        self.assertEqual([item["kind"] for item in row["author_labels"]], ["collective_or_organization", "punctuation_or_empty", "unresolved_person_label", "metadata_contamination"])
        self.assertIsNone(row["roles"])
        reviews[0]["people"][0]["name"] = "NVIDIA"
        with self.assertRaisesRegex(ValueError, "person_name_required"):
            build(payload, reviews)

    def test_roles_unknown_citations_adoption_projects_not_fabricated(self):
        payload, reviews = fixture()
        metrics = build(payload, reviews)["details"]["alex-chen"]["metrics"]
        for key in ["citations", "adoption", "independent_projects", "role_verified_work_count"]:
            self.assertIsNone(metrics[key])
        reviews[0]["people"][0]["authorships"][0]["roles"] = ["first_author"]
        with self.assertRaisesRegex(ValueError, "contribution_roles"):
            build(payload, reviews)

    def test_future_peer_review_not_backdated_and_report_count_canonical(self):
        payload, reviews = fixture()
        wid = payload["works"][0]["work_id"]
        payload["manifestations"] = [{"work_id": wid, "manifestation_id": "peer", "kind": "conference", "url": "https://proceedings.example/paper", "peer_reviewed": True, "published_at": "2026-09-02", "date_precision": "day"},
                                      *[{"work_id": wid, "manifestation_id": "report" + str(i), "kind": "technical_report", "url": f"https://lab.example/report{i}", "published_at": "2026-08-16", "date_precision": "day"} for i in range(2)]]
        metrics = build(payload, reviews)["details"]["alex-chen"]["metrics"]
        self.assertEqual(metrics["peer_reviewed_window"], 0)
        self.assertEqual(metrics["technical_reports_window"], 1)

    def test_explicit_source_role_preserves_project_not_paper_contribution(self):
        payload, reviews = fixture()
        link = reviews[0]["people"][0]["authorships"][0]
        evidence = link["evidence"][0]
        link["roles"] = [{"role": "project_lead", "scope": "project", "source_url": evidence["url"],
                          "work_url": evidence["work_url"], "observed_at": evidence["observed_at"],
                          "statement": "Official project credits explicitly label Alex Chen as project lead."}]
        result = build(payload, reviews)["details"]["alex-chen"]
        self.assertEqual(result["metrics"]["role_verified_work_count"], 1)
        self.assertEqual(result["verified_works"][0]["roles"][0]["scope"], "project")
        link["roles"][0]["source_url"] = "https://unread.example/guess"
        with self.assertRaisesRegex(ValueError, "roles_source_unchecked"):
            build(payload, reviews)

    def test_historical_version_authors_not_current_canonical_union(self):
        payload, reviews = fixture()
        w = payload["works"][0]
        source = {"source_record_id": "source:text", "url": "https://arxiv.org/abs/2608.00001v1"}
        w["source_record_ids"] = [source["source_record_id"]]
        payload["source-records"] = [source]
        for version, when, authors in [("v1", "2026-08-15", ["Alex Chen", "Original Coauthor"]), ("v2", "2026-09-02", ["Future Coauthor"])]:
            payload["text-snapshots"].append(snapshot_from_payload(w, source, {"version": version, "title": w["title"], "abstract": "Study.", "authors": authors, "first_submitted": "2026-08-15", "updated": when}))
        w["authors"] = ["NVIDIA", ":", "Alex Chen", "Future Coauthor"]
        row = build(payload, reviews)["details"]["alex-chen"]["verified_works"][0]
        self.assertEqual(row["version_authorship"]["authors"], ["Alex Chen", "Original Coauthor"])
        self.assertEqual(row["version_authorship"]["version"], "v1")
        self.assertEqual(row["raw_authors"], w["authors"])
        self.assertEqual(row["authorship_version_match"], "exact_label_present")

    def test_versioned_source_candidate_survives_current_author_array_loss(self):
        payload, reviews = fixture([person(ids=())])
        w = payload["works"][0]
        source = {"source_record_id": "source:text", "url": "https://arxiv.org/abs/2608.00001v1"}
        w["source_record_ids"] = [source["source_record_id"]]
        payload["source-records"] = [source]
        payload["text-snapshots"] = [snapshot_from_payload(w, source, {"version": "v1", "title": w["title"], "abstract": "Study.", "authors": ["Alex Chen"], "first_submitted": "2026-08-15", "updated": "2026-08-15"})]
        w["authors"] = []
        profile = build(payload, reviews)["details"]["alex-chen"]
        self.assertIn(w["work_id"], profile["candidate_work_ids"])
        self.assertEqual(profile["metrics"]["verified_works_window"], 0)

    def test_unknown_historical_authors_not_silently_filled(self):
        payload, reviews = fixture()
        row = build(payload, reviews)["details"]["alex-chen"]["verified_works"][0]
        self.assertEqual(row["version_authorship"]["status"], "unavailable")
        self.assertEqual(row["version_authorship"]["authors"], [])
        self.assertEqual(row["raw_authors"], ["Alex Chen"])

    def test_organization_role_keeps_unknown_history_without_work_attribution(self):
        payload, reviews = fixture()
        reviews[0]["people"][0]["official_roles"] = [{"organization_id": None, "organization_name": "University", "title": "Professor", "valid_from": None, "valid_to": None, "source_url": "https://university.example/alex", "observed_at": "2026-09-06T02:00:00Z"}]
        result = build(payload, reviews)
        role = result["details"]["alex-chen"]["official_roles"][0]
        self.assertIsNone(role["valid_from"])
        self.assertEqual(role["basis"], "official_role_not_historical_work_affiliation")
        self.assertNotIn("work-organization-links", payload)

    def test_idempotent_ingest_atomic_conflict_and_inputs_unchanged(self):
        payload, reviews = fixture()
        original = copy.deepcopy((payload, reviews))
        authority = ingest_people_reviews(payload, reviews)
        self.assertEqual(ingest_people_reviews(payload, reviews, authority), authority)
        self.assertEqual((payload, reviews), original)
        before = copy.deepcopy(authority)
        reviews[0]["people"][0]["name"] = "Different Person"
        with self.assertRaisesRegex(ValueError, "authority_conflict"):
            ingest_people_reviews(payload, reviews, authority)
        self.assertEqual(authority, before)

    def test_utc_and_safe_slug_validation(self):
        payload, reviews = fixture()
        reviews[0]["people"][0]["official_profiles"][0]["observed_at"] = "2026-09-06"
        with self.assertRaisesRegex(ValueError, "utc_required"):
            build(payload, reviews)
        reviews[0]["people"][0]["slug"] = "../other"
        with self.assertRaisesRegex(ValueError, "slug_invalid"):
            build(payload, reviews)

    def test_jsonl_sqlite_api_exact_audit_and_tamper(self):
        payload, reviews = fixture()
        authority = ingest_people_reviews(payload, reviews)
        result = build_people_radar(payload, authority, "2026-09-06")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            save_people_authority(root / "authority", authority)
            self.assertEqual(load_people_authority(root / "authority"), authority)
            export_people_files(result, root / "api", root / "downloads")
            connection = sqlite3.connect(":memory:")
            build_people_sqlite(connection, result)
            self.assertEqual(audit_people_exports(result, root / "api", root / "downloads", connection)["status"], "passed")
            connection.execute("DELETE FROM people_authorship_reviews")
            self.assertIn("people_sqlite_mismatch:authorship-reviews", audit_people_exports(result, root / "api", root / "downloads", connection)["errors"])
            connection.close()

    def test_source_change_invalidates_people_version(self):
        payload, reviews = fixture()
        old = build(payload, reviews)["index"]["dataset_version"]
        reviews[0]["people"][0]["authorships"][0]["evidence"][0]["statement"] = "More precise source check."
        self.assertNotEqual(build(payload, reviews)["index"]["dataset_version"], old)
        old = build(payload, reviews)["index"]["dataset_version"]
        payload["works"][1]["title"] = "Corrected candidate title"
        self.assertNotEqual(build(payload, reviews)["index"]["dataset_version"], old)

    def test_citation_measurements_require_full_same_provider_date_coverage(self):
        payload, reviews = fixture([person(ids=(1, 2))])
        record = {"dimension": "citation_count", "work_id": "arxiv:2608.00001", "work_url": "https://arxiv.org/abs/2608.00001",
                  "source_url": "https://citations.example/record1", "observed_at": "2026-09-06T02:00:00Z", "as_of": "2026-09-05",
                  "review_status": "verified", "provider": "example-index", "count": 3, "statement": "Source-bound count for this work, not unique authors or citations across works."}
        reviews[0]["people"][0]["influence_evidence"] = [record]
        metrics = build(payload, reviews)["details"]["alex-chen"]["metrics"]
        self.assertIsNone(metrics["citations"])
        self.assertEqual(metrics["citation_coverage"]["measured_works"], 1)
        reviews[0]["people"][0]["influence_evidence"].append({**record, "work_id": "arxiv:2608.00002", "work_url": "https://arxiv.org/abs/2608.00002", "count": 4})
        self.assertEqual(build(payload, reviews)["details"]["alex-chen"]["metrics"]["citations"], 7)
        reviews[0]["people"][0]["influence_evidence"][1]["as_of"] = "2026-09-04"
        self.assertIsNone(build(payload, reviews)["details"]["alex-chen"]["metrics"]["citations"])

    def test_independent_adoption_requires_reviewed_external_source_not_coauthor(self):
        payload, reviews = fixture()
        record = {"dimension": "independent_adoption", "work_id": "arxiv:2608.00001", "work_url": "https://arxiv.org/abs/2608.00001",
                  "source_url": "https://adopter.example/implementation", "observed_at": "2026-09-06T02:00:00Z", "as_of": "2026-09-05",
                  "review_status": "verified", "statement": "External implementation explicitly cites and uses the work."}
        reviews[0]["people"][0]["influence_evidence"] = [record]
        with self.assertRaisesRegex(ValueError, "independence_source_required"):
            build(payload, reviews)
        record.update(independent_team=True, independence_statement="The named implementer is an independent team, source-checked.",
                      independence_source_url="https://adopter.example/team", adopter_name="External Team")
        metrics = build(payload, reviews)["details"]["alex-chen"]["metrics"]
        self.assertEqual(metrics["adoption"], 1)
        self.assertIsNone(metrics["independent_replication_works_window"])
        record["review_status"] = "draft"
        self.assertIsNone(build(payload, reviews)["details"]["alex-chen"]["metrics"]["adoption"])

    def test_conflicting_citation_snapshot_rejected_before_authority_write(self):
        payload, reviews = fixture()
        record = {"dimension": "citation_count", "work_id": "arxiv:2608.00001", "work_url": "https://arxiv.org/abs/2608.00001",
                  "source_url": "https://citations.example/record1", "observed_at": "2026-09-06T02:00:00Z", "as_of": "2026-09-05",
                  "review_status": "verified", "provider": "example-index", "count": 3, "statement": "Measured count."}
        reviews[0]["people"][0]["influence_evidence"] = [record, {**record, "count": 9}]
        with self.assertRaisesRegex(ValueError, "conflicting_citation"):
            ingest_people_reviews(payload, reviews)

    def test_current_withdrawal_blocks_validation_and_adoption_preserves_history(self):
        payload, reviews = fixture()
        w = payload["works"][0]
        sid, url, published = "source:notice", "https://arxiv.org/abs/2608.00001v3", "2026-09-05T01:00:00Z"
        w["source_record_ids"] = [sid]
        w["research_status_notices"] = [{"notice_id": "notice:withdrawn", "work_id": w["work_id"], "event_type": "withdrawn", "scope": "work",
            "public_at": published, "date_precision": "second", "review_status": "verified", "source_record_ids": [sid], "source_url": url, "summary_zh": "合成撤回通知"}]
        payload["source-records"] = [{"source_record_id": sid, "url": url, "source_type": "official_arxiv_status_notice", "published_at": published,
                                      "observed_at": "2026-09-06T02:00:00Z", "raw": {"work_id": w["work_id"]}}]
        payload["manifestations"] = [{"work_id": w["work_id"], "manifestation_id": "peer", "kind": "conference", "url": "https://conference.example/paper",
                                      "peer_reviewed": True, "published_at": "2026-08-20", "date_precision": "day"}]
        reviews[0]["people"][0]["influence_evidence"] = [{"dimension": "independent_adoption", "work_id": w["work_id"], "work_url": "https://arxiv.org/abs/2608.00001",
            "source_url": "https://adopter.example/project", "observed_at": "2026-09-06T02:00:00Z", "as_of": "2026-09-04", "review_status": "verified",
            "statement": "Source checked adoption before withdrawal.", "adopter_name": "External Team", "independent_team": True,
            "independence_statement": "Official independent team source.", "independence_source_url": "https://adopter.example/team"}]
        before = copy.deepcopy(payload)
        authority = ingest_people_reviews(payload, reviews)
        profile = build_people_radar(payload, authority, "2026-09-01")["details"]["alex-chen"]
        row = profile["verified_works"][0]
        self.assertEqual(row["research_status"]["status"], "withdrawn")
        self.assertEqual(row["research_status"]["as_of"], "2026-09-06")
        self.assertEqual(row["historical_evidence_as_of"], "2026-08-31")
        self.assertTrue(row["historical_evidence"]["strict_peer_reviewed"])
        self.assertFalse(row["strict_peer_reviewed"])
        self.assertEqual(profile["metrics"]["peer_reviewed_window"], 0)
        self.assertEqual(profile["metrics"]["historical_peer_reviewed_window"], 1)
        self.assertEqual(profile["metrics"]["verified_works_window"], 1)
        self.assertIsNone(profile["metrics"]["adoption"])
        self.assertEqual(len(profile["influence_evidence"]), 1)
        self.assertEqual(payload, before)

    def test_additional_official_role_requires_literal_label_and_exact_source(self):
        payload, reviews = fixture()
        link = reviews[0]["people"][0]["authorships"][0]
        evidence = link["evidence"][0]
        link["roles"] = [{"role": "supervision", "label": "Project Direction and Guidance", "scope": "project", "source_url": evidence["url"],
                          "work_url": evidence["work_url"], "observed_at": evidence["observed_at"], "statement": "Official contribution list directly names this person in this role."}]
        row = build(payload, reviews)["details"]["alex-chen"]["verified_works"][0]
        self.assertEqual(row["roles"][0]["role"], "supervision")
        self.assertEqual(row["roles"][0]["label"], "Project Direction and Guidance")
        del link["roles"][0]["label"]
        with self.assertRaisesRegex(ValueError, "official_label_required"):
            build(payload, reviews)

    def test_staging_schema_matches_fixture(self):
        from jsonschema import Draft202012Validator
        _, reviews = fixture()
        schema = json.loads((ROOT / "config/people-review.schema.json").read_text())
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(reviews[0])

    def test_no_people_remains_honest_empty_index(self):
        payload, _ = fixture()
        result = build_people_radar(payload, load_people_authority(Path("/nonexistent-people-fixture")), "2026-09-06")
        self.assertEqual(result["index"]["counts"]["persons"], 0)
        self.assertEqual(result["index"]["people"], [])


if __name__ == "__main__":
    unittest.main()
