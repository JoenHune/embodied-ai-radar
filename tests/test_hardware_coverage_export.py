import copy
import gzip
import hashlib
import json
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from catalog_store import encode, fingerprint
from fulltext_reading_reviews import ASSURANCE, NORMALIZATION, TEXT_SCOPE, public_audit
from hardware_coverage_export import (audit_coverage, build_coverage, coverage_sqlite, export_coverage,
                                      load_hardware_dictionary, project_work)
from test_equipment_radar import fixture, make_work
from test_hardware_census import dictionary_fixture, observation, scan


def public_reading_fixture(work, version='v1'):
    """Synthetic public receipt only; this fixture claims no actual reading."""
    wid = work['work_id']
    source_url = 'https://arxiv.org/html/' + work['identifiers']['arxiv'] + version
    raw_hash = fingerprint(['test-raw', wid, version])
    text_hash = fingerprint(['test-article', wid, version])
    locator_hash = fingerprint(['test-section', wid, version])
    obs = observation(wid, source_url=source_url, effective_url=source_url, version=version,
                      raw_sha256=raw_hash, text_sha256=fingerprint(['test-body', wid, version]),
                      transport_verification='legacy_unrecorded')
    identity = [wid, source_url, version, raw_hash, text_hash, TEXT_SCOPE, NORMALIZATION]
    record = {'schema_version': '1', 'reading_id': 'fulltext-reading:' + fingerprint(identity)[:24],
              'work_id': wid, 'source_url': source_url, 'version': version, 'raw_sha256': raw_hash,
              'observed_at': obs['observed_at'], 'read_completed_at': '2026-09-14T02:00:00Z',
              'reader_kind': 'AI', 'reading_status': 'completed', 'assurance': ASSURANCE,
              'human_reviewed': False, 'understanding_verified': False,
              'verification_scope': 'source_identity_hash_ranges_and_locators_only',
              'text_scope': TEXT_SCOPE, 'article_normalization': NORMALIZATION,
              'article_chars': 100, 'article_text_sha256': text_hash, 'read_ranges': [{'start': 0, 'end': 100}],
              'range_units': 'python_unicode_characters_zero_based_half_open',
              'checked_table_ids': [], 'checked_table_count': 0, 'checked_table_text_sha256': {}, 'tables_exhaustive': False,
              'math_source_note_zh': '测试声明：按原文核对数学表达，未作独立推导。',
              'images_inspected': False, 'supplementary_materials_inspected': False,
              'supplementary_scope_note': 'external_media_only; embedded_appendix_text_is_within_article_scope',
              'source_availability_status': obs['status'], 'transport_verification': 'legacy_unrecorded',
              'publisher_fulltext_or_media_completeness_verified': False,
              'findings_zh': [{'text_zh': '测试声明：作者报告了研究方法。', 'source_locator': 'S1', 'locator_text_sha256': {'S1': locator_hash}}],
              'limitations_zh': [{'text_zh': '测试声明：尚未独立核验实验结果。', 'source_locator': 'S1', 'locator_text_sha256': {'S1': locator_hash}}],
              'declaration_sha256': fingerprint(['synthetic-declaration', wid, version])}
    return record, obs


def coverage_fixture():
    payload, authority, manifest = fixture()
    payload["works"][0].update(primary_direction="D5", directions=["D1", "D5"])
    payload["works"].extend([make_work(2, "excluded"), make_work(3, "manual_review", "2026-07"),
                             make_work(4, "candidate", "2026-09"), make_work(5, "included")])
    payload["works"][4]["abstract"] = None
    dictionary = dictionary_fixture()
    observations = [observation(work["work_id"], source_url="https://arxiv.org/html/" + work["work_id"][6:] + "v1",
                                 status=status, cache_ref="/Users/private/body.html", blocks_ref=".research/secret/blocks.json",
                                 section_text="Private source paragraph should not be exported.")
                    for work, status in zip(payload["works"], ["full_text_available", "full_text_available", "blocked", "partial_text"])]
    scans = [scan(observations[0], dictionary), scan(observations[1], dictionary, text="No explicit models are named."),
             scan(observations[3], dictionary, text="NVIDIA RTX 4090 trained the baseline. Unitree G1 robot in a cited work.")]
    scans[0]["blocks_ref"] = "/Users/private/blocks.json"
    scans[0]["unrecognized_raw_paragraph"] = "Private source paragraph should not be exported."
    scans[0]["matches"] *= 2
    return payload, authority, dictionary, scans, observations, manifest


class HardwareCoverageExportTests(unittest.TestCase):
    def build(self):
        return build_coverage(*coverage_fixture())

    def export(self, bundle, directory, connection):
        api, downloads = Path(directory) / "api/equipment", Path(directory) / "downloads/equipment"
        export_coverage(bundle, api, downloads)
        coverage_sqlite(connection, bundle)
        return api, downloads

    def test_build_shares_dataset_version_preserves_inputs_and_separates_states(self):
        args = coverage_fixture()
        before = copy.deepcopy(args)
        bundle = build_coverage(*args)
        self.assertEqual(args, before)
        self.assertEqual(bundle["summary"]["dataset_version"], args[-1]["dataset_version"])
        self.assertEqual(bundle["models"]["dataset_version"], args[-1]["dataset_version"])
        counts = bundle["summary"]["all_works"]
        self.assertEqual(counts["denominator"], 5)
        self.assertEqual(counts["metadata_screened_work_count"], 5)
        self.assertEqual(counts["full_text_screened_current_dictionary_work_count"], 2)
        self.assertEqual(counts["partial_text_screened_current_dictionary_work_count"], 1)
        self.assertEqual(counts["full_text_failed_work_count"], 1)
        self.assertEqual(counts["full_text_not_attempted_work_count"], 1)
        self.assertEqual(counts["verified_relationship_work_count"], 1)

    def test_unique_model_work_counts_not_occurrences_or_verified_usage(self):
        bundle = self.build()
        model = next(row for row in bundle["models"]["models"] if row["dictionary_id"] == "unitree-g1")
        self.assertEqual(model["metadata_work_count"], 4)
        self.assertEqual(model["body_work_count"], 2)
        self.assertEqual(model["candidate_work_count"], 4)
        self.assertEqual(model["included_candidate_work_count"], 1)
        self.assertEqual(model["evidence_status"], "unverified_mention")
        self.assertEqual(model["usage_inference"], "none")
        unused = next(row for row in bundle["models"]["models"] if row["dictionary_id"] == "apple-m1")
        self.assertEqual(unused["work_ids"], [])
        self.assertEqual(unused["evidence_status"], "unverified_mention")

    def test_compact_rows_are_under_300_bytes_and_do_not_repeat_source_hashes(self):
        bundle = self.build()
        projections = [project_work(row) for row in bundle["rows"]]
        self.assertLess(sum(len(encode(row).encode()) for row in projections) / len(projections), 300)
        for row in projections:
            self.assertFalse({"title", "abstract", "excerpt", "content_hash", "dictionary_hash", "source_observations"} & row.keys())

    def test_roundtrip_gzip_api_shards_sqlite_and_exact_ids(self):
        bundle = self.build()
        with tempfile.TemporaryDirectory() as directory, closing(sqlite3.connect(":memory:")) as connection:
            api, downloads = self.export(bundle, directory, connection)
            result = audit_coverage(bundle, api, downloads, connection)
            self.assertEqual(result["work_count"], 5)
            self.assertEqual(result["shards"], 256)
            self.assertEqual(len(list((api / "coverage/works").glob("*.json"))), 256)
            self.assertEqual({path.name for path in downloads.iterdir()}, {"hardware-coverage.jsonl.gz", 'fulltext-readings.jsonl'})
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM hardware_coverage").fetchone()[0], 5)
            self.assertEqual({row[1] for row in connection.execute("PRAGMA table_info(hardware_coverage)")} & {"payload_json", "abstract", "title"}, set())
            self.assertEqual({row[0] for row in connection.execute("SELECT key FROM coverage_metadata")}, {"summary", "dictionary", "source_observations", "source_scans", "models", 'readings'})

    def test_public_exports_omit_body_excerpts_and_local_paths_at_all_depths(self):
        bundle = self.build()
        with tempfile.TemporaryDirectory() as directory, closing(sqlite3.connect(":memory:")) as connection:
            api, downloads = self.export(bundle, directory, connection)
            with gzip.open(downloads / "hardware-coverage.jsonl.gz", "rt") as stream:
                text = stream.read()
            text += "\n".join(value for _, value in connection.execute("SELECT key,payload_json FROM coverage_metadata"))
            text += "\n".join(path.read_text() for path in api.rglob("*.json"))
            for forbidden in ("/Users/private", ".research/secret", '"excerpt"', '"cache_ref"', '"blocks_ref"', "Private source paragraph"):
                self.assertNotIn(forbidden, text)
            self.assertIn('"dictionary_hash"', text)
            self.assertIn('"content_hash"', text)
            self.assertIn('"body_source_state"', text)
            self.assertEqual(audit_coverage(bundle, api, downloads, connection)["status"], "ok")

    def test_gzip_output_is_deterministic_without_local_header_filename(self):
        bundle = self.build()
        with tempfile.TemporaryDirectory() as directory:
            api, downloads = Path(directory) / "api", Path(directory) / "downloads"
            export_coverage(bundle, api, downloads)
            original = (downloads / "hardware-coverage.jsonl.gz").read_bytes()
            export_coverage(bundle, api, downloads)
            self.assertEqual((downloads / "hardware-coverage.jsonl.gz").read_bytes(), original)
            self.assertEqual(original[4:8], b"\x00\x00\x00\x00")
            self.assertEqual(original[3] & 8, 0)

    def test_duplicate_rows_are_rejected_before_export_or_sqlite(self):
        bundle = self.build()
        bundle["rows"].append(copy.deepcopy(bundle["rows"][0]))
        with tempfile.TemporaryDirectory() as directory, closing(sqlite3.connect(":memory:")) as connection:
            with self.assertRaisesRegex(ValueError, "duplicate_work_id"):
                export_coverage(bundle, Path(directory) / "api", Path(directory) / "downloads")
            with self.assertRaisesRegex(ValueError, "duplicate_work_id"):
                coverage_sqlite(connection, bundle)

    def test_api_summary_and_shard_tampering_fails(self):
        for tamper in ("summary", "missing_work", "extra_work", "wrong_state", "extra_shard", "revision"):
            with self.subTest(tamper=tamper), tempfile.TemporaryDirectory() as directory, closing(sqlite3.connect(":memory:")) as connection:
                bundle = self.build()
                api, downloads = self.export(bundle, directory, connection)
                wid = bundle["rows"][0]["work_id"]
                shard_path = api / "coverage/works" / (hashlib.sha1(wid.encode()).hexdigest()[:2] + ".json")
                saved = json.loads(shard_path.read_text())
                if tamper == "summary":
                    summary = json.loads((api / "coverage-summary.json").read_text())
                    summary["all_works"]["denominator"] += 1
                    (api / "coverage-summary.json").write_text(encode(summary))
                elif tamper == "extra_shard":
                    (api / "coverage/works/extra.json").write_text("{}")
                else:
                    if tamper == "missing_work":
                        del saved["by_work"][wid]
                    elif tamper == "extra_work":
                        saved["by_work"]["invented"] = saved["by_work"][wid]
                    elif tamper == "wrong_state":
                        saved["by_work"][wid]["verified_count"] += 1
                    else:
                        saved["dataset_version"] = "stale"
                    shard_path.write_text(encode(saved))
                with self.assertRaisesRegex(ValueError, "hardware_coverage"):
                    audit_coverage(bundle, api, downloads, connection)

    def test_download_gzip_missing_duplicate_changed_or_private_row_fails(self):
        for tamper in ("missing", "duplicate", "state", "private"):
            with self.subTest(tamper=tamper), tempfile.TemporaryDirectory() as directory, closing(sqlite3.connect(":memory:")) as connection:
                bundle = self.build()
                api, downloads = self.export(bundle, directory, connection)
                path = downloads / "hardware-coverage.jsonl.gz"
                with gzip.open(path, "rt") as stream:
                    rows = [json.loads(line) for line in stream]
                if tamper == "missing":
                    rows.pop()
                elif tamper == "duplicate":
                    rows.append(rows[0])
                elif tamper == "state":
                    rows[0]["body_scan_status"] = "not_attempted"
                else:
                    rows[0]["cache_ref"] = "/Users/private/source.html"
                with gzip.open(path, "wt") as stream:
                    stream.write("\n".join(encode(row) for row in rows) + "\n")
                with self.assertRaisesRegex(ValueError, "hardware_coverage_download"):
                    audit_coverage(bundle, api, downloads, connection)

    def test_sqlite_typed_counts_metadata_and_canonical_work_set_are_audited(self):
        for tamper in ("count", "state", "missing", "extra", "metadata", "canonical"):
            with self.subTest(tamper=tamper), tempfile.TemporaryDirectory() as directory, closing(sqlite3.connect(":memory:")) as connection:
                bundle = self.build()
                api, downloads = self.export(bundle, directory, connection)
                wid = bundle["rows"][0]["work_id"]
                if tamper == "count":
                    connection.execute("UPDATE hardware_coverage SET verified_count=verified_count+1 WHERE work_id=?", (wid,))
                elif tamper == "state":
                    connection.execute("UPDATE hardware_coverage SET body_scan_status='wrong' WHERE work_id=?", (wid,))
                elif tamper == "missing":
                    connection.execute("DELETE FROM hardware_coverage WHERE work_id=?", (wid,))
                elif tamper == "extra":
                    connection.execute("UPDATE hardware_coverage SET work_id='invented' WHERE work_id=?", (wid,))
                elif tamper == "metadata":
                    connection.execute("UPDATE coverage_metadata SET payload_json='{}' WHERE key='dictionary'")
                else:
                    connection.execute("CREATE TABLE works(work_id TEXT PRIMARY KEY)")
                    connection.execute("INSERT INTO works VALUES ('invented')")
                with self.assertRaisesRegex(ValueError, "hardware_coverage"):
                    audit_coverage(bundle, api, downloads, connection)

    def test_even_faithfully_copied_bad_summary_or_model_counts_fail(self):
        for tamper in ("summary", "groups", "model_count", "model_included", "verified_model"):
            with self.subTest(tamper=tamper), tempfile.TemporaryDirectory() as directory, closing(sqlite3.connect(":memory:")) as connection:
                bundle = self.build()
                if tamper == "summary":
                    bundle["summary"]["all_works"]["denominator"] += 1
                elif tamper == "groups":
                    bundle["summary"]["by_month"][0]["all_works"]["denominator"] += 1
                elif tamper == "model_count":
                    bundle["models"]["models"][0]["candidate_work_count"] += 1
                elif tamper == "model_included":
                    bundle["models"]["models"][0]["included_metadata_work_count"] += 1
                else:
                    bundle["models"]["models"][0]["evidence_status"] = "verified"
                api, downloads = self.export(bundle, directory, connection)
                with self.assertRaisesRegex(ValueError, "hardware_coverage"):
                    audit_coverage(bundle, api, downloads, connection)

    def test_source_text_and_dictionary_hash_change_still_require_rescan(self):
        args = coverage_fixture()
        original = build_coverage(*args)
        args[2]["version"] = "2"
        newer_dictionary = build_coverage(*args)
        self.assertEqual(original["summary"]["all_works"]["full_text_screened_current_dictionary_work_count"], 2)
        self.assertEqual(newer_dictionary["summary"]["all_works"]["full_text_screened_current_dictionary_work_count"], 0)
        self.assertEqual(newer_dictionary["summary"]["all_works"]["verified_relationship_work_count"], 1)

    def test_missing_revision_or_private_dictionary_fails_closed(self):
        args = coverage_fixture()
        args[-1].pop("dataset_version")
        with self.assertRaisesRegex(ValueError, "manifest_version"):
            build_coverage(*args)
        args = coverage_fixture()
        args[2]["cache_ref"] = "/Users/private/dictionary.json"
        with self.assertRaisesRegex(ValueError, "dictionary_contains_private"):
            build_coverage(*args)

    def test_dictionary_loader_requires_explicit_valid_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'hardware-dictionary.json'
            with self.assertRaisesRegex(FileNotFoundError, 'dictionary_required'):
                load_hardware_dictionary(path)
            for invalid in ({}, {'schema_version': '1', 'version': 'unconfigured', 'entries': []},
                            {'schema_version': '1', 'version': '1', 'entries': {}}):
                path.write_text(encode(invalid))
                with self.assertRaises(ValueError):
                    load_hardware_dictionary(path)
            explicit_empty = {'schema_version': '1', 'version': 'fixture-empty', 'entries': []}
            path.write_text(encode(explicit_empty))
            self.assertEqual(load_hardware_dictionary(path), explicit_empty)

    def test_offline_reparse_is_an_observation_not_an_extra_http_request(self):
        payload, authority, dictionary, scans, observations, manifest = coverage_fixture()
        original = observations[0]
        original['observation_id'] = 'observation:initial'
        reparsed = {**original, 'observation_id': 'observation:reparse',
                    'parent_observation_id': original['observation_id'],
                    'processing_basis': 'cached_raw_reparse_no_network',
                    'observed_at': '2026-09-14T03:00:00Z', 'fetched_at': original['observed_at'],
                    'parser_version': 'fixture-v2'}
        result = build_coverage(payload, authority, dictionary, scans, [*observations, reparsed], manifest)
        row = next(row for row in result['rows'] if row['work_id'] == original['work_id'])
        self.assertEqual(row['source_attempt_count'], 2)
        self.assertEqual(result['summary']['all_works']['body_attempted_work_count'], 4)
        self.assertIn('not_http_requests', result['summary']['source_attempt_count_semantics'])
        self.assertEqual(row['source_observations'][0]['processing_basis'], 'cached_raw_reparse_no_network')
        public = result['source_observations'][-1]
        self.assertEqual(public['parent_observation_id'], 'observation:initial')
        self.assertEqual(public['fetched_at'], original['observed_at'])
        self.assertNotIn('cache_ref', public)

    def test_transport_provenance_survives_public_observations_without_inventing_legacy_results(self):
        keys = {'transport_verification', 'transport_complete', 'transport_returncode', 'transport_truncated', 'curl_exit_code'}
        cases = [
            {'transport_verification': 'complete', 'transport_complete': True, 'transport_returncode': 0, 'transport_truncated': False},
            {'transport_verification': 'incomplete', 'transport_complete': False, 'transport_returncode': 28, 'transport_truncated': True, 'curl_exit_code': 28},
            {'transport_verification': 'legacy_unrecorded'},
            {'transport_verification': 'not_requested', 'transport_returncode': None},
        ]
        for transport in cases:
            with self.subTest(transport=transport):
                payload, authority, dictionary, scans, observations, manifest = coverage_fixture()
                original = observations[0]
                original.update(transport)
                if transport['transport_verification'] == 'incomplete':
                    original['status'] = 'partial_text'
                result = build_coverage(payload, authority, dictionary, scans, observations, manifest)
                row = next(row for row in result['rows'] if row['work_id'] == original['work_id'])
                for public in (row['source_observations'][0], result['source_observations'][0]):
                    self.assertEqual({key: value for key, value in public.items() if key in keys}, transport)
                if transport['transport_verification'] == 'legacy_unrecorded':
                    self.assertNotIn('transport_complete', row['source_observations'][0])
                    self.assertNotIn('transport_returncode', result['source_observations'][0])

    def test_141_body_scans_with_empty_receipts_are_zero_declared_AI_reading(self):
        payload, _, manifest = fixture()
        payload['works'] = [make_work(index) for index in range(1, 142)]
        dictionary = dictionary_fixture()
        observations = [observation(work['work_id'], source_url='https://arxiv.org/html/' + work['identifiers']['arxiv'] + 'v1') for work in payload['works']]
        scans = [scan(obs, dictionary, text='No model names.') for obs in observations]
        authority = {key: [] for key in ('devices', 'usage-evidence', 'loco-reviews', 'loco-observations')}
        bundle = build_coverage(payload, authority, dictionary, scans, observations, manifest)
        self.assertEqual(bundle['summary']['all_works']['full_text_screened_current_dictionary_work_count'], 141)
        self.assertEqual(bundle['readings']['records'], [])
        self.assertEqual(bundle['readings']['counts'], {'all_work_count': 0, 'included_work_count': 0, 'receipt_count': 0})
        self.assertEqual(bundle['summary']['article_reading']['all_work_count'], 0)
        self.assertEqual(bundle['readings']['assurance'], ASSURANCE)

    def test_prepared_packet_cannot_be_imported_as_reading_receipt(self):
        args = coverage_fixture()
        forged = {'preparation_status': 'prepared_not_read', 'work_id': args[0]['works'][0]['work_id'],
                  'reading_status': 'completed', 'reader_kind': 'AI'}
        with self.assertRaisesRegex(ValueError, 'fulltext_reading_review'):
            build_coverage(*args, reading_reviews=[forged])

    def test_13_source_version_receipts_deduplicate_works_and_export_original_receipts(self):
        payload, _, manifest = fixture()
        payload['works'] = [make_work(index, status='included' if index <= 7 else 'excluded') for index in range(1, 13)]
        authority = {key: [] for key in ('devices', 'usage-evidence', 'loco-reviews', 'loco-observations')}
        pairs = [public_reading_fixture(work) for work in payload['works']]
        pairs.append(public_reading_fixture(payload['works'][0], 'v2'))
        records, observations = [pair[0] for pair in pairs], [pair[1] for pair in pairs]
        original = copy.deepcopy(records)
        with patch('fulltext_reading_reviews.private_bytes', side_effect=AssertionError('Public export must not open the source cache')):
            bundle = build_coverage(payload, authority, dictionary_fixture(), [], observations, manifest, reading_reviews=records)
        self.assertEqual(records, original)
        self.assertEqual(bundle['readings']['counts'], {'all_work_count': 12, 'included_work_count': 7, 'receipt_count': 13})
        self.assertEqual(bundle['summary']['all_works']['full_text_screened_current_dictionary_work_count'], 0)
        self.assertEqual(bundle['summary']['all_works']['verified_relationship_work_count'], 0)
        self.assertEqual(bundle['readings']['verification_scope'], 'public_metadata_consistency_only_not_re_reading')
        for record in bundle['readings']['records']:
            source_work = next(work for work in payload['works'] if work['work_id'] == record['work_id'])
            self.assertEqual(record['title'], source_work['title'])
            self.assertEqual(record['relevance_status'], source_work['relevance']['status'])
        with tempfile.TemporaryDirectory() as directory, closing(sqlite3.connect(':memory:')) as connection:
            api, downloads = self.export(bundle, directory, connection)
            result = audit_coverage(bundle, api, downloads, connection)
            self.assertEqual(result['article_reading']['receipt_count'], 13)
            saved = json.loads((api / 'coverage-readings.json').read_text())
            self.assertEqual(saved, bundle['readings'])
            receipts = [json.loads(line) for line in (downloads / 'fulltext-readings.jsonl').read_text().splitlines()]
            self.assertTrue(all('title' not in row and 'relevance_status' not in row for row in receipts))
            self.assertEqual(public_audit(receipts, payload, observations, manifest['data_through'])['counts']['AI_read_work_count'], 12)
            self.assertEqual(json.loads(connection.execute("SELECT payload_json FROM coverage_metadata WHERE key='readings'").fetchone()[0]), saved)

    def test_future_dated_receipt_is_not_backdated_into_article_reading_counts(self):
        payload, authority, manifest = fixture()
        record, obs = public_reading_fixture(payload['works'][0])
        record['read_completed_at'] = '2026-09-15T00:00:00Z'
        bundle = build_coverage(payload, authority, dictionary_fixture(), [], [obs], manifest, reading_reviews=[record])
        self.assertEqual(bundle['readings']['counts']['receipt_count'], 0)
        self.assertEqual(bundle['summary']['all_works']['verified_relationship_work_count'], 1)

    def test_independent_review_clock_shows_next_day_sources_and_readings_without_new_corpus_date(self):
        payload, authority, manifest = fixture()
        record, obs = public_reading_fixture(payload['works'][0])
        old_obs = copy.deepcopy(obs)
        obs['observed_at'] = record['observed_at'] = '2026-09-15T00:01:00Z'
        record['read_completed_at'] = '2026-09-15T00:03:00Z'
        dictionary = dictionary_fixture()
        scanned = scan(obs, dictionary, observed_at='2026-09-15T00:02:00Z')
        original = copy.deepcopy((payload, authority, manifest, record, obs, old_obs, scanned))
        old = build_coverage(payload, authority, dictionary, [scanned], [old_obs, obs], manifest, reading_reviews=[record])
        self.assertEqual(old['summary']['as_of'], '2026-09-14')
        self.assertEqual(old['readings']['counts']['receipt_count'], 0)
        reviewed_manifest = {**manifest, 'source_review_as_of': '2026-09-15T00:03:00.123456Z',
                             'source_review_clock_digest': 'a' * 64}
        bundle = build_coverage(payload, authority, dictionary, [scanned], [old_obs, obs], reviewed_manifest, reading_reviews=[record])
        self.assertEqual(bundle['summary']['data_through'], '2026-09-14')
        self.assertEqual(bundle['summary']['as_of'], reviewed_manifest['source_review_as_of'])
        self.assertEqual(bundle['summary']['all_works']['denominator'], old['summary']['all_works']['denominator'])
        self.assertEqual(bundle['rows'][0]['first_public_month'], '2026-08')
        self.assertTrue(bundle['rows'][0]['full_text_screened_current_dictionary'])
        self.assertEqual(bundle['readings']['counts']['receipt_count'], 1)
        self.assertEqual(len(bundle['source_observations']), 2)
        self.assertEqual(bundle['readings']['records'][0]['read_completed_at'], record['read_completed_at'])
        for part in ('summary', 'models', 'readings'):
            for field in ('source_review_as_of', 'source_review_clock_digest'):
                self.assertEqual(bundle[part][field], reviewed_manifest[field])
        self.assertEqual(original, (payload, authority, manifest, record, obs, old_obs, scanned))
        with tempfile.TemporaryDirectory() as directory, closing(sqlite3.connect(':memory:')) as connection:
            api, downloads = self.export(bundle, directory, connection)
            self.assertEqual(audit_coverage(bundle, api, downloads, connection)['article_reading']['receipt_count'], 1)

    def test_same_day_later_reading_is_hidden_but_future_bad_hash_still_fails(self):
        payload, authority, manifest = fixture()
        record, obs = public_reading_fixture(payload['works'][0])
        record['read_completed_at'] = '2026-09-15T23:00:00Z'
        manifest.update(source_review_as_of='2026-09-15T00:01:00Z', source_review_clock_digest='a' * 64)
        bundle = build_coverage(payload, authority, dictionary_fixture(), [], [obs], manifest, reading_reviews=[record])
        self.assertEqual(bundle['readings']['counts']['receipt_count'], 0)
        self.assertEqual(len(bundle['source_observations']), 1)
        record['raw_sha256'] = 'f' * 64
        with self.assertRaises(ValueError):
            build_coverage(payload, authority, dictionary_fixture(), [], [obs], manifest, reading_reviews=[record])

    def test_explicit_malformed_clock_does_not_fall_back_and_subviews_cannot_disagree(self):
        args = coverage_fixture()
        args[-1]['source_review_as_of'] = '2026-09-15T00:00:00Z'
        with self.assertRaises(ValueError): build_coverage(*args)
        args[-1]['source_review_clock_digest'] = 'a' * 64
        bundle = build_coverage(*args)
        bundle['models']['source_review_clock_digest'] = 'b' * 64
        with tempfile.TemporaryDirectory() as directory, closing(sqlite3.connect(':memory:')) as connection:
            api, downloads = self.export(bundle, directory, connection)
            with self.assertRaisesRegex(ValueError, 'review_clock_or_revision_mismatch'):
                audit_coverage(bundle, api, downloads, connection)

    def test_reading_api_download_metadata_and_count_tampering_fail_audit(self):
        for tamper in ('api', 'download_duplicate', 'sqlite', 'count', 'human_claim'):
            with self.subTest(tamper=tamper), tempfile.TemporaryDirectory() as directory, closing(sqlite3.connect(':memory:')) as connection:
                payload, authority, manifest = fixture()
                record, obs = public_reading_fixture(payload['works'][0])
                bundle = build_coverage(payload, authority, dictionary_fixture(), [], [obs], manifest, reading_reviews=[record])
                if tamper == 'count': bundle['readings']['counts']['all_work_count'] += 1
                if tamper == 'human_claim': bundle['readings']['human_reviewed'] = True
                api, downloads = self.export(bundle, directory, connection)
                if tamper == 'api': (api / 'coverage-readings.json').write_text('{}')
                elif tamper == 'download_duplicate':
                    path = downloads / 'fulltext-readings.jsonl'; path.write_text(path.read_text() * 2)
                elif tamper == 'sqlite': connection.execute("UPDATE coverage_metadata SET payload_json='{}' WHERE key='readings'")
                with self.assertRaisesRegex(ValueError, 'hardware_coverage'):
                    audit_coverage(bundle, api, downloads, connection)


if __name__ == "__main__":
    unittest.main()
