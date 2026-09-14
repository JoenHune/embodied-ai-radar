"""Archive attestation fixtures: no authority writes or dependency on raw cache."""
import copy
import hashlib
import html
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import extract_report_archive as archive

ROOT = Path(__file__).resolve().parents[1]


def fixtures():
    # The public test fixture reuses the SAME <=25 excerpt words, not additional
    # article prose; all unquoted full-body characters below are synthetic.
    stored = json.loads((ROOT / "data/report-text-additions.jsonl").read_text().splitlines()[0])
    chars = [" "] * 25536
    chars[:10] = "2026-08-19"
    chars[200:205] = "A & B"
    for row in stored["excerpts"]:
        chars[row["start"]:row["end"]] = row["text"]
    text = "".join(chars)
    raw = ('<html><body><a class="blog-entry" href="/blog/gen-1.5" data-search="' + html.escape(html.escape(text, quote=True), quote=True) + '">Fixture</a></body></html>').encode()
    proof = dict(archive.PINNED_GEN15)
    source = {"source_id": proof["archive_source_record_id"], "organization_id": "org:generalist-ai", "url": archive.SOURCE_URL,
              "content_hash": archive.sha256(raw), "last_checked": proof["archive_captured_at"], "status": "healthy"}
    status = json.dumps({"sources": [source]}).encode()
    deployment = json.loads((ROOT / archive.DEPLOY_PATH).read_text())
    deployment_blob = json.dumps(deployment).encode()
    proof.update(archive_content_sha256=archive.sha256(raw), archive_status_sha256=archive.sha256(status),
                 blob_sha1=hashlib.sha1(f"blob {len(status)}\0".encode() + status).hexdigest(),
                 deployment_proof_sha256=archive.sha256(deployment_blob), extracted_text_sha256=archive.sha256(text.encode()))
    source_proof, snapshot = archive.make_gen15_records(proof, text, len(raw), captured_at="2026-09-06T03:00:00Z", verified_at="2026-09-06T03:00:01Z")
    return proof, text, raw, status, deployment_blob, source_proof, snapshot


class ReportArchiveTests(unittest.TestCase):
    def test_full_material_chain_and_double_entity_decode(self):
        proof, text, raw, status, deployment, _, _ = fixtures()
        self.assertEqual(archive.check_archive_materials(proof, raw, status, deployment, archive.SOURCE_URL, archive.REPORT_URL), text)
        self.assertIn("A & B", text)

    def test_git_status_bytes_and_blob_object_hash_are_independent_checks(self):
        proof, _, raw, status, deployment, _, _ = fixtures()
        with self.assertRaisesRegex(ValueError, "status_sha256"):
            archive.check_archive_materials(proof, raw, status + b" ", deployment, archive.SOURCE_URL, archive.REPORT_URL)
        proof["blob_sha1"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "blob_sha1"):
            archive.check_archive_materials(proof, raw, status, deployment, archive.SOURCE_URL, archive.REPORT_URL)

    def test_old_source_id_url_and_raw_html_must_match(self):
        proof, _, raw, status, deployment, _, _ = fixtures()
        with self.assertRaisesRegex(ValueError, "html_hash"):
            archive.check_archive_materials(proof, raw + b" ", status, deployment, archive.SOURCE_URL, archive.REPORT_URL)
        with self.assertRaisesRegex(ValueError, "official_url"):
            archive.check_archive_materials(proof, raw, status, deployment, "https://example.test/other", archive.REPORT_URL)
        proof["archive_source_record_id"] = "source:missing"
        with self.assertRaisesRegex(ValueError, "source_not_unique"):
            archive.check_archive_materials(proof, raw, status, deployment, archive.SOURCE_URL, archive.REPORT_URL)

    def test_deployment_head_success_and_completed_time_are_required(self):
        for change, pattern in [({"head_sha": "a" * 40}, "commit_mismatch"), ({"conclusion": "failure"}, "not_successful")]:
            proof, _, raw, status, deployment, _, _ = fixtures()
            value = json.loads(deployment)
            value.update(change)
            deployment = json.dumps(value).encode()
            proof["deployment_proof_sha256"] = archive.sha256(deployment)
            with self.assertRaisesRegex(ValueError, pattern):
                archive.check_archive_materials(proof, raw, status, deployment, archive.SOURCE_URL, archive.REPORT_URL)
        proof, _, raw, status, deployment, _, _ = fixtures()
        proof["deploy_completed_at"] = json.loads(deployment)["created_at"]
        with self.assertRaisesRegex(ValueError, "job_not_proven"):
            archive.check_archive_materials(proof, raw, status, deployment, archive.SOURCE_URL, archive.REPORT_URL)

    def test_selector_report_href_and_extracted_hash_are_checked(self):
        proof, _, raw, status, deployment, _, _ = fixtures()
        with self.assertRaisesRegex(ValueError, "report_link"):
            archive.check_archive_materials(proof, raw, status, deployment, archive.SOURCE_URL, "https://generalistai.com/blog/other")
        wrong = {**proof, "selector": "a.missing"}
        with self.assertRaisesRegex(ValueError, "selector"):
            archive.check_archive_materials(wrong, raw, status, deployment, archive.SOURCE_URL, archive.REPORT_URL)
        wrong = {**proof, "extracted_text_sha256": "0" * 64}
        with self.assertRaisesRegex(ValueError, "extracted_text_hash"):
            archive.check_archive_materials(wrong, raw, status, deployment, archive.SOURCE_URL, archive.REPORT_URL)

    def test_output_contains_only_short_excerpts_and_distinct_dates(self):
        _, text, _, _, _, source, snapshot = fixtures()
        self.assertEqual(archive.lexical_word_count(row["text"] for row in snapshot["excerpts"]), 25)
        self.assertNotIn(text, json.dumps({"source": source, "snapshot": snapshot}))
        self.assertNotIn("excerpts", source["report_text_attestations"][0])
        self.assertEqual(snapshot["report_published_at"], "2026-08-19")
        self.assertEqual(snapshot["available_at"], "2026-08-26T17:31:56Z")
        self.assertTrue(snapshot["captured_at"].startswith("2026-09-06"))
        self.assertEqual(snapshot["review_status"], "source_content_checked")
        self.assertEqual(snapshot["context_kind"], "ai_extracted_context")
        self.assertEqual(snapshot["license"], "copyrighted_excerpt_only")

    def test_nine_cannot_match_fifty_nine_numeric_token(self):
        _, text, _, _, _, source, snapshot = fixtures()
        snapshot["observations"][0]["value"] = "9"
        attestation = source["report_text_attestations"][0]
        attestation["proof"]["observations_digest"] = archive.digest(snapshot["observations"])
        row = {k: v for k, v in snapshot.items() if k != "snapshot_id"}
        snapshot["snapshot_id"] = "report-text:" + archive.digest(row)[:24]
        with self.assertRaisesRegex(ValueError, "numeric_token"):
            archive._validate_public_snapshot(snapshot, attestation, text)

    def test_observations_cannot_change_without_global_attestation(self):
        _, text, _, _, _, source, snapshot = fixtures()
        snapshot["observations"][0]["context"] = archive.FT_CONTEXT
        snapshot["snapshot_id"] = "report-text:" + archive.digest({k: v for k, v in snapshot.items() if k != "snapshot_id"})[:24]
        with self.assertRaisesRegex(ValueError, "observations_not_attested"):
            archive._validate_public_snapshot(snapshot, source["report_text_attestations"][0], text)

    def test_old_capture_claim_cannot_be_reused_as_current_read_time(self):
        _, text, _, _, _, source, snapshot = fixtures()
        snapshot["captured_at"] = "2026-08-26T14:29:04Z"
        source["report_text_attestations"][0]["captured_at"] = snapshot["captured_at"]
        snapshot["snapshot_id"] = "report-text:" + archive.digest({k: v for k, v in snapshot.items() if k != "snapshot_id"})[:24]
        with self.assertRaisesRegex(ValueError, "capture_chronology"):
            archive._validate_public_snapshot(snapshot, source["report_text_attestations"][0], text)

    def test_aggregate_quota_is_per_report_and_counts_numeric_hyphen_tokens(self):
        _, _, _, _, _, _, snapshot = fixtures()
        self.assertEqual(archive.lexical_word_count(["one-shot 59%"]), 3)
        archive.validate_total_excerpt_quota([snapshot, copy.deepcopy(snapshot)])
        additional = {"report_url": snapshot["report_url"], "excerpts": [{"text": "extra"}]}
        with self.assertRaisesRegex(ValueError, "quota"):
            archive.validate_total_excerpt_quota([snapshot, additional])

    def test_registration_is_copy_on_write_and_verifies_new_source(self):
        proof, _, raw, status, deployment, source, snapshot = fixtures()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            for relative, content in [(archive.RAW_PATH, raw), (archive.DEPLOY_PATH, deployment)]:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
            original_work = {"work_id": archive.WORK_ID, "source_record_ids": ["source:old"], "manual_note": "keep"}
            unrelated = {"work_id": "work:untouched", "source_record_ids": []}
            payload = {"works": [original_work, unrelated], "source-records": [{"source_record_id": "source:old"}],
                       "manifestations": [{"manifestation_id": archive.MANIFESTATION_ID, "work_id": archive.WORK_ID, "kind": "technical_report", "url": archive.REPORT_URL}]}
            before = copy.deepcopy(payload)
            with patch.dict(archive.PINNED_GEN15, proof, clear=True), patch.object(archive, "_git_status", return_value=status) as read:
                result = archive.register_report_archive_proofs(payload, [source], [snapshot], root=root)
                read.assert_called_once()
            self.assertEqual(payload, before)
            self.assertIs(result["works"][1], unrelated)
            self.assertEqual(result["works"][0]["manual_note"], "keep")
            self.assertIn(snapshot["source_record_id"], result["works"][0]["source_record_ids"])
            self.assertNotIn("work_id", result["source-records"][-1])
            self.assertEqual(result["reconciliation"][0]["work_id"], archive.WORK_ID)
            self.assertEqual(result["reconciliation"][0]["snapshot_id"], snapshot["snapshot_id"])
            self.assertEqual({row["field"].rsplit(".", 1)[-1] for row in result["field-provenance"]}, {"excerpts", "available_at"})
            self.assertTrue(all(row["observed_at"] == snapshot["verified_at"] and row["basis"] == "archive_content_check" for row in result["field-provenance"]))

    def test_identical_registered_source_needs_no_ignored_cache_or_git(self):
        _, _, _, _, _, source, snapshot = fixtures()
        payload = {"works": [{"work_id": archive.WORK_ID, "source_record_ids": [source["source_record_id"]]}],
                   "source-records": [{k: v for k, v in source.items() if k != "work_id"}]}
        with patch.object(archive, "verify_report_archive_proof", side_effect=AssertionError("must not read missing raw/Git")):
            self.assertIs(archive.register_report_archive_proofs(payload, [source], [snapshot], root=Path("/missing-fixture")), payload)

    def test_changed_registered_source_id_is_rejected_without_overwrite(self):
        _, _, _, _, _, source, snapshot = fixtures()
        old = {k: v for k, v in source.items() if k != "work_id"}
        old["retrieved_at"] = "2026-09-06T02:00:00Z"
        payload = {"works": [{"work_id": archive.WORK_ID, "source_record_ids": [source["source_record_id"]]}], "source-records": [old]}
        with self.assertRaisesRegex(ValueError, "source_conflict"):
            archive.register_report_archive_proofs(payload, [source], [snapshot])
        self.assertEqual(old["retrieved_at"], "2026-09-06T02:00:00Z")

    def test_unique_historical_work_alias_preserves_proof_and_skips_registered_reads(self):
        _, _, _, _, _, source, snapshot = fixtures()
        source_before, snapshot_before = copy.deepcopy(source), copy.deepcopy(snapshot)
        current_id = "official:merged-gen15"
        payload = {"works": [{"work_id": current_id, "aliases": [archive.WORK_ID], "source_record_ids": []}],
                   "source-records": [], "manifestations": [{"manifestation_id": archive.MANIFESTATION_ID, "work_id": current_id, "kind": "technical_report", "url": archive.REPORT_URL}]}
        with patch.object(archive, "verify_report_archive_proof") as verify:
            result = archive.register_report_archive_proofs(payload, [source], [snapshot])
            verify.assert_called_once_with(source, snapshot, root=archive.ROOT)
        self.assertEqual(result["reconciliation"][0]["work_id"], current_id)
        self.assertEqual(result["reconciliation"][0]["original_work_id"], archive.WORK_ID)
        self.assertTrue(all(row["work_id"] == current_id for row in result["field-provenance"]))
        with patch.object(archive, "verify_report_archive_proof", side_effect=AssertionError("no ignored cache/Git required")):
            self.assertIs(archive.register_report_archive_proofs(result, [source], [snapshot]), result)
        self.assertEqual(source, source_before)
        self.assertEqual(snapshot, snapshot_before)

    def test_ambiguous_historical_work_alias_is_not_guessed(self):
        _, _, _, _, _, source, snapshot = fixtures()
        payload = {"works": [{"work_id": "work:a", "aliases": [archive.WORK_ID]}, {"work_id": "work:b", "aliases": [archive.WORK_ID]}], "source-records": []}
        with self.assertRaisesRegex(ValueError, "alias_missing_or_ambiguous"):
            archive.register_report_archive_proofs(payload, [source], [snapshot])

    def test_unknown_work_or_wrong_manifestation_fails_before_source_registration(self):
        _, _, _, _, _, source, snapshot = fixtures()
        payload = {"works": [{"work_id": archive.WORK_ID, "source_record_ids": []}], "source-records": [], "manifestations": []}
        with self.assertRaisesRegex(ValueError, "manifestation"):
            archive.register_report_archive_proofs(payload, [source], [snapshot])
        self.assertEqual(payload["source-records"], [])

    def test_raw_paths_cannot_escape_or_follow_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            with self.assertRaises(ValueError):
                archive._safe_local(root, "../outside")
            with self.assertRaises(ValueError):
                archive._safe_local(root, "/absolute/file")
            (root / "link").symlink_to(root, target_is_directory=True)
            with self.assertRaises(ValueError):
                archive._safe_local(root, "link/file")

    def test_fulltext_or_absolute_path_fields_are_not_registered(self):
        proof, _, _, _, _, source, snapshot = fixtures()
        source["full_text"] = "not permitted"
        with patch.dict(archive.PINNED_GEN15, proof, clear=True), self.assertRaisesRegex(ValueError, "unexpected_source_fields"):
            archive.verify_report_archive_proof(source, snapshot)
        source.pop("full_text")
        source["cache_ref"] = "/Users/private/report.html"
        with patch.dict(archive.PINNED_GEN15, proof, clear=True), self.assertRaisesRegex(ValueError, "raw_scope"):
            archive.verify_report_archive_proof(source, snapshot)

    def test_git_target_is_fixed_and_never_shell_interpreted(self):
        with patch.object(archive.subprocess, "check_output") as command:
            with self.assertRaises(ValueError):
                archive._git_status(ROOT, {"commit": "bad;command", "path": archive.STATUS_PATH})
            command.assert_not_called()


if __name__ == "__main__":
    unittest.main()
