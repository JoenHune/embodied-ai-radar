import copy
import json
import sqlite3
import sys
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import test_pdf_reading_reviews as fixtures
from pdf_coverage_export import (build_pdf_coverage, export_pdf_coverage, pdf_coverage_sqlite,
                                 audit_pdf_coverage, pdf_summary, attach_pdf_coverage)


class PdfCoverageExportTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.PdfReadingReviewsTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.material = self.fixture.validate(self.fixture.with_reading())
        self.manifest = {'dataset_version': 'pdf-revision', 'data_through': '2026-09-14'}

    def build(self, readings=None):
        return build_pdf_coverage(self.fixture.payload, self.material['sources'],
            self.material['readings'] if readings is None else readings, self.manifest, 'dictionary-hash')

    def test_counts_scope_and_catalog_overlay_without_mutating_authority(self):
        before = copy.deepcopy(self.material)
        bundle = self.build()
        self.assertEqual(self.material, before)
        self.assertEqual(bundle['records'][0]['title'], 'Test Robotics Paper')
        self.assertEqual(bundle['counts']['included_work_count'], 1)
        self.assertEqual(bundle['counts']['included_source_work_count'], 1)
        self.assertEqual(bundle['dataset_version'], 'pdf-revision')
        self.assertEqual(pdf_summary(bundle)['overlap_policy'], 'not_additive_with_HTML_work_counts')
        self.assertFalse(bundle['human_reviewed'])
        self.assertFalse(bundle['private_source_reverified'])

    def test_acquired_and_identity_checked_source_does_not_create_reading(self):
        bundle = self.build([])
        self.assertEqual(bundle['counts']['source_count'], 1)
        self.assertEqual(bundle['counts']['receipt_count'], 0)
        self.assertEqual(bundle['counts']['all_work_count'], 0)
        self.assertEqual(bundle['records'], [])

    def test_excluded_work_retained_but_not_included_count(self):
        self.fixture.payload['works'][0]['relevance']['status'] = 'excluded'
        bundle = self.build()
        self.assertEqual(bundle['counts']['all_work_count'], 1)
        self.assertEqual(bundle['counts']['included_work_count'], 0)
        self.assertEqual(bundle['records'][0]['relevance_status'], 'excluded')

    def test_roundtrip_public_api_downloads_and_typed_sqlite(self):
        bundle = self.build()
        api, downloads = self.fixture.root / 'api', self.fixture.root / 'downloads'
        export_pdf_coverage(bundle, api, downloads)
        with closing(sqlite3.connect(':memory:')) as db:
            pdf_coverage_sqlite(db, bundle)
            with patch('pdf_reading_reviews.extract_pdf', side_effect=AssertionError('public audit must not reread')):
                result = audit_pdf_coverage(bundle, self.fixture.payload, api, downloads, db)
            self.assertEqual(result['status'], 'passed')
            self.assertEqual(result['all_work_count'], 1)
            self.assertEqual(db.execute('SELECT page_count FROM pdf_reading_receipts').fetchone()[0], 2)
        raw = (downloads / 'pdf-readings.jsonl').read_text()
        self.assertNotIn('"title"', raw)
        self.assertNotIn('cache_ref', raw)
        self.assertNotIn(str(self.fixture.cache), raw)
        self.assertIn('source_pages', raw)

    def test_api_download_or_sqlite_tampering_is_rejected(self):
        for tamper in ('api', 'download', 'typed', 'payload'):
            with self.subTest(tamper=tamper), closing(sqlite3.connect(':memory:')) as db:
                bundle = self.build()
                api, downloads = self.fixture.root / tamper / 'api', self.fixture.root / tamper / 'downloads'
                export_pdf_coverage(bundle, api, downloads)
                pdf_coverage_sqlite(db, bundle)
                if tamper == 'api':
                    value = copy.deepcopy(bundle)
                    value['counts']['all_work_count'] = 999
                    (api / 'coverage-pdf-readings.json').write_text(json.dumps(value))
                elif tamper == 'download':
                    (downloads / 'pdf-readings.jsonl').write_text('')
                elif tamper == 'typed':
                    db.execute('UPDATE pdf_reading_receipts SET page_count=99')
                else:
                    db.execute("UPDATE pdf_source_observations SET payload_json='{}'")
                with self.assertRaises(ValueError):
                    audit_pdf_coverage(bundle, self.fixture.payload, api, downloads, db)

    def test_missing_revision_or_duplicate_canonical_rejected(self):
        for manifest in ({}, {'data_through': '2026-09-14'}):
            with self.assertRaisesRegex(ValueError, 'revision_required'):
                build_pdf_coverage(self.fixture.payload, [], [], manifest, 'dictionary')
        self.fixture.payload['works'] *= 2
        with self.assertRaisesRegex(ValueError, 'duplicate_canonical'):
            self.build()

    def test_per_work_projection_distinguishes_PDF_from_HTML_not_attempted(self):
        bundle = self.build()
        html = {'rows': [{'work_id': 'work:test', 'body_source_state': 'not_attempted'},
                         {'work_id': 'another', 'body_source_state': 'not_attempted'}], 'summary': {}}
        attach_pdf_coverage(html, bundle)
        self.assertEqual(html['rows'][0]['pdf'], {'source_count': 1, 'reading_count': 1})
        self.assertEqual(html['rows'][0]['body_source_state'], 'not_attempted')
        self.assertNotIn('pdf', html['rows'][1])
        self.assertIn('arxiv_HTML_only', html['summary']['body_source_scope'])
        before = copy.deepcopy(html)
        attach_pdf_coverage(html, bundle)
        self.assertEqual(html, before)
        with self.assertRaisesRegex(ValueError, 'missing_from_HTML_census'):
            attach_pdf_coverage({'rows': [], 'summary': {}}, bundle)

    def next_day_material(self):
        for part in ('landing', 'pdf'):
            item = self.fixture.input['sources'][0][part]
            item['observed_at'] = item['observed_at'].replace('2026-09-14', '2026-09-15')
        self.fixture.input['sources'][0]['identity_check']['checked_at'] = '2026-09-15T01:01:00Z'
        self.fixture.as_of = '2026-09-15T02:00:00Z'
        declaration = self.fixture.with_reading()
        declaration['readings'][0]['read_completed_at'] = '2026-09-15T01:30:00Z'
        return self.fixture.validate(declaration)

    def test_review_clock_advances_pdf_visibility_not_corpus_date_or_original_timestamps(self):
        older = copy.deepcopy(self.material)
        newer = self.next_day_material()
        self.material = {key: older[key] + newer[key] for key in ('sources', 'readings')}
        before = copy.deepcopy(self.material)
        legacy = self.build()
        self.assertEqual(legacy['counts']['source_count'], 1)
        self.assertEqual(legacy['counts']['receipt_count'], 1)
        self.manifest.update(source_review_as_of='2026-09-15T01:30:00.123456Z', source_review_clock_digest='a' * 64)
        with patch('pdf_reading_reviews.extract_pdf', side_effect=AssertionError('No cache reads in export')):
            bundle = self.build()
        self.assertEqual(bundle['data_through'], '2026-09-14')
        self.assertEqual(bundle['source_review_as_of'], self.manifest['source_review_as_of'])
        self.assertEqual(bundle['source_review_clock_digest'], self.manifest['source_review_clock_digest'])
        self.assertEqual(bundle['counts']['source_count'], 2)
        self.assertEqual(bundle['counts']['receipt_count'], 2)
        self.assertEqual(bundle['counts']['all_work_count'], 1)
        self.assertEqual(self.material, before)
        api, downloads = self.fixture.root / 'clock-api', self.fixture.root / 'clock-downloads'
        export_pdf_coverage(bundle, api, downloads)
        with closing(sqlite3.connect(':memory:')) as db:
            pdf_coverage_sqlite(db, bundle)
            self.assertEqual(audit_pdf_coverage(bundle, self.fixture.payload, api, downloads, db)['receipt_count'], 2)

    def test_future_pdf_identity_review_and_reading_do_not_leak_before_exact_cutoff(self):
        self.material = self.next_day_material()
        for cutoff, source_count, reading_count in (
                ('2026-09-15T01:00:02.999999Z', 0, 0),
                ('2026-09-15T01:00:30Z', 0, 0),
                ('2026-09-15T01:01:00Z', 1, 0),
                ('2026-09-15T01:29:59.999999Z', 1, 0),
                ('2026-09-15T01:30:00Z', 1, 1)):
            with self.subTest(cutoff=cutoff):
                self.manifest.update(source_review_as_of=cutoff, source_review_clock_digest='a' * 64)
                bundle = self.build()
                self.assertEqual(bundle['counts']['source_count'], source_count)
                self.assertEqual(bundle['counts']['receipt_count'], reading_count)

    def test_future_malformed_pdf_history_is_rejected_before_filtering(self):
        self.material = self.next_day_material()
        self.material['sources'][0]['metadata_sha256'] = 'f' * 64
        with self.assertRaisesRegex(ValueError, 'metadata_hash_mismatch'):
            self.build()

    def test_pdf_explicit_clock_pair_required_and_html_clock_must_agree(self):
        self.manifest['source_review_as_of'] = '2026-09-15T00:00:00Z'
        with self.assertRaises(ValueError): self.build()
        self.manifest['source_review_clock_digest'] = 'a' * 64
        bundle = self.build()
        html = {'summary': {'data_through': '2026-09-14'}, 'rows': [{'work_id': 'work:test'}]}
        with self.assertRaisesRegex(ValueError, 'review_clock_mismatch'):
            attach_pdf_coverage(html, bundle)


if __name__ == '__main__':
    unittest.main()
