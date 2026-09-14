import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from report_text import (audit_report_text, digest, excerpt_word_count, register_report_text_additions,
                         report_text_as_of, sha256_text, snapshot_id_for)


def fixture(*, archived=True, available="2026-08-26T17:31:56Z", captured="2026-09-06T07:00:00Z"):
    # All artifacts are synthetic. Full source text is deliberately absent
    # from the public snapshot and SourceRecord returned by this fixture.
    text = "3 to 12 seconds; results: 59% then 83%; limitation: simple and short-horizon."
    excerpts = []
    for index, quote in enumerate(["3 to 12 seconds", "59%", "83%", "simple and short-horizon"]):
        start = text.index(quote)
        excerpts.append({"excerpt_id": "excerpt:" + str(index), "text": quote, "start": start,
                         "end": start + len(quote), "locator": "a.blog-entry[href='/blog/gen-1.5']@data-search"})
    row = {"work_id": "official:generalist/gen-1.5", "manifestation_id": "manifest:gen-1.5",
           "report_url": "https://generalistai.com/blog/gen-1.5", "source_url": "https://generalistai.com/blog/research",
           "source_record_id": "source:report-archive", "attestation_id": "attestation:gen-1.5",
           "report_published_at": "2026-08-19", "report_date_precision": "day", "captured_at": captured,
           "available_at": available if archived else captured, "date_precision": "second",
           "content_sha256": sha256_text(text), "excerpts": excerpts, "excerpt_digest": digest(excerpts),
           "observations": [{"id": "metric:score", "label": "作者报告的任务分数", "value": "59", "unit": "percentage",
                             "context": "AI 提取语境：该数值来自作者报告，不代表独立复现。", "excerpt_ids": ["excerpt:1"]}],
           "license": "copyrighted_excerpt_only", "evidence_scope": "author_report", "review_status": "source_content_checked",
           "context_kind": "ai_extracted_context", "verified_by": "codex_source_audit", "verified_at": captured}
    row["snapshot_id"] = snapshot_id_for(row)
    proof = {"raw_sha256": "a" * 64, "extracted_text_sha256": row["content_sha256"], "observations_digest": digest(row["observations"]), "selector": "a.blog-entry[href='/blog/gen-1.5']",
             "attribute": "data-search", "entity_unescape_passes": 1}
    if archived:
        proof.update({"commit": "b" * 40, "path": "data/group-source-status.json", "blob_sha1": "c" * 40,
                      "archive_status_sha256": "d" * 64, "archive_source_record_id": "source:old-status-id",
                      "archive_content_sha256": "a" * 64, "archive_captured_at": "2026-08-26T14:29:04.760164+00:00",
                      "deployment_url": "https://api.github.com/repos/example/radar/actions/runs/123",
                      "run_id": "123", "head_sha": "b" * 40, "deploy_completed_at": available,
                      "deployment_proof_sha256": "e" * 64})
    binding_keys = ["report_url", "source_url", "report_published_at", "report_date_precision", "captured_at", "available_at",
                    "date_precision", "content_sha256", "excerpt_digest", "verified_by", "verified_at"]
    attestation = {"attestation_id": row["attestation_id"], "status": "verified", "verification_scope": "source_content",
                   **{key: row[key] for key in binding_keys}, "basis": "git_archive" if archived else "fresh_capture", "proof": proof}
    source = {"source_record_id": row["source_record_id"], "source_type": "official_report_text_archive" if archived else "official_report_text_capture",
              "url": row["source_url"], "retrieved_at": captured, "content_sha256": row["content_sha256"], "raw_sha256": "a" * 64,
              "hash_scope": "http_response_body_bytes", "byte_count": 900, "report_text_attestations": [attestation]}
    work = {"work_id": row["work_id"], "aliases": [], "title": "GEN-1.5", "abstract": "", "authors": [],
            "first_public_date": "2026-08-19", "relevance": "included", "primary_direction": "D1",
            "strict_peer_reviewed": False, "source_record_ids": [source["source_record_id"]]}
    manifestation = {"manifestation_id": row["manifestation_id"], "work_id": work["work_id"], "url": row["report_url"],
                     "kind": "technical_report", "published_at": "2026-08-19", "date_precision": "day", "peer_reviewed": False}
    return {"works": [work], "manifestations": [manifestation], "source-records": [source]}, row


def reseal(row):
    row["excerpt_digest"] = digest(row["excerpts"])
    row["snapshot_id"] = snapshot_id_for(row)


def sync_attestation(payload, row):
    source = payload["source-records"][0]
    attestation = source["report_text_attestations"][0]
    for key in ["report_url", "source_url", "report_published_at", "report_date_precision", "captured_at", "available_at",
                "date_precision", "content_sha256", "excerpt_digest", "verified_by", "verified_at"]:
        attestation[key] = row[key]


def attest_observations(payload, row):
    """Fixture-only stand-in for an independent source/extraction verifier."""
    payload["source-records"][0]["report_text_attestations"][0]["proof"]["observations_digest"] = digest(row["observations"])


class ReportTextTests(unittest.TestCase):
    def test_register_is_pure_additive_and_idempotent_without_peer_or_work_mutations(self):
        payload, row = fixture()
        before, before_row = copy.deepcopy(payload), copy.deepcopy(row)
        first = register_report_text_additions(payload, [row])
        self.assertEqual(payload, before)
        self.assertEqual(row, before_row)
        self.assertEqual(first, register_report_text_additions(first, [row, row]))
        for key in before:
            self.assertEqual(first[key], before[key])
        self.assertEqual(first["report-text-snapshots"], [row])
        self.assertEqual(row["review_status"], "source_content_checked")
        self.assertEqual(row["evidence_scope"], "author_report")

    def test_archived_index_usable_after_deployment_not_report_publication(self):
        payload, row = fixture()
        result = register_report_text_additions(payload, [row])
        work = payload["works"][0]
        self.assertEqual(report_text_as_of(work, result["report-text-snapshots"], "2026-08-19")["status"], "retrospective_only")
        self.assertEqual(report_text_as_of(work, [row], "2026-08-26T16:00:00Z")["status"], "retrospective_only")
        view = report_text_as_of(work, [row], "2026-08")
        self.assertEqual(view["status"], "available")
        self.assertEqual(view["available_at"], "2026-08-26T17:31:56Z")
        self.assertNotEqual(row["source_url"], row["report_url"])
        self.assertEqual(view["canonical_work_id"], work["work_id"])

    def test_fresh_capture_never_borrows_publication_date(self):
        payload, row = fixture(archived=False)
        register_report_text_additions(payload, [row])
        self.assertEqual(report_text_as_of(payload["works"][0], [row], "2026-08")["status"], "retrospective_only")
        row["available_at"] = row["report_published_at"]
        row["date_precision"] = "day"
        reseal(row)
        sync_attestation(payload, row)  # Even an asserted global binding cannot bypass the capture rule.
        with self.assertRaisesRegex(ValueError, "fresh_capture_cannot_be_backdated"):
            register_report_text_additions(payload, [row])

    def test_input_cannot_backdate_or_self_attest(self):
        payload, row = fixture()
        row["available_at"] = "2026-08-20T00:00:00Z"
        reseal(row)
        with self.assertRaisesRegex(ValueError, "attestation_binding_mismatch"):
            register_report_text_additions(payload, [row])
        payload, row = fixture()
        row["attestation"] = payload["source-records"][0].pop("report_text_attestations")[0]
        reseal(row)
        with self.assertRaisesRegex(ValueError, "schema"):
            register_report_text_additions(payload, [row])

    def test_unknown_unverified_or_duplicate_global_attestations_rejected(self):
        for mode in ["missing", "unverified", "duplicate"]:
            with self.subTest(mode=mode):
                payload, row = fixture()
                proof = payload["source-records"][0]["report_text_attestations"]
                if mode == "missing":
                    proof.clear()
                elif mode == "unverified":
                    proof[0]["status"] = "draft"
                else:
                    proof.append(copy.deepcopy(proof[0]))
                with self.assertRaisesRegex(ValueError, "attestation"):
                    register_report_text_additions(payload, [row])

    def test_foreign_source_or_report_manifestation_not_accepted(self):
        for field, value in [("source_record_id", "foreign-source"), ("manifestation_id", "foreign-version"),
                             ("report_url", "https://generalistai.com/blog/another-report"), ("source_url", "https://example.com/copied")]:
            with self.subTest(field=field):
                payload, row = fixture()
                row[field] = value
                reseal(row)
                with self.assertRaises(ValueError):
                    register_report_text_additions(payload, [row])

    def test_company_demo_or_peer_review_cannot_be_injected(self):
        payload, row = fixture()
        payload["manifestations"][0]["kind"] = "demo"
        with self.assertRaisesRegex(ValueError, "kind_or_url"):
            register_report_text_additions(payload, [row])
        for field, value in [("peer_reviewed", True), ("review_status", "human_verified"), ("license", "CC0-1.0")]:
            payload, row = fixture()
            row[field] = value
            reseal(row)
            with self.assertRaisesRegex(ValueError, "schema"):
                register_report_text_additions(payload, [row])

    def test_report_date_must_match_existing_manifestation_without_guessing_day(self):
        payload, row = fixture()
        payload["manifestations"][0].update(published_at="2026-08-01", date_precision="month")
        with self.assertRaisesRegex(ValueError, "publication_date_mismatch"):
            register_report_text_additions(payload, [row])
        row.update(report_published_at="2026-08", report_date_precision="month")
        reseal(row)
        sync_attestation(payload, row)
        register_report_text_additions(payload, [row])

    def test_unknown_publication_preserved_but_capture_known(self):
        payload, row = fixture(archived=False)
        row.update(report_published_at=None, report_date_precision="unknown")
        payload["manifestations"][0].update(published_at=None, date_precision="unknown")
        reseal(row)
        sync_attestation(payload, row)
        register_report_text_additions(payload, [row])
        self.assertIsNone(row["report_published_at"])
        self.assertEqual(report_text_as_of(payload["works"][0], [row], "2026-09")["status"], "available")

    def test_same_id_conflict_fails_atomically_and_preserves_old_snapshot(self):
        payload, row = fixture()
        registered = register_report_text_additions(payload, [row])
        before = copy.deepcopy(registered)
        tampered = copy.deepcopy(row)
        tampered["observations"][0]["value"] = "83"
        with self.assertRaisesRegex(ValueError, "immutable_report_snapshot_conflict"):
            register_report_text_additions(registered, [tampered])
        self.assertEqual(registered, before)

    def test_excerpt_mutation_cannot_be_hidden_by_rehashing_snapshot(self):
        payload, row = fixture()
        row["excerpts"][1]["text"] = "99%"
        row["observations"][0]["value"] = "99"
        reseal(row)
        with self.assertRaisesRegex(ValueError, "attestation_binding_mismatch"):
            register_report_text_additions(payload, [row])

    def test_offset_and_locator_mutation_rejected(self):
        for changed in ["start", "locator"]:
            payload, row = fixture()
            if changed == "start":
                row["excerpts"][1]["start"] += 1
            else:
                row["excerpts"][1]["locator"] = "another-selector"
            reseal(row)
            with self.assertRaises(ValueError):
                register_report_text_additions(payload, [row])

    def test_content_raw_archive_and_deployment_tampering_fail(self):
        for field, value in [("archive_content_sha256", "f" * 64), ("head_sha", "f" * 40),
                             ("deploy_completed_at", "2026-08-20T00:00:00Z"), ("extracted_text_sha256", "f" * 64)]:
            payload, row = fixture()
            payload["source-records"][0]["report_text_attestations"][0]["proof"][field] = value
            with self.assertRaises(ValueError):
                register_report_text_additions(payload, [row])

    def test_collector_reported_time_is_not_historical_availability(self):
        payload, row = fixture()
        attestation = payload["source-records"][0]["report_text_attestations"][0]
        row["available_at"] = "2026-08-26T14:29:04.760164Z"
        attestation["available_at"] = row["available_at"]
        reseal(row)
        with self.assertRaisesRegex(ValueError, "not_deployment_bound"):
            register_report_text_additions(payload, [row])

    def test_numeric_boundaries_and_referenced_excerpt_only(self):
        for value, refs, unit in [("9", ["excerpt:1"], "percentage"), ("83", ["excerpt:1"], "percentage"),
                                  ("59", ["excerpt:1"], "count"), ("0.59", ["excerpt:1"], "ratio"), ("5", ["excerpt:0"], "count")]:
            payload, row = fixture()
            row["observations"][0].update(value=value, excerpt_ids=refs, unit=unit)
            reseal(row)
            with self.assertRaisesRegex(ValueError, "number_or_unit_not_in_excerpt"):
                register_report_text_additions(payload, [row])

    def test_physical_budget_count_has_explicit_context_no_unit_conversion(self):
        payload, row = fixture()
        row["observations"][0].update(label="响应等待时长上界（秒）", value="12", unit="count", context="AI 提取：12 秒；时间预算不是成功率或论文数量。", excerpt_ids=["excerpt:0"])
        reseal(row)
        attest_observations(payload, row)
        register_report_text_additions(payload, [row])

    def test_registered_attestation_cannot_be_reused_for_rehashed_observation_changes(self):
        changes = [
            {"value": "83", "excerpt_ids": ["excerpt:2"]},
            {"label": "基线成功率，非适配后表现"},
            {"context": "AI 提取语境：零样本，无任何演示或适配。"},
            {"value": "12", "unit": "count", "label": "响应等待时长（秒）", "excerpt_ids": ["excerpt:0"]},
        ]
        for archived in [True, False]:
            for change in changes:
                with self.subTest(archived=archived, change=change):
                    payload, original = fixture(archived=archived)
                    registered = register_report_text_additions(payload, [original])
                    before = copy.deepcopy(registered)
                    altered = copy.deepcopy(original)
                    altered["observations"][0].update(change)
                    reseal(altered)
                    self.assertNotEqual(altered["snapshot_id"], original["snapshot_id"])
                    with self.assertRaisesRegex(ValueError, "observations_attestation_mismatch"):
                        register_report_text_additions(registered, [altered])
                    self.assertEqual(registered, before)

    def test_missing_observation_digest_rejected_even_for_empty_observation_list(self):
        for archived in [True, False]:
            payload, row = fixture(archived=archived)
            row["observations"] = []
            reseal(row)
            payload["source-records"][0]["report_text_attestations"][0]["proof"].pop("observations_digest")
            with self.assertRaisesRegex(ValueError, "observations_attestation_mismatch"):
                register_report_text_additions(payload, [row])

    def test_number_punctuation_does_not_allow_partial_decimal_or_thousands(self):
        from report_text import _number_supported
        for text, value, expected in [("59, then", "59", True), ("59.", "59", True), ("1,059", "59", False),
                                      ("0.59", "59", False), ("-59", "59", False), ("159", "59", False)]:
            observation = {"value": value, "unit": "count", "excerpt_ids": ["ex"]}
            self.assertEqual(_number_supported(observation, {"ex": {"text": text}}), expected, text)

    def test_short_excerpt_budget_counts_hyphen_numbers_and_aggregate_versions(self):
        self.assertEqual(excerpt_word_count("10 gradient steps on 5 minutes of data per task (~50 demonstrations)"), 12)
        self.assertEqual(excerpt_word_count("simple and short-horizon"), 4)
        payload, row = fixture()
        row["excerpts"] = [{"excerpt_id": "long", "text": " ".join(["word"] * 26), "start": 0, "end": 129, "locator": "body"}]
        row["observations"] = []
        reseal(row)
        with self.assertRaisesRegex(ValueError, "word_budget"):
            register_report_text_additions(payload, [row])
        # Quota is across all history of this report, not reset each snapshot.
        payload, first = fixture()
        second = copy.deepcopy(first)
        text = " ".join("unique" + str(i) for i in range(16))
        second["excerpts"] = [{"excerpt_id": "second", "text": text, "start": 0, "end": len(text), "locator": "body"}]
        second["observations"] = []
        reseal(second)
        result = audit_report_text([first, second], payload["works"], payload["manifestations"], payload["source-records"])
        self.assertIn("report_excerpt_word_budget_exceeded", {error["reason"] for error in result["errors"]})

    def test_no_public_full_body_or_duplicate_quotes_in_proof(self):
        payload, row = fixture()
        serialized = json.dumps(register_report_text_additions(payload, [row]))
        self.assertNotIn("results:", serialized)
        self.assertEqual(serialized.count('"59%"'), 1)
        self.assertNotIn("full_text", serialized)
        payload["source-records"][0]["report_text_attestations"][0]["proof"]["full_text"] = "do not publish a report"
        with self.assertRaisesRegex(ValueError, "must_not_duplicate_source_text"):
            register_report_text_additions(payload, [row])

    def test_utc_boundary_and_second_precision(self):
        payload, row = fixture(available="2026-08-31T16:00:00Z")
        register_report_text_additions(payload, [row])
        work = payload["works"][0]
        self.assertEqual(report_text_as_of(work, [row], "2026-08")["status"], "retrospective_only")
        self.assertEqual(report_text_as_of(work, [row], "2026-09-01")["status"], "available")
        self.assertEqual(report_text_as_of(work, [row], "2026-08-31T16:00:00Z")["status"], "available")

    def test_date_only_month_and_year_bounds_are_never_midnight(self):
        payload, row = fixture()
        work = payload["works"][0]
        for value, precision, before, after in [("2026-08-26", "day", "2026-08-26T00:00:00Z", "2026-08-26"),
                                                ("2026-08", "month", "2026-08-30", "2026-08"),
                                                ("2026", "year", "2026-11", "2026")]:
            with self.subTest(precision=precision):
                candidate = copy.deepcopy(row)
                candidate.update(available_at=value, date_precision=precision)
                reseal(candidate)
                self.assertEqual(report_text_as_of(work, [candidate], before)["status"], "retrospective_only")
                self.assertEqual(report_text_as_of(work, [candidate], after)["status"], "available")

    def test_naive_or_unknown_dates_not_treated_as_historical(self):
        payload, row = fixture()
        row.update(available_at="2026-08-26T09:00:00", date_precision="second")
        reseal(row)
        with self.assertRaisesRegex(ValueError, "temporal"):
            register_report_text_additions(payload, [row])
        row.update(available_at=None, date_precision="unknown")
        reseal(row)
        self.assertEqual(report_text_as_of(payload["works"][0], [row], "2026-08")["status"], "unavailable")

    def test_same_time_conflicting_snapshots_are_preserved_not_chosen(self):
        payload, first = fixture()
        second = copy.deepcopy(first)
        second["content_sha256"] = "f" * 64
        reseal(second)
        view = report_text_as_of(payload["works"][0], [first, second], "2026-08")
        self.assertEqual(view["status"], "conflicting_snapshots")
        self.assertEqual(set(view["snapshot_ids"]), {first["snapshot_id"], second["snapshot_id"]})
        self.assertEqual(view["snapshots"], [])

    def test_same_time_observation_conflicts_not_silently_selected(self):
        payload, first = fixture()
        second = copy.deepcopy(first)
        second["observations"][0].update(value="83", excerpt_ids=["excerpt:2"])
        second["attestation_id"] = "attestation:independent-extraction"
        reseal(second)
        # A genuinely distinct, independently registered extraction is kept,
        # not overwritten or rejected merely because its interpretation differs.
        independent = copy.deepcopy(payload["source-records"][0]["report_text_attestations"][0])
        independent["attestation_id"] = second["attestation_id"]
        independent["proof"]["observations_digest"] = digest(second["observations"])
        payload["source-records"][0]["report_text_attestations"].append(independent)
        registered = register_report_text_additions(payload, [first, second])
        self.assertEqual(len(registered["report-text-snapshots"]), 2)
        view = report_text_as_of(payload["works"][0], registered["report-text-snapshots"], "2026-08")
        self.assertEqual(view["status"], "conflicting_snapshots")

    def test_latest_eligible_capture_keeps_earlier_snapshot(self):
        payload, first = fixture()
        second = copy.deepcopy(first)
        second["available_at"] = "2026-09-05T00:00:00Z"
        second["content_sha256"] = "f" * 64
        reseal(second)
        work = payload["works"][0]
        self.assertEqual(report_text_as_of(work, [first, second], "2026-08")["snapshot_ids"], [first["snapshot_id"]])
        self.assertEqual(report_text_as_of(work, [first, second], "2026-09")["snapshot_ids"], [second["snapshot_id"]])

    def test_later_identical_audit_does_not_replace_earlier_source_by_hash_order(self):
        payload, first = fixture()
        later = copy.deepcopy(first)
        later["captured_at"] = later["verified_at"] = "2026-09-06T08:00:00Z"
        # Find a deterministic later record whose content-derived ID sorts
        # before the original, reproducing the former min(snapshot_id) bug.
        for index in range(100):
            later["attestation_id"] = "attestation:later-" + str(index)
            reseal(later)
            if later["snapshot_id"] < first["snapshot_id"]:
                break
        self.assertLess(later["snapshot_id"], first["snapshot_id"])
        view = report_text_as_of(payload["works"][0], [later, first], "2026-08")
        self.assertEqual(view["snapshot_ids"], [first["snapshot_id"]])
        self.assertEqual(view, report_text_as_of(payload["works"][0], [first, later], "2026-08"))

    def test_identical_capture_tie_prefers_earliest_verification(self):
        payload, first = fixture()
        later = copy.deepcopy(first)
        later["verified_at"] = "2026-09-06T07:30:00Z"
        reseal(later)
        self.assertEqual(report_text_as_of(payload["works"][0], [later, first], "2026-08")["snapshot_ids"], [first["snapshot_id"]])

    def test_identity_merge_uses_unique_alias_without_rewriting_snapshot(self):
        payload, row = fixture()
        original = copy.deepcopy(row)
        work = payload["works"][0]
        work["aliases"] = [work["work_id"]]
        work["work_id"] = "doi:10.example/new-canonical"
        payload["manifestations"][0]["work_id"] = work["work_id"]
        result = register_report_text_additions(payload, [row])
        audit = audit_report_text([row], payload["works"], payload["manifestations"], payload["source-records"])
        self.assertEqual(audit["canonical_work_ids"][row["snapshot_id"]], work["work_id"])
        self.assertEqual(result["report-text-snapshots"][0], original)
        self.assertEqual(report_text_as_of(work, [row], "2026-08")["canonical_work_id"], work["work_id"])

    def test_ambiguous_alias_or_removed_source_fails_closed(self):
        payload, row = fixture()
        other = copy.deepcopy(payload["works"][0])
        other.update(work_id="other", aliases=[row["work_id"]])
        payload["works"].append(other)
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            register_report_text_additions(payload, [row])
        payload, row = fixture()
        payload["source-records"].clear()
        with self.assertRaisesRegex(ValueError, "source_unknown"):
            register_report_text_additions(payload, [row])

    def test_every_snapshot_audited_not_sampled(self):
        payload, row = fixture()
        bad = copy.deepcopy(row)
        bad["excerpts"][0]["text"] = "mutation"
        report = audit_report_text([row, bad], payload["works"], payload["manifestations"], payload["source-records"])
        self.assertEqual(report["checked_snapshots"], 2)
        self.assertEqual(report["status"], "failed")
        self.assertTrue(report["errors"])

    def test_malformed_excerpt_rows_report_schema_errors_without_crashing_audit(self):
        payload, row = fixture()
        row["excerpts"] = None
        report = audit_report_text([row, None], payload["works"], payload["manifestations"], payload["source-records"])
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["checked_snapshots"], 2)


if __name__ == "__main__":
    unittest.main()
