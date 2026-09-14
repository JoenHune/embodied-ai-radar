import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_release_recall import audit_release_recall, normalize_url, validate_gold, recall_gate


def release(number=1, **extra):
    url = f"https://lab.example/research/{number}"
    return {"gold_id": f"g:{number}", "record_type": "release", "organization_id": "org:lab", "title": f"Robot research {number}",
            "url": url, "equivalent_urls": [url], "index_url": "https://lab.example/research", "release_type": "paper",
            "frozen_at": "2026-09-06T00:00:00Z", "published_at": "2026-01-01", "published_at_precision": "day",
            "window": {"from": "2025-09-01", "to": "2026-08-31"}, "sampling_frame_id": "independent-v1", "selection_basis": "source_first",
            "provenance": [{"role": "release_page", "source_url": url, "effective_url": url, "status": "captured", "sha256": "a" * 64,
                            "hash_scope": "http_response_body_bytes", "excerpt": f"Robot research {number}"}], **extra}


def catalog(works=None, manifestations=None, sources=None):
    return {"works": works or [], "manifestations": manifestations or [], "source-records": sources or []}


def work(wid="w:1", status="included", title="Robot research 1", sources=None):
    return {"work_id": wid, "title": title, "relevance": {"status": status}, "source_record_ids": sources or [], "identifiers": {}}


class ReleaseRecallTest(unittest.TestCase):
    def test_release_receipt_without_manifestation_fails_regression_gate(self):
        sample = [release()]
        db = catalog([work(sources=["s"])], sources=[{"source_record_id": "s", "url": release()["url"]}])
        report = audit_release_recall(sample, db)
        policy = {"version": "1", "scope": report["scope"], "gold_hash": report["gold_hash"],
                  "minimum_sampled_organizations": 1, "minimum_research_releases": 1, "minimum_manifestation_link_recall": .95}
        self.assertEqual(report["overall"]["release_capture_recall"], 1)
        self.assertEqual(recall_gate(report, policy)["status"], "failed")
        db["manifestations"].append({"work_id": "w:1", "url": release()["url"]})
        report = audit_release_recall(sample, db)
        self.assertEqual(recall_gate(report, policy)["status"], "passed")
        # Removing a difficult sample cannot manufacture a passing score.
        policy["gold_hash"] = "frozen_other_frame"
        self.assertIn("frozen_sample_changed_without_policy_revision", recall_gate(report, policy)["errors"])
        policy["minimum_research_releases"] = 2
        self.assertIn("research_denominator_shrunk", recall_gate(report, policy)["errors"])

    def test_missing_stays_in_denominator(self):
        result = audit_release_recall([release(1), release(2)], catalog([work()], [{"work_id": "w:1", "url": release()["url"]}]))
        self.assertEqual(result["overall"]["denominator"], 2)
        self.assertEqual(result["overall"]["release_capture_recall"], .5)
        self.assertEqual(result["overall"]["status_counts"], {"included": 1, "missing": 1})

    def test_all_relevance_states_are_reported_separately(self):
        states = ["included", "candidate", "manual_review", "excluded"]
        rows = [release(i) for i in range(4)]
        works = [work(f"w:{i}", state, f"Robot research {i}") for i, state in enumerate(states)]
        versions = [{"work_id": f"w:{i}", "url": rows[i]["url"]} for i in range(4)]
        result = audit_release_recall(rows, catalog(works, versions))["overall"]
        self.assertEqual(result["status_counts"], dict.fromkeys(states, 1))
        self.assertEqual(result["denominator"], 4)
        self.assertEqual(result["release_capture_recall"], 1)
        self.assertEqual(result["formal_visible_recall"], .25)

    def test_existing_work_does_not_imply_release_url_capture(self):
        row = release(url="https://arxiv.org/abs/2601.00001", equivalent_urls=["https://arxiv.org/abs/2601.00001"])
        w = {**work(), "identifiers": {"arxiv": "2601.00001"}}
        result = audit_release_recall([row], catalog([w]))
        self.assertEqual(result["results"][0]["status"], "known_work_missing_release")
        self.assertEqual(result["overall"]["canonical_work_recall"], 1)
        self.assertEqual(result["overall"]["release_capture_recall"], 0)

    def test_title_only_is_candidate_not_identity(self):
        result = audit_release_recall([release()], catalog([work()]))
        self.assertEqual(result["results"][0]["status"], "title_candidate")
        self.assertEqual(result["overall"]["canonical_work_recall"], 0)
        self.assertEqual(result["results"][0]["matched_work_ids"], ["w:1"])

    def test_unlinked_raw_source_remains_an_explicit_gap(self):
        source = {"source_record_id": "src:1", "url": release()["url"]}
        result = audit_release_recall([release()], catalog(sources=[source]))
        self.assertEqual(result["results"][0]["status"], "unlinked_source")
        self.assertEqual(result["overall"]["canonical_work_recall"], 0)

    def test_ambiguous_urls_do_not_get_optimistic_credit(self):
        versions = [{"work_id": wid, "url": release()["url"]} for wid in ["a", "b"]]
        result = audit_release_recall([release()], catalog([work("a"), work("b")], versions))
        self.assertEqual(result["results"][0]["status"], "ambiguous")
        self.assertEqual(result["overall"]["release_captured"], 0)
        self.assertEqual(result["overall"]["release_url_present"], 1)
        self.assertEqual(result["overall"]["canonical_work_present"], 1)
        self.assertEqual(result["overall"]["canonical_identity_resolved"], 0)

    def test_only_observed_redirects_are_equivalent(self):
        row = release(equivalent_urls=["https://project.example/paper"])
        self.assertIn("unobserved_equivalent_url:g:1", validate_gold([row]))
        row["provenance"][0]["effective_url"] = row["equivalent_urls"][0]
        result = audit_release_recall([row], catalog([work()], [{"work_id": "w:1", "url": row["equivalent_urls"][0]}]))
        self.assertEqual(result["overall"]["release_captured"], 1)

    def test_related_project_and_index_do_not_match(self):
        row = release(related_urls=["https://another.example/research"])
        versions = [{"work_id": "w:1", "url": row["index_url"]}, {"work_id": "w:1", "url": row["related_urls"][0]}]
        result = audit_release_recall([row], catalog([work(title="Unrelated publication")], versions))
        self.assertEqual(result["results"][0]["status"], "missing")

    def test_source_gap_is_not_zero_releases(self):
        gap = {"record_type": "source_gap", "gold_id": "gap:1", "organization_id": "org:blocked", "source_url": "https://blocked.example", "reason": "access_blocked"}
        result = audit_release_recall([gap], catalog())
        self.assertIsNone(result["overall"]["release_capture_recall"])
        self.assertEqual(result["source_gaps"], [gap])
        self.assertEqual(result["sampled_organizations"], 1)
        self.assertEqual(result["organizations_with_at_least_two_releases"], 0)

    def test_url_normalization_is_conservative(self):
        self.assertEqual(normalize_url("http://www.arxiv.org/pdf/2601.00001v3.pdf?utm_source=test#x"), "https://arxiv.org/abs/2601.00001")
        self.assertNotEqual(normalize_url("https://lab.example/page?paper=1"), normalize_url("https://lab.example/page?paper=2"))
        self.assertEqual(normalize_url("https://lab.example/project/."), normalize_url("https://lab.example/project/"))
        self.assertNotEqual(normalize_url("https://lab.example/project."), normalize_url("https://lab.example/project/"))

    def test_gold_cannot_include_catalog_match_state(self):
        errors = validate_gold([release(matched_work_id="w:1")])
        self.assertIn("catalog_state_must_not_enter_gold:g:1", errors)

    def test_repeat_is_pure_and_deterministic(self):
        rows, db = [release()], catalog([work()])
        originals = copy.deepcopy((rows, db))
        self.assertEqual(audit_release_recall(rows, db), audit_release_recall(rows, db))
        self.assertEqual((rows, db), originals)

    def test_observations_not_mixed_with_research_artifact_rate(self):
        result = audit_release_recall([release(1), release(2, release_type="deployment_report")], catalog())
        self.assertEqual(result["research_artifacts"]["denominator"], 1)
        self.assertEqual(result["observational_releases"]["denominator"], 1)

    def test_invalid_hash_and_unknown_date_fail_validation(self):
        row = release(published_at_precision="unknown")
        row["provenance"][0]["sha256"] = "fake"
        self.assertEqual(len(validate_gold([row])), 2)

    def test_duplicate_gold_rows_are_rejected_not_silently_deduplicated(self):
        with self.assertRaises(ValueError):
            audit_release_recall([release(), release()], catalog())


if __name__ == "__main__":
    unittest.main()
