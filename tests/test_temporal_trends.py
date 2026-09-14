import copy
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from catalog_rules import evidence_relationships, independent_clusters
from temporal_evidence import evidence_as_of, public_day
from trend_signals import assess_signal, reviewed_signal_evidence

SPEC = {"signal_id": "S1", "terms": ["robot"], "required_terms": ["policy"]}
MONTHS = ["2026-05", "2026-06", "2026-07", "2026-08"]


def work(wid="a", published="2026-08-01", reviewed=False):
    result = {"work_id": wid, "title": "A robot policy", "abstract": "", "authors": ["Author " + wid],
              "first_public_date": published, "first_public_date_precision": "day", "relevance": {"status": "included"},
              "source_record_ids": ["src:" + wid], "evidence_flags": {"real_robot": True}, "repositories": ["https://github.com/shared/benchmark"],
              "signal_evidence": []}
    if reviewed:
        result["signal_evidence"] = [proof(result)]
        result["evidence_flag_evidence"] = [{"record_id": "real:" + wid, "flag": "real_robot", "value": True,
            "review_status": "verified", "public_at": published, "source_url": "https://example.org/" + wid, "source_record_ids": ["src:" + wid]}]
    return result


def proof(row, **changes):
    return {"record_id": "proof:" + row["work_id"], "signal_id": "S1", "work_id": row["work_id"], "stance": "supports",
            "statement": "The measured policy improves under the specified experiment.", "review_status": "verified", "research_scope": "in_scope",
            "source_url": "https://example.org/" + row["work_id"], "source_record_ids": row["source_record_ids"],
            "public_at": row["first_public_date"], "public_at_precision": "day",
            "experiment": {"setting": None, "baseline": None, "metric": None, "limitations": []}, **changes}


def version(wid="a", **changes):
    return {"manifestation_id": "m:" + wid, "work_id": wid, "kind": "conference", "venue": "CoRL", "peer_reviewed": True,
            "publication_status": "accepted_peer_reviewed", "accepted_at": "2026-09-04", "date_precision": "day", **changes}


def assess(rows, versions=None, months=None, **kwargs):
    return assess_signal(SPEC, rows, months or MONTHS, {r["work_id"]: ["org:" + r["work_id"]] for r in rows}, versions or {}, **kwargs)


class TemporalEvidenceTests(unittest.TestCase):
    def test_calendar_cutoff_preserves_dates_and_converts_utc(self):
        self.assertEqual(public_day("2026-08-31"), date(2026, 8, 31))
        self.assertEqual(public_day("2026-08-31T16:00:00Z"), date(2026, 9, 1))
        self.assertEqual(public_day("2026-08", "month"), date(2026, 8, 31))
        self.assertEqual(public_day("2026-01-01", "year"), date(2026, 12, 31))
        self.assertIsNone(public_day("2026-08-01", "unknown"))
        self.assertIsNone(public_day("2026-08-31T15:00:00"))

    def test_future_acceptance_not_backdated(self):
        row = work(reviewed=True)
        before = evidence_as_of(row, [version()], "2026-08")
        after = evidence_as_of(row, [version()], "2026-09")
        self.assertFalse(before["strict_peer_reviewed"])
        self.assertEqual(before["evidence_grade"], "E2")
        self.assertEqual(before["available_manifestation_ids"], [])
        self.assertTrue(after["strict_peer_reviewed"])
        self.assertEqual(after["evidence_grade"], "E3")

    def test_unknown_acceptance_cannot_use_preprint_or_venue_date(self):
        result = evidence_as_of(work(), [version(accepted_at=None, published_at="2026-06-01")], "2026-08")
        self.assertFalse(result["strict_peer_reviewed"])
        self.assertIn("peer_review_date_unknown", [gap["reason"] for gap in result["information_gaps"]])
        unknown = evidence_as_of(work(), [version(accepted_at="2026-08-01", date_precision="unknown")], "2026-08")
        self.assertFalse(unknown["strict_peer_reviewed"])

    def test_unknown_current_flags_and_replication_ids_do_not_upgrade(self):
        row = {**work(), "independent_replication_evidence_ids": ["undated-replication"]}
        result = evidence_as_of(row, [], "2026-08")
        self.assertEqual(result["evidence_grade"], "E0")
        self.assertFalse(result["evidence_flags"]["real_robot"])
        self.assertEqual(result["independent_replication_evidence_ids"], [])

    def test_asset_needs_known_release_and_verification(self):
        row = work()
        code = version(kind="code", peer_reviewed=False, status="verified_repository", publication_status="code", accepted_at=None, published_at="2026-08-31T16:01:00Z", url="https://github.com/lab/code")
        self.assertFalse(evidence_as_of(row, [code], "2026-08")["evidence_flags"]["open_code"])
        self.assertTrue(evidence_as_of(row, [code], "2026-09")["evidence_flags"]["open_code"])
        code["published_at"] = None
        self.assertFalse(evidence_as_of(row, [code], "2026-09")["evidence_flags"]["open_code"])

    def test_first_party_report_remains_e1(self):
        report = version(kind="technical_report", peer_reviewed=False, publication_status="technical_report", accepted_at=None, published_at="2026-08-01")
        self.assertEqual(evidence_as_of(work(reviewed=True), [report], "2026-08")["evidence_grade"], "E1")

    def test_helper_does_not_mutate_inputs(self):
        row, manifestation = work(reviewed=True), version()
        original = copy.deepcopy((row, manifestation))
        evidence_as_of(row, [manifestation], "2026-08")
        self.assertEqual((row, manifestation), original)


class EvidenceOriginTests(unittest.TestCase):
    def test_same_benchmark_does_not_merge_origins(self):
        rows = [work("a"), work("b")]
        clusters = independent_clusters(rows)
        self.assertNotEqual(clusters["a"], clusters["b"])
        relations = evidence_relationships(rows)
        self.assertTrue(any(r["type"] == "shared_repository" and not r["merges_evidence_origin"] for r in relations))

    def test_author_bridges_are_not_transitive_identity(self):
        rows = [work("a"), work("b"), work("c")]
        for row, authors in zip(rows, [["Alice", "Bob"], ["Alice", "Bob", "Carol", "David"], ["Carol", "David"]]):
            row["authors"] = authors
        clusters = independent_clusters(rows)
        self.assertEqual(len(set(clusters.values())), 3)
        self.assertEqual(sum(r["type"] == "author_overlap" for r in evidence_relationships(rows)), 2)

    def test_only_explicit_series_or_verified_dependency_merges(self):
        rows = [work("a"), work("b")]
        rows[0]["evidence_dependencies"] = [{"target_work_id": "b", "review_status": "draft", "source_url": "https://example.org/project"}]
        self.assertEqual(len(set(independent_clusters(rows).values())), 2)
        rows[0]["evidence_dependencies"][0]["review_status"] = "verified"
        self.assertEqual(len(set(independent_clusters(rows).values())), 1)
        rows[0].pop("evidence_dependencies")
        for row in rows:
            row["project_series_ids"] = ["verified-project"]
        self.assertEqual(len(set(independent_clusters(rows).values())), 1)


class TemporalSignalTests(unittest.TestCase):
    def test_retrieval_and_legacy_strings_cannot_upgrade(self):
        rows = [work(str(i), reviewed=False) for i in range(3)]
        for row in rows:
            row["signal_evidence"] = {"S1": "supports"}
        result = assess(rows)
        self.assertEqual(result["lifecycle"], "candidate")
        self.assertEqual(result["supporting_work_ids"], [])
        self.assertEqual(result["assessment_status"], "retrieval_only")
        self.assertEqual(result["momentum_basis"], "retrieval_topic_share_not_verified_capability")

    def test_verified_support_can_emerge(self):
        result = assess([work(str(i), reviewed=True) for i in range(3)])
        self.assertEqual(result["lifecycle"], "emerging")
        self.assertEqual(len(result["supporting_evidence_ids"]), 3)

    def test_future_peer_cannot_make_historical_signal_mature(self):
        rows = [work("a", "2026-07-01", True), work("b", "2026-08-01", True)]
        versions = {"a": [version("a", venue="CoRL", accepted_at="2026-09-04")], "b": [version("b", venue="NeurIPS", accepted_at="2026-10-01")]}
        self.assertNotEqual(assess(rows, versions)["lifecycle"], "established")
        after = assess(rows, versions, MONTHS + ["2026-09", "2026-10"])
        self.assertEqual(after["lifecycle"], "established")

    def test_future_counterevidence_does_not_change_past(self):
        rows = [work("a", reviewed=True), work("b", reviewed=True)]
        rows[1]["signal_evidence"] = [proof(rows[1], stance="contradicts", public_at="2026-09-01")]
        self.assertEqual(assess(rows)["counterevidence_ids"], [])
        self.assertFalse(assess(rows)["disputed"])
        after = assess(rows, months=MONTHS + ["2026-09"])
        self.assertEqual(after["counterevidence_ids"], ["b"])
        self.assertTrue(after["disputed"])

    def test_draft_out_of_scope_unknown_date_or_missing_source_are_not_support(self):
        for changes in [{"review_status": "draft"}, {"research_scope": "out_of_scope"}, {"public_at": None}, {"public_at_precision": "unknown"}, {"source_record_ids": []}, {"source_url": ""}, {"work_id": "other"}, {"experiment": {}}, {"experiment": {"setting": None, "baseline": None, "metric": 1, "limitations": []}}]:
            with self.subTest(changes=changes):
                row = work(reviewed=True)
                row["signal_evidence"] = [proof(row, **changes)]
                self.assertEqual(reviewed_signal_evidence(row, "S1", "2026-08"), [])

    def test_source_map_checks_record_identity_and_url(self):
        row = work(reviewed=True)
        sources = {"src:a": {"source_record_id": "src:a", "url": "https://example.org/a"}}
        self.assertEqual(len(reviewed_signal_evidence(row, "S1", "2026-08", sources)), 1)
        sources["src:a"]["url"] = "https://example.org/wrong"
        self.assertEqual(reviewed_signal_evidence(row, "S1", "2026-08", sources), [])

    def test_month_precision_available_at_end_not_start(self):
        row = work(reviewed=True)
        row["signal_evidence"] = [proof(row, public_at="2026-08", public_at_precision="month")]
        self.assertEqual(reviewed_signal_evidence(row, "S1", "2026-08-15"), [])
        self.assertEqual(len(reviewed_signal_evidence(row, "S1", "2026-08-31")), 1)

    def test_reviewed_evidence_does_not_require_lexical_hit(self):
        row = work(reviewed=True)
        row["title"] = "A specially named experiment"
        self.assertEqual(assess([row])["supporting_work_ids"], ["a"])

    def test_explicit_cutoff_ignores_future_months(self):
        rows = [work("a", reviewed=True), work("b", "2026-09-01", True)]
        result = assess(rows, months=MONTHS + ["2026-09"], as_of_month="2026-08")
        self.assertEqual(result["months"], MONTHS)
        self.assertEqual(result["supporting_work_ids"], ["a"])


if __name__ == "__main__":
    unittest.main()
