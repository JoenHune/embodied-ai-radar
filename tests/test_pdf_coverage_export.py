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


if __name__ == '__main__':
    unittest.main()
