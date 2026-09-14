import copy
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from catalog_store import fingerprint
import import_people_candidate_reviews as importer
from import_people_candidate_reviews import (apply_candidate_reviews, capture_cohort, merge_results,
                                            normalize_result, validate_cohort_scope)
from people_radar import build_people_radar, ingest_people_reviews
from test_people_radar import fixture


def sample():
    payload, reviews = fixture()
    authority = ingest_people_reviews(payload, reviews)
    candidate = {"person_id": "person:alex-chen", "work_id": "arxiv:2608.00002", "matched_author_name": "Alex Chen", "in_complete_window": True}
    cohort = {"cohort_id": fingerprint([candidate]), "authority_hash": fingerprint(authority), "rows": [candidate]}
    raw = {**candidate, "status": "verified", "reason": "官方个人论文条目中硬链接和作者一致。", "kind": "official_publications", "observed_at": "2026-09-09T01:00:00Z", "source_url": "https://university.example/alex/publications", "work_url": "https://arxiv.org/abs/2608.00002", "matched_link": "https://arxiv.org/abs/2608.00002"}
    return payload, authority, cohort, raw


class CandidateReviewTests(unittest.TestCase):
    def window_sample(self):
        payload, authority, cohort, raw = sample()
        cohort["scope"] = "window"
        raw.update(author_profile_url="https://university.example/alex", matched_author_name="Alex Chen",
                   locator="article.publication > a.paper", source_scope="official_project_author_block")
        return payload, authority, cohort, raw

    def api_fixture(self, folder):
        index = {"people": [{"slug": "alex-chen", "person_id": "person:alex-chen"}], "review_hash": "authority", "dataset_version": "data",
                 "window": {"cutoff": "2026-08-31", "months": ["2025-09", "2025-10", "2025-11", "2025-12",
                    "2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07", "2026-08"]}}
        detail = {"person_id": "person:alex-chen", "review_hash": "authority", "dataset_version": "data", "candidate_works": [
            {"work_id": "arxiv:2608.00002", "in_complete_window": True, "authorship_evidence": {"matched_author_name": "Alex Chen"}},
            {"work_id": "arxiv:2408.00003", "in_complete_window": False, "authorship_evidence": {"matched_author_name": "Alex Chen"}}]}
        (folder / "index.json").write_text(json.dumps(index))
        (folder / "alex-chen.json").write_text(json.dumps(detail))
        return index, detail

    def test_capture_window_only_true_flags_and_default_all_unchanged(self):
        with tempfile.TemporaryDirectory() as path:
            folder = Path(path)
            index, _ = self.api_fixture(folder)
            all_cohort = capture_cohort(folder)
            self.assertEqual(len(all_cohort["rows"]), 2)
            self.assertNotIn("scope", all_cohort)
            self.assertEqual(all_cohort, capture_cohort(folder, "all"))
            window = capture_cohort(folder, "window")
            self.assertEqual(len(window["rows"]), 1)
            self.assertTrue(window["rows"][0]["in_complete_window"])
            self.assertEqual(window["window"], index["window"])
            self.assertEqual(window["cohort_id"], fingerprint(window["rows"]))

    def test_saved_scope_cannot_expand_or_mix_window(self):
        *_, cohort, _ = self.window_sample()
        with self.assertRaisesRegex(ValueError, "scope_mismatch"):
            validate_cohort_scope(cohort, "all")
        cohort["rows"][0]["in_complete_window"] = False
        with self.assertRaisesRegex(ValueError, "outside_row"):
            validate_cohort_scope(cohort, "window")
        cohort["rows"][0]["in_complete_window"] = True
        cohort["cohort_id"] = "changed"
        with self.assertRaisesRegex(ValueError, "hash_mismatch"):
            validate_cohort_scope(cohort, "window")

    def test_window_capture_rejects_mixed_versions_and_missing_window(self):
        with tempfile.TemporaryDirectory() as path:
            folder = Path(path)
            index, detail = self.api_fixture(folder)
            detail["review_hash"] = "changed"
            (folder / "alex-chen.json").write_text(json.dumps(detail))
            with self.assertRaisesRegex(ValueError, "mixed_versions"):
                capture_cohort(folder, "window")
            detail["review_hash"] = "authority"
            (folder / "alex-chen.json").write_text(json.dumps(detail))
            index.pop("window")
            (folder / "index.json").write_text(json.dumps(index))
            with self.assertRaisesRegex(ValueError, "twelve_month"):
                capture_cohort(folder, "window")

    def test_result_alias_and_nested_evidence_are_preserved(self):
        *_, raw = self.window_sample()
        raw["result"] = raw.pop("status")
        raw["evidence"] = [{"linked_url": raw["matched_link"], "locator": "article.publication",
                            "structure": {"author_link": {"text": "Alex Chen", "href": "https://university.example/alex"}},
                            "identity_bridge": {"author_name": "Alex Chen", "linked_url": "https://university.example/alex"},
                            "source_sha256": "a" * 64}]
        raw["checked_sources"] = ["https://university.example/check"]
        row = normalize_result(raw)
        self.assertEqual(row["result"], "verified")
        self.assertEqual(row["evidence"][0]["structure"], raw["evidence"][0]["structure"])
        self.assertEqual(row["evidence"][0]["identity_bridge"], raw["evidence"][0]["identity_bridge"])
        self.assertEqual(row["evidence"][0]["source_sha256"], "a" * 64)
        self.assertIn("https://university.example/check", row["checked_sources"])
        raw["status"] = "unresolved"
        with self.assertRaisesRegex(ValueError, "conflicting_resolution"):
            normalize_result(raw)

    def test_window_requires_identity_anchor_entry_and_actual_work_link(self):
        for missing, error in [("author_profile_url", "author_profile_anchor"), ("locator", "entry_locator"),
                               ("matched_link", "actual_work_link"), ("matched_author_name", "explicit_author_anchor")]:
            payload, authority, cohort, raw = self.window_sample()
            raw.pop(missing)
            with self.subTest(missing=missing), self.assertRaisesRegex(ValueError, error):
                apply_candidate_reviews(payload, authority, cohort, [normalize_result(raw)], "window")

    def test_window_unknown_profile_requires_explicit_identity_bridge(self):
        payload, authority, cohort, raw = self.window_sample()
        raw["author_profile_url"] = "https://alex.example/"
        raw["evidence"] = [{"linked_url": raw["matched_link"], "identity_chain": [{
            "source_url": "https://university.example/alex", "statement": "This is Alex's homepage."}]}]
        with self.assertRaisesRegex(ValueError, "identity_bridge_not_verified"):
            apply_candidate_reviews(payload, authority, cohort, [normalize_result(raw)], "window")
        cohort["identity_bridges"] = [{"person_id": "person:alex-chen", "source_url": "https://university.example/alex",
            "linked_url": "https://alex.example/", "locator": "Homepage field", "observed_at": "2026-09-14T00:00:00Z"}]
        result = apply_candidate_reviews(payload, authority, cohort, [normalize_result(raw)], "window")
        self.assertEqual(next(x for x in result["authorship-reviews"] if x["work_id"] == raw["work_id"])["status"], "verified")

    def test_window_never_accepts_wrong_person_name_or_reference_scope(self):
        for field, value, message in [("matched_author_name", "Other Person", "name_mismatch"),
                                      ("source_scope", "bibliography", "non_primary_scope")]:
            payload, authority, cohort, raw = self.window_sample()
            raw[field] = value
            with self.assertRaisesRegex(ValueError, message):
                apply_candidate_reviews(payload, authority, cohort, [normalize_result(raw)], "window")

    def test_window_review_leaves_outside_pairs_and_person_tables_equal(self):
        payload, authority, cohort, raw = self.window_sample()
        before = copy.deepcopy(authority)
        updated = apply_candidate_reviews(payload, authority, cohort, [normalize_result(raw)], "window")
        for table in ("persons", "organization-links", "influence-evidence"):
            self.assertEqual(updated[table], before[table])
        self.assertIn(before["authorship-reviews"][0], updated["authorship-reviews"])
        self.assertEqual(apply_candidate_reviews(payload, updated, cohort, [normalize_result(raw)], "window"), updated)

    def test_explicit_same_entry_manifestation_bridge_preserves_actual_link(self):
        payload, authority, cohort, raw = self.window_sample()
        original_id = raw["work_id"]
        wid = "doi:10.1126/scirobotics.example"
        payload["works"][1].update(work_id=wid, identifiers={"doi": wid[4:]}, aliases=[])
        cohort["rows"][0]["work_id"] = wid
        cohort["cohort_id"] = fingerprint(cohort["rows"])
        raw["work_id"] = wid
        raw["evidence"] = [{"linked_url": raw["matched_link"], "manifestation_identity_bridge": {
            "source_url": "https://coauthor.example/", "locator": "article#publication",
            "linked_url": "https://www.science.org/doi/10.1126/scirobotics.example",
            "same_entry_arxiv": raw["matched_link"]}}]
        rows = [normalize_result(raw)]
        self.assertEqual(rows[0]["evidence"][0]["linked_url"], raw["matched_link"])
        self.assertEqual(rows[0]["evidence"][0]["work_url"], "https://doi.org/10.1126/scirobotics.example")
        before = copy.deepcopy(payload)
        updated = apply_candidate_reviews(payload, authority, cohort, rows, "window")
        self.assertEqual(payload, before)
        self.assertNotIn(original_id, payload["works"][1]["aliases"])
        self.assertEqual(updated["authorship-reviews"][-1]["status"], "verified")
        raw["evidence"][0]["manifestation_identity_bridge"]["same_entry_arxiv"] = "https://arxiv.org/abs/9999.99999"
        with self.assertRaisesRegex(ValueError, "identifier_mismatch"):
            normalize_result(raw)

    def test_window_cli_reuses_locked_baseline_without_recapturing_api(self):
        payload, authority, cohort, raw = self.window_sample()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            batch = root / "data/people/candidate-audits/window-test"
            batch.mkdir(parents=True)
            (batch / "baseline.json").write_text(json.dumps(cohort))
            source = root / "review.json"
            source.write_text(json.dumps({"results": [raw]}))
            before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
            args = ["--input", str(source), "--batch", "window-test", "--scope", "window"]
            with patch.object(importer, "ROOT", root), patch.object(importer, "load_catalog", return_value=(payload, {})), \
                    patch.object(importer, "load_people_authority", return_value=authority), \
                    patch.object(importer, "capture_cohort", side_effect=AssertionError("must not recapture")), \
                    contextlib.redirect_stdout(io.StringIO()) as output:
                importer.main(args)
            self.assertEqual(json.loads(output.getvalue())["scope"], "window")
            self.assertEqual({p: p.read_bytes() for p in root.rglob("*") if p.is_file()}, before)

    def test_verified_candidate_added_without_touching_previous_work_or_person(self):
        payload, authority, cohort, raw = sample()
        before = copy.deepcopy(authority)
        result = apply_candidate_reviews(payload, authority, cohort, [normalize_result(raw)], "test-batch")
        self.assertEqual(authority, before)
        self.assertEqual(result["persons"], before["persons"])
        self.assertIn(before["authorship-reviews"][0], result["authorship-reviews"])
        view = build_people_radar(payload, result, "2026-09-06")
        person = view["details"]["alex-chen"]
        self.assertEqual(person["metrics"]["verified_works_window"], 2)
        self.assertEqual(person["candidate_review"]["confirmed"], 1)
        self.assertEqual(person["candidate_review"]["checked"], 1)

    def test_unresolved_records_keep_reason_and_do_not_count_as_verified(self):
        payload, authority, cohort, raw = sample()
        raw.update(status="unresolved", reason="官网缺少硬链接，不能判定是同一人。")
        result = apply_candidate_reviews(payload, authority, cohort, [normalize_result(raw)], "test-batch")
        person = build_people_radar(payload, result, "2026-09-06")["details"]["alex-chen"]
        self.assertEqual(person["metrics"]["verified_works_window"], 1)
        self.assertEqual(person["candidate_review"]["unresolved"], 1)
        self.assertEqual(person["candidate_works"][0]["authorship_evidence"]["verification_audit"]["reason"], raw["reason"])

    def test_replaying_legacy_review_staging_preserves_new_audit_annotations(self):
        payload, reviews = fixture()
        reviews[0]["people"][0]["authorships"].append({"work_id": "arxiv:2608.00002", "status": "candidate", "matched_author_name": "Alex Chen", "evidence": [], "roles": None})
        authority = ingest_people_reviews(payload, reviews)
        _, _, cohort, raw = sample()
        cohort["authority_hash"] = fingerprint(authority)
        raw.update(status="unresolved", reason="待补直接标识。")
        result = apply_candidate_reviews(payload, authority, cohort, [normalize_result(raw)], "test-batch")
        self.assertEqual(ingest_people_reviews(payload, reviews, result), result)

    def test_repeated_import_is_idempotent(self):
        payload, authority, cohort, raw = sample()
        rows = [normalize_result(raw)]
        first = apply_candidate_reviews(payload, authority, cohort, rows, "test-batch")
        self.assertEqual(apply_candidate_reviews(payload, first, cohort, rows, "test-batch"), first)

    def test_cohort_must_be_complete_and_cannot_accept_foreign_pairs(self):
        payload, authority, cohort, raw = sample()
        for rows in [[], [normalize_result(raw)] * 2, [normalize_result({**raw, "person_id": "person:other"})]]:
            with self.assertRaisesRegex(ValueError, "cohort_missing_extra_or_duplicate"):
                apply_candidate_reviews(payload, authority, cohort, rows, "test-batch")

    def test_wrong_work_link_and_unresolved_identity_fail_closed(self):
        payload, authority, cohort, raw = sample()
        raw.update(work_url="https://arxiv.org/abs/2608.99999", matched_link="https://arxiv.org/abs/2608.99999")
        with self.assertRaisesRegex(ValueError, "work_url_mismatch"):
            apply_candidate_reviews(payload, authority, cohort, [normalize_result(raw)], "test-batch")
        payload, authority, cohort, raw = sample()
        authority["authorship-reviews"] = []
        authority["persons"][0]["identity_status"] = "candidate"
        cohort["authority_hash"] = fingerprint(authority)
        with self.assertRaisesRegex(ValueError, "candidate_identity_cannot"):
            apply_candidate_reviews(payload, authority, cohort, [normalize_result(raw)], "test-batch")

    def test_title_only_match_is_not_a_hard_identity_link(self):
        *_, raw = sample()
        row = normalize_result({**raw, "match_basis": "exact_title_and_explicit_author_in_own_official_publication_entry", "matched_link": None})
        self.assertEqual(row["result"], "unresolved")
        self.assertEqual(row["evidence"], [])

    def test_distinct_official_program_fragments_are_not_one_shared_work_identity(self):
        from people_radar import _hard_identity
        base = "https://conference.example/program.html"
        self.assertNotEqual(_hard_identity(base + "#paper1"), _hard_identity(base + "#paper2"))

    def test_source_link_can_be_an_arxiv_manifestation_of_a_doi_canonical(self):
        payload, authority, cohort, raw = sample()
        wid = "doi:10.1234/example"
        payload["works"][1].update(work_id=wid, aliases=[raw["work_id"]])
        cohort["rows"][0]["work_id"] = wid
        raw.update(work_id=wid, work_url="https://doi.org/10.1234/example")
        result = apply_candidate_reviews(payload, authority, cohort, [normalize_result(raw)], "test-batch")
        self.assertEqual(next(r for r in result["authorship-reviews"] if r["work_id"] == wid)["evidence"][0]["work_url"], "https://arxiv.org/abs/2608.00002")

    def test_supplementary_project_can_resolve_gap_but_cannot_remove_a_verified_result(self):
        *_, raw = sample()
        unresolved = {**raw, "status": "unresolved", "reason": "官网暂不可用。"}
        merged = merge_results([unresolved, raw, unresolved])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["result"], "verified")

    def test_stale_authority_is_not_silently_overwritten(self):
        payload, authority, cohort, raw = sample()
        authority["persons"][0]["notes"] = ["Another source edit."]
        with self.assertRaisesRegex(ValueError, "stale_authority_cohort"):
            apply_candidate_reviews(payload, authority, cohort, [normalize_result(raw)], "test-batch")


if __name__ == "__main__":
    unittest.main()
