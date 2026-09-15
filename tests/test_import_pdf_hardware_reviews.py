import contextlib
import copy
import hashlib
import io
import json
import socket
import sqlite3
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import import_pdf_hardware_reviews as hardware
import pdf_reading_reviews as pdf
import test_pdf_reading_reviews as fixtures
from catalog_store import encode, fingerprint
from equipment_radar import (TABLES, audit_equipment, build_equipment_bundle,
                             equipment_sqlite, export_equipment)
from source_review_clock import LEDGER_PATHS, resolve_source_review_clock


class PdfHardwareReviewTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.PdfReadingReviewsTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.payload = self.fixture.payload
        self.payload['works'][0].update(first_public_date='2026-08-01', first_public_date_precision='day', abstract='')
        self.material = self.fixture.validate(self.fixture.with_reading())
        self.as_of = self.fixture.as_of
        self.directory = self.root / 'data/equipment'
        self.directory.mkdir(parents=True)
        self.authority = {key: [] for key in TABLES}
        self.authority['devices'] = [{
            'hardware_id': 'hardware:nvidia-h200', 'slug': 'nvidia-h200', 'name': 'NVIDIA H200',
            'aliases': ['H200'], 'vendor': 'NVIDIA', 'identity_level': 'model_specified',
            'category': 'compute_platform', 'official_url': 'https://www.nvidia.com/en-us/data-center/h200/'}]
        self.write_authority()
        self.reset_review()

    def reset_review(self):
        source, reading = self.material['sources'][0], self.material['readings'][0]
        self.review = {
            'work_id': source['work_id'], 'hardware_id': 'hardware:nvidia-h200', 'reported_device_name': 'NVIDIA H200',
            'role': 'training_compute', 'setting': 'dataset', 'usage_scope': 'study',
            'configuration': '32 GPUs for one stage; 8 for another; not a GPU purchase count.',
            'validation_context': 'source_reported_model_training_compute',
            'statement_zh': '测试用页绑定AI设备声明，不代表独立实验验证。',
            'source_observation_id': source['source_observation_id'], 'reading_id': reading['reading_id'],
            'manifestation_id': source['manifestation_id'], 'source_url': source['source_url'],
            'source_version': source['version'], 'pdf_sha256': source['pdf_sha256'],
            'observed_at': source['observed_at'], 'reviewed_at': '2026-09-14T01:45:00Z',
            'source_pages': [2], 'page_text_sha256': {'2': source['page_text_sha256']['2']},
            'reviewer_kind': 'AI', 'review_scope': 'hardware_use_assertions_only',
        }
        self.input = {'schema_version': '1', 'reviews': [self.review]}

    def write_authority(self):
        for key, rows in self.authority.items():
            (self.directory / (key + '.jsonl')).write_text(''.join(encode(row) + '\n' for row in rows))

    def prepare(self):
        return hardware.prepare_reviews(self.input, self.payload, self.authority,
                                        self.material['sources'], self.material['readings'], self.as_of)

    def run_import(self, **kwargs):
        return hardware.import_reviews(self.input, self.payload, self.directory,
                                       self.material['sources'], self.material['readings'], self.as_of, **kwargs)

    def audit(self, authority):
        return hardware.audit_pdf_hardware_usage(self.payload, authority,
            self.material['sources'], self.material['readings'], self.as_of)

    def test_valid_complete_reading_and_page_proof_no_independence_claim(self):
        merged, report = self.prepare()
        self.assertEqual(report['added'], {'usage-evidence': 1})
        self.assertEqual(report['devices_created'], 0)
        self.assertEqual(self.authority['usage-evidence'], [])
        row = merged['usage-evidence'][0]
        self.assertEqual(row['source_version'], None)  # conference edition, not invented v1
        self.assertEqual(row['pdf_evidence']['reading_id'], self.review['reading_id'])
        self.assertEqual(row['pdf_evidence']['page_text_sha256'], self.review['page_text_sha256'])
        self.assertEqual(row['source_locator'], 'PDF pages 2')
        self.assertFalse(row['human_reviewed'])
        self.assertFalse(row['independently_verified'])
        self.assertFalse(row['full_experiment_verified'])
        self.assertNotIn(str(self.fixture.cache), encode(row))
        self.assertNotIn('cache_ref', encode(row))

    def test_arxiv_version_retained_and_wrong_version_rejected(self):
        address = 'https://arxiv.org/abs/2409.11952'
        self.payload['works'][0]['identifiers'] = {'arxiv': '2409.11952', 'doi': None}
        self.payload['manifestations'][0].update(url=address, venue='arXiv', kind='preprint')
        self.payload['source-records'][0]['url'] = address
        self.payload['text-snapshots'] = [{'work_id': 'work:test', 'source_url': address + 'v1', 'version': 'v1'}]
        source = self.fixture.input['sources'][0]
        source['landing']['url'] = address + 'v1'
        source['pdf']['url'] = 'https://arxiv.org/pdf/2409.11952v1'
        self.fixture.replace_html(self.fixture.input, self.fixture.html.replace(
            b'https://files.example.org/paper.pdf', b'https://arxiv.org/pdf/2409.11952v1'))
        self.material = self.fixture.validate(self.fixture.with_reading())
        self.reset_review()
        merged, _ = self.prepare()
        self.assertEqual(merged['usage-evidence'][0]['source_version'], 'v1')
        for value in ['v2', None, '']:
            self.review['source_version'] = value
            with self.assertRaisesRegex(ValueError, 'binding_mismatch'):
                self.prepare()

    def arxiv_relative_anchor_fixture(self):
        address = 'https://arxiv.org/abs/2409.11952'
        target = 'https://arxiv.org/pdf/2409.11952v1'
        self.payload['works'][0]['identifiers'] = {'arxiv': '2409.11952', 'doi': None}
        self.payload['manifestations'][0].update(url=address, venue='arXiv', kind='preprint')
        self.payload['source-records'][0]['url'] = address
        self.payload['text-snapshots'] = [{'work_id': 'work:test', 'source_url': address + 'v1', 'version': 'v1'}]
        source = self.fixture.input['sources'][0]
        source['landing']['url'] = address + 'v1'
        source['pdf']['url'] = target
        raw = self.fixture.html.replace(b'https://files.example.org/paper.pdf', target.encode())
        raw = raw.replace(('href="' + target + '"').encode(), b'href="/pdf/2409.11952v1"')
        self.fixture.replace_html(self.fixture.input, raw)
        self.material = self.fixture.validate(self.fixture.with_reading())
        self.reset_review()

    def test_official_arxiv_relative_anchor_keeps_original_metadata_and_hash(self):
        self.arxiv_relative_anchor_fixture()
        before = copy.deepcopy(self.material)
        self.assertEqual(before['sources'][0]['pdf_link_evidence']['anchor_href'], '/pdf/2409.11952v1')
        merged, _ = self.prepare()
        self.assertEqual(self.audit(merged)['pdf_usage_count'], 1)
        self.assertEqual(self.material, before)
        self.assertEqual(merged['usage-evidence'][0]['pdf_evidence']['source_metadata_sha256'],
                         before['sources'][0]['metadata_sha256'])
        self.assertEqual(merged['usage-evidence'][0]['source_url'], 'https://arxiv.org/pdf/2409.11952v1')

    def test_private_relative_href_is_rejected_even_if_it_resolves_to_the_valid_pdf(self):
        self.arxiv_relative_anchor_fixture()
        original = copy.deepcopy(self.material)
        for href in ('/private/../pdf/2409.11952v1', '/var/../pdf/2409.11952v1', '\n/pdf/2409.11952v1'):
            with self.subTest(href=href):
                self.material = copy.deepcopy(original)
                source = self.material['sources'][0]
                source['pdf_link_evidence']['anchor_href'] = href
                source['metadata_sha256'] = fingerprint({key: value for key, value in source.items()
                                                        if key != 'metadata_sha256'})
                if href.startswith('/var/'):
                    # Generic public PDF metadata accepts this URL resolution;
                    # the hardware audit must still reject the private prefix.
                    pdf.public_audit(self.material['readings'], self.payload, self.material['sources'], self.as_of)
                with self.assertRaisesRegex(ValueError, 'private|invalid_'):
                    self.prepare()

    def test_relative_href_exception_does_not_relax_other_source_or_assertion_fields(self):
        self.arxiv_relative_anchor_fixture()
        source = self.material['sources'][0]
        source['identity_check']['reason_zh'] = '来源确认，内部路径 /var/cache/paper.pdf'
        source['metadata_sha256'] = fingerprint({key: value for key, value in source.items() if key != 'metadata_sha256'})
        with self.assertRaisesRegex(ValueError, 'private_path'):
            self.prepare()
        self.arxiv_relative_anchor_fixture()
        self.review['configuration'] = '/pdf/2409.11952v1'
        with self.assertRaisesRegex(ValueError, 'private_path'):
            self.prepare()

    def test_relative_anchor_cannot_change_to_another_public_pdf_or_skip_metadata_hash(self):
        self.arxiv_relative_anchor_fixture()
        source = self.material['sources'][0]
        source['pdf_link_evidence']['anchor_href'] = '/pdf/2409.99999v1'
        source['metadata_sha256'] = fingerprint({key: value for key, value in source.items() if key != 'metadata_sha256'})
        with self.assertRaisesRegex(ValueError, 'anchor_binding'):
            self.prepare()
        self.arxiv_relative_anchor_fixture()
        self.material['sources'][0]['metadata_sha256'] = 'f' * 64
        with self.assertRaisesRegex(ValueError, 'metadata_hash'):
            self.prepare()

    def test_download_or_identity_check_without_complete_reading_rejected(self):
        self.material['readings'] = []
        with self.assertRaisesRegex(ValueError, 'complete_reading_and_source_required'):
            self.prepare()
        self.material['sources'] = []
        with self.assertRaisesRegex(ValueError, 'complete_reading_and_source_required'):
            self.prepare()

    def test_incomplete_or_unverified_public_reading_rejected(self):
        for key, value in [('read_pages', [1]), ('reading_status', 'prepared'), ('reader_kind', 'human'),
                           ('human_reviewed', True), ('understanding_verified', True)]:
            with self.subTest(key=key):
                material = copy.deepcopy(self.material)
                self.material['readings'][0][key] = value
                with self.assertRaises(ValueError):
                    self.prepare()
                self.material = material

    def test_work_manifestation_pdf_url_version_hash_and_source_ids_must_match(self):
        for key, value in [('work_id', 'work:other'), ('manifestation_id', 'manifest:other'),
                           ('pdf_sha256', 'f' * 64), ('source_version', 'v2'),
                           ('source_url', 'https://files.example.org/other.pdf'),
                           ('reading_id', 'pdf-reading:missing'), ('source_observation_id', 'pdf-source:missing'),
                           ('observed_at', '2026-09-14T01:02:00Z')]:
            with self.subTest(key=key):
                original = self.review[key]
                self.review[key] = value
                with self.assertRaises(ValueError):
                    self.prepare()
                self.review[key] = original

    def test_pages_outside_coverage_duplicate_bool_unsorted_or_wrong_hash_rejected(self):
        for pages in ([], [0], [3], [True], [2, 2], [2, 1], ['2']):
            with self.subTest(pages=pages):
                self.review['source_pages'] = pages
                with self.assertRaises(ValueError):
                    self.prepare()
        self.review['source_pages'] = [2]
        for hashes in ({}, {'02': 'a' * 64}, {'1': 'a' * 64, '2': 'b' * 64}, {'2': 'f' * 64}, {'2': 'bad'}):
            self.review['page_text_sha256'] = hashes
            with self.assertRaises(ValueError):
                self.prepare()

    def test_source_and_reading_metadata_tampering_fail_without_private_files(self):
        for group, key, value in [('sources', 'page_text_sha256', {'1': 'a' * 64, '2': 'b' * 64}),
                                  ('sources', 'metadata_sha256', 'f' * 64),
                                  ('readings', 'declaration_sha256', 'f' * 64)]:
            old = self.material[group][0][key]
            self.material[group][0][key] = value
            with self.assertRaises(ValueError):
                self.prepare()
            self.material[group][0][key] = old

    def test_review_clock_bounds_are_inclusive_and_have_no_now_fallback(self):
        for when in ('2026-09-14T01:30:00Z', self.as_of):
            self.review['reviewed_at'] = when
            self.prepare()
        for when in ('2026-09-14T01:29:59Z', '2026-09-14T02:00:01Z', '2026-09-14'):
            self.review['reviewed_at'] = when
            with self.assertRaises(ValueError):
                self.prepare()
        self.review['reviewed_at'] = self.as_of
        self.as_of = None
        with self.assertRaises(ValueError):
            self.prepare()

    def test_unknown_hardware_alias_mismatch_and_unresolved_cross_work_identity(self):
        for key, value in [('hardware_id', 'hardware:new-model'), ('reported_device_name', 'NVIDIA H100')]:
            original = self.review[key]
            self.review[key] = value
            with self.assertRaises(ValueError):
                self.prepare()
            self.review[key] = original
        self.review['reported_device_name'] = 'H200'
        self.prepare()
        self.authority['devices'][0].update(identity_level='family_only', identity_context_work_id='work:other')
        with self.assertRaisesRegex(ValueError, 'cross_work'):
            self.prepare()

    def test_roles_and_hardware_categories_cannot_be_faked(self):
        for role, setting in [('mentioned', 'real'), ('dataset_source', 'dataset'), ('made_up', 'dataset'),
                               ('real_robot', 'simulation'), ('simulated_robot', 'real')]:
            self.review.update(role=role, setting=setting)
            with self.assertRaises(ValueError):
                self.prepare()
        self.reset_review()
        self.authority['devices'][0]['category'] = 'robot_platform'
        with self.assertRaisesRegex(ValueError, 'compute_role'):
            self.prepare()

    def test_private_paths_controls_unknown_keys_and_nonfinite_rejected(self):
        for value in ['/Users/alice/private.txt', 'source file:///private/cache/a.pdf', 'file:cache/page.pdf', '.research/pdf/page.txt',
                      'C:\\Users\\alice\\paper.pdf', 'Saved to /var/tmp/a', '~/secret', 'text\nprivate']:
            self.review['configuration'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.prepare()
        self.reset_review()
        self.review['cache_ref'] = 'not-exported-but-forbidden'
        with self.assertRaisesRegex(ValueError, 'unknown_or_missing_fields'):
            self.prepare()
        for raw in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
            with self.assertRaises(ValueError):
                hardware.strict_json(raw)

    def test_ordinary_profile_label_is_not_a_file_URI(self):
        self.review['configuration'] = 'power profile: standard; thermal profile: steady'
        self.prepare()
        self.review['configuration'] = 'public profile: file:///private/cache.pdf'
        with self.assertRaisesRegex(ValueError, 'private_path'):
            self.prepare()

    def test_duplicate_semantics_ignore_URL_pages_version_prose_and_configuration(self):
        merged, _ = self.prepare()
        original = merged['usage-evidence'][0]
        legacy = {key: value for key, value in original.items()
                  if key not in {'source_format', 'pdf_evidence', 'review_scope'}}
        legacy.update(usage_id='usage:legacy-html', source_url=self.material['sources'][0]['landing_url'],
                      source_locator='Section 5', configuration='A different configuration')
        self.authority['usage-evidence'] = [legacy]
        with self.assertRaisesRegex(ValueError, 'duplicate_cross_source'):
            self.prepare()
        # The public audit also rejects an HTML use added AFTER a PDF use.
        merged['usage-evidence'].append(legacy)
        with self.assertRaisesRegex(ValueError, 'duplicate_cross_source'):
            self.audit(merged)
        self.authority['usage-evidence'] = [original]
        self.review['source_pages'] = [1]
        self.review['page_text_sha256'] = {'1': self.material['sources'][0]['page_text_sha256']['1']}
        with self.assertRaisesRegex(ValueError, 'existing_PDF_usage_conflict'):
            self.prepare()

    def test_legacy_per_locator_behavior_preserved_when_no_pdf_proof_present(self):
        merged, _ = self.prepare()
        base = {key: value for key, value in merged['usage-evidence'][0].items()
                if key not in {'source_format', 'pdf_evidence', 'review_scope'}}
        merged['usage-evidence'] = [{**base, 'usage_id': 'usage:old1', 'source_locator': 'Sec 1'},
                                     {**base, 'usage_id': 'usage:old2', 'source_locator': 'Sec 2'}]
        self.assertEqual(self.audit(merged)['pdf_usage_count'], 0)

    def test_duplicate_batch_rejected_but_distinct_roles_and_scopes_allowed(self):
        self.input['reviews'].append(copy.deepcopy(self.review))
        with self.assertRaisesRegex(ValueError, 'duplicate_cross_source'):
            self.prepare()
        self.input['reviews'][1]['role'] = 'inference_compute'
        self.assertEqual(self.prepare()[1]['added']['usage-evidence'], 2)
        self.input['reviews'][1].update(role='training_compute', usage_scope='baseline')
        self.assertEqual(self.prepare()[1]['added']['usage-evidence'], 2)

    def test_invalid_second_source_or_duplicate_receipt_does_not_hide_from_audit(self):
        for table in ('sources', 'readings'):
            self.material[table].append(copy.deepcopy(self.material[table][0]))
            with self.assertRaises(ValueError):
                self.prepare()
            self.material[table].pop()

    def test_page_proof_can_reference_multiple_pages_but_cannot_omit_any_hash(self):
        self.review['source_pages'] = [1, 2]
        self.review['page_text_sha256'] = copy.deepcopy(self.material['sources'][0]['page_text_sha256'])
        merged, _ = self.prepare()
        self.assertEqual(merged['usage-evidence'][0]['source_locator'], 'PDF pages 1, 2')
        self.review['page_text_sha256'].pop('1')
        with self.assertRaisesRegex(ValueError, 'exact_page_hash_keys'):
            self.prepare()

    def test_every_public_proof_and_visible_assertion_is_bound(self):
        merged, _ = self.prepare()
        mutations = [lambda row: row['pdf_evidence'].update(page_text_sha256={'2': 'f' * 64}),
                     lambda row: row['pdf_evidence'].update(reading_declaration_sha256='f' * 64),
                     lambda row: row.update(statement='被替换的中文断言'),
                     lambda row: row.update(configuration='different configuration'),
                     lambda row: row.update(human_reviewed=True),
                     lambda row: row.update(independently_verified=0),
                     lambda row: row.pop('pdf_evidence'),
                     lambda row: row.update(source_format='html'),
                     lambda row: row.update(usage_id='usage:forged'),
                     lambda row: row['pdf_evidence'].update(cache_ref='/Users/private/file')]
        for mutate in mutations:
            candidate = copy.deepcopy(merged)
            mutate(candidate['usage-evidence'][0])
            with self.assertRaises(ValueError):
                self.audit(candidate)

    def test_public_audit_never_reads_files_parses_pdf_or_uses_network(self):
        merged, _ = self.prepare()
        with patch.object(Path, 'read_bytes', side_effect=AssertionError('file read')), \
                patch.object(Path, 'read_text', side_effect=AssertionError('file read')), \
                patch.object(pdf, 'extract_pdf', side_effect=AssertionError('PDF parse')), \
                patch.object(pdf, 'private_bytes', side_effect=AssertionError('private cache')), \
                patch.object(socket, 'socket', side_effect=AssertionError('network')):
            report = self.audit(merged)
        self.assertEqual(report['pdf_usage_count'], 1)
        self.assertFalse(report['private_source_reverified'])

    def test_default_dryrun_apply_only_usage_and_exact_replay_no_write(self):
        before = {path.name: path.read_bytes() for path in self.directory.iterdir()}
        self.assertFalse(self.run_import()['applied'])
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.directory.iterdir()})
        self.assertTrue(self.run_import(apply=True)['applied'])
        after = {path.name: path.read_bytes() for path in self.directory.iterdir()}
        for key in before:
            if key != 'usage-evidence.jsonl':
                self.assertEqual(before[key], after[key])
        with patch.object(hardware.os, 'replace', side_effect=AssertionError('no replay write')):
            self.assertEqual(self.run_import(apply=True)['added']['usage-evidence'], 0)
        self.review['configuration'] = 'another config'
        with self.assertRaisesRegex(ValueError, 'existing_PDF_usage_conflict'):
            self.run_import(apply=True)
        self.assertEqual(after, {path.name: path.read_bytes() for path in self.directory.iterdir()})

    def test_preflight_invalid_second_row_or_changed_authority_writes_nothing(self):
        before = (self.directory / 'usage-evidence.jsonl').read_bytes()
        bad = copy.deepcopy(self.review)
        bad.update(role='inference_compute', pdf_sha256='f' * 64)
        self.input['reviews'].append(bad)
        with self.assertRaises(ValueError):
            self.run_import(apply=True)
        self.assertEqual((self.directory / 'usage-evidence.jsonl').read_bytes(), before)
        self.input['reviews'].pop()
        def change():
            (self.directory / 'devices.jsonl').write_text('changed by concurrent writer\n')
        with self.assertRaisesRegex(ValueError, 'authority_changed'):
            self.run_import(apply=True, before_write=change)
        self.assertEqual((self.directory / 'usage-evidence.jsonl').read_bytes(), before)

    def test_concurrent_edit_while_tempfile_is_written_is_never_overwritten(self):
        target = self.directory / 'usage-evidence.jsonl'
        original_fsync = hardware.os.fsync
        def concurrent_edit(descriptor):
            original_fsync(descriptor)
            target.write_text('concurrent editor content\n')
        with patch.object(hardware.os, 'fsync', side_effect=concurrent_edit):
            with self.assertRaisesRegex(ValueError, 'authority_changed'):
                self.run_import(apply=True)
        self.assertEqual(target.read_text(), 'concurrent editor content\n')
        self.assertEqual(list(self.directory.glob('.pdf-hardware-*.tmp')), [])

    def test_before_write_guard_runs_again_immediately_before_replace(self):
        guard = unittest.mock.Mock(side_effect=[None, ValueError('late catalog mutation')])
        before = (self.directory / 'usage-evidence.jsonl').read_bytes()
        with self.assertRaisesRegex(ValueError, 'late catalog mutation'):
            self.run_import(apply=True, before_write=guard)
        self.assertEqual(guard.call_count, 2)
        self.assertEqual((self.directory / 'usage-evidence.jsonl').read_bytes(), before)
        self.assertEqual(list(self.directory.glob('.pdf-hardware-*.tmp')), [])

    def test_symlink_usage_output_rejected(self):
        target = self.directory / 'usage-evidence.jsonl'
        other = self.root / 'other.jsonl'
        target.rename(other)
        target.symlink_to(other)
        with self.assertRaisesRegex(ValueError, 'unsafe_file'):
            self.run_import(apply=True)
        self.assertEqual(other.read_bytes(), b'')

    def test_equipment_jsonl_API_and_sqlite_roundtrip_keeps_pdf_proof(self):
        merged, _ = self.prepare()
        manifest = {'dataset_version': 'pdf-hardware-test', 'data_through': '2026-09-14',
                    'complete_months': ['2026-08'], 'provisional_month': '2026-09',
                    'source_review_as_of': self.as_of, 'source_review_clock_digest': 'c' * 64}
        bundle = build_equipment_bundle(self.payload, merged, manifest)
        api, downloads = self.root / 'api', self.root / 'downloads'
        export_equipment(bundle, api, downloads)
        with contextlib.closing(sqlite3.connect(':memory:')) as connection:
            equipment_sqlite(connection, bundle)
            audit_equipment(bundle, api, downloads, connection)
            row = json.loads(connection.execute('SELECT payload_json FROM equipment_usage_evidence').fetchone()[0])
            self.assertEqual(row['pdf_evidence']['reading_id'], self.review['reading_id'])
        self.assertEqual(self.audit(bundle['tables'])['pdf_usage_count'], 1)
        public = (downloads / 'usage-evidence.jsonl').read_text()
        self.assertIn('page_text_sha256', public)
        self.assertNotIn(str(self.fixture.cache), public)
        self.assertEqual(bundle['index']['counts']['works'], 1)

    def test_audit_equipment_main_passes_public_sources_and_receipts_and_rejects_orphan(self):
        import audit_equipment as command
        from pdf_coverage_export import API, SOURCE_DOWNLOAD, READING_DOWNLOAD
        merged, _ = self.prepare()
        manifest = {'dataset_version': 'main-pdf-hardware-test', 'data_through': '2026-09-14',
                    'complete_months': ['2026-08'], 'provisional_month': '2026-09',
                    'source_review_as_of': self.as_of, 'source_review_clock_digest': 'c' * 64,
                    'equipment': {'coverage_api': '/api/v1/equipment/coverage-summary.json',
                        'readings_api': '/api/v1/equipment/coverage-readings.json', 'pdf_readings_api': API},
                    'downloads': {'hardware_coverage': '/downloads/equipment/hardware-coverage.jsonl.gz',
                        'fulltext_readings': '/downloads/equipment/fulltext-readings.jsonl',
                        'pdf_readings': READING_DOWNLOAD, 'pdf_source_observations': SOURCE_DOWNLOAD,
                        'sqlite': '/downloads/radar.sqlite.zip'}}
        api = self.root / 'docs/public/api/v1'
        api.mkdir(parents=True)
        (api / 'catalog-manifest.json').write_text(encode(manifest))
        database = self.root / 'audit.sqlite'
        sqlite3.connect(database).close()
        def public_table(_, key):
            return {'pdf-source-observations': self.material['sources'],
                    'pdf-readings': self.material['readings']}.get(key, [])
        coverage = {'rows': [{'work_id': 'work:test'}],
                    'summary': {'dictionary_hash': 'dictionary', 'all_works': {}, 'included': {}},
                    'readings': {'counts': {}}}
        clock = {key: manifest[key] for key in ('source_review_as_of', 'source_review_clock_digest')}
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(command, 'ROOT', self.root))
            stack.enter_context(patch.object(command, 'load_catalog', return_value=(self.payload, {})))
            stack.enter_context(patch.object(command, 'load_equipment_authority', return_value=merged))
            stack.enter_context(patch.object(command, 'load_hardware_dictionary', return_value={}))
            stack.enter_context(patch.object(command, 'read_table', side_effect=public_table))
            stack.enter_context(patch.object(command, 'build_coverage', return_value=coverage))
            stack.enter_context(patch.object(command, 'local_sqlite_path', return_value=database))
            stack.enter_context(patch.object(command, 'verify_archive', return_value={}))
            for name in ('audit_equipment', 'audit_coverage', 'audit_pdf_coverage'):
                stack.enter_context(patch.object(command, name, return_value={}))
            stack.enter_context(patch('source_review_clock.resolve_source_review_clock', return_value=clock))
            spy = stack.enter_context(patch.object(command, 'audit_pdf_hardware_usage', wraps=hardware.audit_pdf_hardware_usage))
            stack.enter_context(patch.object(pdf, 'private_bytes', side_effect=AssertionError('private cache')))
            stack.enter_context(patch.object(pdf, 'extract_pdf', side_effect=AssertionError('parse PDF')))
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                command.main()
            self.assertEqual(json.loads(stdout.getvalue())['pdf_hardware_usage']['pdf_usage_count'], 1)
            self.assertEqual(spy.call_args.args[2:], (self.material['sources'], self.material['readings'], self.as_of))
            merged['usage-evidence'][0]['pdf_evidence']['reading_id'] = 'pdf-reading:orphan'
            with self.assertRaisesRegex(ValueError, 'complete_reading_and_source_required'):
                command.main()

    def make_approved_clock(self):
        manifest = self.root / 'data/catalog/manifest.json'
        manifest.parent.mkdir(parents=True, exist_ok=True)
        if not manifest.exists():
            manifest.write_text(encode({'data_through': '2026-09-14'}))
        for relative in LEDGER_PATHS:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_text('')
        for filename, key in [('pdf-source-observations', 'sources'), ('pdf-readings', 'readings')]:
            (self.root / ('data/hardware-review/' + filename + '.jsonl')).write_text(
                ''.join(encode(row) + '\n' for row in self.material[key]))
        value = {'schema_version': '1', 'source_review_as_of': self.as_of,
                 'ledger_sha256': {relative: hashlib.sha256((self.root / relative).read_bytes()).hexdigest()
                                   for relative in LEDGER_PATHS}}
        config = self.root / 'config/source-review-clock.json'
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text(encode(value))
        return config

    def test_CLI_requires_actual_approved_bound_clock_and_never_rewrites_it(self):
        source = self.root / 'input.json'
        source.write_text(encode(self.input))
        args = ['--input', str(source), '--root', str(self.root)]
        with patch.object(hardware, 'load_catalog', return_value=(self.payload, {'data_through': '2026-09-14'})):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                hardware.main(args)  # no configured approval, no legacy fallback
            config = self.make_approved_clock()
            before = config.read_bytes()
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(hardware.main(args), 0)
                self.assertEqual(hardware.main(args + ['--apply']), 0)
            self.assertEqual(before, config.read_bytes())
            with self.assertRaisesRegex(ValueError, 'ledger_hash_mismatch'):
                resolve_source_review_clock(self.root, '2026-09-14')
            self.make_approved_clock()  # explicit owner approval for changed ledger
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(hardware.main(args + ['--apply']), 0)

    def test_CLI_preview_clock_is_dryrun_only(self):
        config = self.make_approved_clock()
        preview = config.with_name('pdf-preview.json')
        preview.write_bytes(config.read_bytes())
        source = self.root / 'input.json'
        source.write_text(encode(self.input))
        args = ['--input', str(source), '--root', str(self.root), '--clock-config', str(preview)]
        before = (self.directory / 'usage-evidence.jsonl').read_bytes()
        with patch.object(hardware, 'load_catalog', return_value=(self.payload, {'data_through': '2026-09-14'})):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(hardware.main(args), 0)
            with contextlib.redirect_stderr(io.StringIO()) as stderr, self.assertRaises(SystemExit):
                hardware.main(args + ['--apply'])
            self.assertIn('apply_requires_default_approved_clock', stderr.getvalue())
        self.assertEqual((self.directory / 'usage-evidence.jsonl').read_bytes(), before)

    def test_CLI_rechecks_logical_catalog_even_when_manifest_and_clock_unchanged(self):
        self.make_approved_clock()
        source = self.root / 'input.json'
        source.write_text(encode(self.input))
        args = ['--input', str(source), '--root', str(self.root), '--apply']
        changed = copy.deepcopy(self.payload)
        changed['works'][0]['work_id'] = 'work:canonical-merge-target'
        loads = [(self.payload, {'data_through': '2026-09-14'})] * 3 + [(changed, {'data_through': '2026-09-14'})]
        before = (self.directory / 'usage-evidence.jsonl').read_bytes()
        with patch.object(hardware, 'load_catalog', side_effect=loads):
            with contextlib.redirect_stderr(io.StringIO()) as stderr, self.assertRaises(SystemExit):
                hardware.main(args)
            self.assertIn('catalog_changed_during_import', stderr.getvalue())
        self.assertEqual((self.directory / 'usage-evidence.jsonl').read_bytes(), before)
        self.assertEqual(list(self.directory.glob('.pdf-hardware-*.tmp')), [])

    def test_CLI_rechecks_catalog_manifest_identity_during_temp_write(self):
        self.make_approved_clock()
        source = self.root / 'input.json'
        source.write_text(encode(self.input))
        args = ['--input', str(source), '--root', str(self.root), '--apply']
        original_fsync = hardware.os.fsync
        def replace_manifest(descriptor):
            original_fsync(descriptor)
            # Same parsed metadata, different manifest identity/bytes.
            (self.root / 'data/catalog/manifest.json').write_text('{ "data_through": "2026-09-14" }\n')
        before = (self.directory / 'usage-evidence.jsonl').read_bytes()
        with patch.object(hardware, 'load_catalog', return_value=(self.payload, {'data_through': '2026-09-14'})), \
                patch.object(hardware.os, 'fsync', side_effect=replace_manifest):
            with contextlib.redirect_stderr(io.StringIO()) as stderr, self.assertRaises(SystemExit):
                hardware.main(args)
            self.assertIn('catalog_changed_during_import', stderr.getvalue())
        self.assertEqual((self.directory / 'usage-evidence.jsonl').read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
