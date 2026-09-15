import copy
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pdf_reading_reviews as pdf
from catalog_store import encode, fingerprint


def pdf_fixture(pages=2):
    from pypdf import PdfWriter
    from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
    writer = PdfWriter()
    for number in range(pages):
        page = writer.add_blank_page(width=300, height=300)
        font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'),
                                 NameObject('/BaseFont'): NameObject('/Helvetica')})
        page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): font})})
        stream = DecodedStreamObject()
        stream.set_data(f'BT /F1 12 Tf 20 260 Td (Test Robotics Paper page {number + 1}) Tj ET'.encode())
        page[NameObject('/Contents')] = writer._add_object(stream)
    # Deliberately misleading PDF Info must never decide identity.
    writer.add_metadata({'/Author': 'Anonymous Submission', '/CreationDate': 'D:20101201120000'})
    stream = io.BytesIO()
    writer.write(stream)
    return stream.getvalue()


class PdfReadingReviewsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.cache = self.root / 'cache'
        self.cache.mkdir()
        self.html = b'<html><head><meta name="citation_title" content="Test Robotics Paper"><meta name="citation_author" content="A Reader"><meta name="citation_doi" content="10.1234/test"><meta name="citation_conference_title" content="Robotics: Science and Systems"><meta name="citation_publication_date" content="2024/07/15"><meta name="citation_pdf_url" content="https://files.example.org/paper.pdf"></head><body><a href="https://files.example.org/paper.pdf">Download PDF</a></body></html>'
        self.raw = pdf_fixture()
        (self.cache / 'paper.html').write_bytes(self.html)
        (self.cache / 'paper.pdf').write_bytes(self.raw)
        self.payload = {'works': [{'work_id': 'work:test', 'title': 'Test Robotics Paper', 'authors': ['A Reader'],
                                   'identifiers': {'doi': '10.1234/test'}, 'relevance': {'status': 'included'}}],
                        'manifestations': [{'manifestation_id': 'manifest:test', 'work_id': 'work:test',
                                            'url': 'https://proceedings.example.org/paper.html', 'source_record_id': 'source:test',
                                            'kind': 'conference', 'venue': 'RSS', 'year': 2024}],
                        'source-records': [{'source_record_id': 'source:test', 'url': 'https://proceedings.example.org/paper.html'}]}
        def item(kind, address, raw, time):
            return {'url': address, 'sha256': pdf.sha256(raw), 'cache_ref': str(self.cache / ('paper.' + kind)),
                    'observed_at': time, 'transport': {'http_status': 200, 'returncode': 0, 'complete': True,
                        'truncated': False, 'response_bytes': len(raw), 'content_length': len(raw),
                        'content_type': 'application/octet-stream' if kind == 'pdf' else 'text/html'}}
        self.input = {'schema_version': '1', 'sources': [{'work_id': 'work:test', 'manifestation_id': 'manifest:test',
            'landing': item('html', 'https://proceedings.example.org/paper.html', self.html, '2026-09-14T01:00:00Z'),
            'pdf': item('pdf', 'https://files.example.org/paper.pdf', self.raw, '2026-09-14T01:00:03Z'),
            'identity_check': {'status': 'same_work_confirmed', 'reader_kind': 'AI', 'checked_at': '2026-09-14T01:01:00Z',
                'source_pages': [1], 'title_checked': True, 'authors_checked': True, 'identifier_or_venue_checked': True,
                'differences_zh': '作者显示无差异。', 'reason_zh': '明确核对官方页、首页题名、作者及会议身份。'}}], 'readings': []}
        self.as_of = '2026-09-14T02:00:00Z'

    def validate(self, value=None):
        return pdf.validate_declarations(value or self.input, self.payload, self.cache, as_of=self.as_of)

    def with_reading(self):
        source = self.validate()['sources'][0]
        reading = {key: source[key] for key in pdf.READING_DECLARATION_KEYS if key in source}
        reading.update(read_pages=[1, 2], read_completed_at='2026-09-14T01:30:00Z', reader_kind='AI',
                       reading_status='completed', checked_table_count=0, visual_pages_checked=[1],
                       supplementary_materials_inspected=False, human_reviewed=False,
                       findings_zh=[{'text_zh': '本示例用于来源验证，不产生设备事实。', 'source_pages': [1, 2]}],
                       limitations_zh=[{'text_zh': '未检查外部补充材料。', 'source_pages': [2]}])
        value = copy.deepcopy(self.input)
        value['readings'] = [reading]
        return value

    def test_valid_octet_stream_pdf_source_not_read(self):
        result = self.validate()
        self.assertEqual(result['readings'], [])
        source = result['sources'][0]
        self.assertEqual(source['page_count'], 2)
        self.assertEqual(source['version'], None)
        self.assertEqual(source['edition_label'], 'RSS 2024')
        self.assertEqual(source['identity_status'], 'same_work_confirmed')
        self.assertNotIn('Anonymous', encode(source))
        audit = pdf.public_audit([], self.payload, result['sources'], self.as_of)
        self.assertEqual(audit['counts'], {'all_work_count': 0, 'included_work_count': 0, 'receipt_count': 0,
                                          'source_count': 1, 'source_work_count': 1, 'included_source_work_count': 1})

    def test_complete_reading_bound_to_pages_and_no_private_paths(self):
        result = self.validate(self.with_reading())
        audit = pdf.public_audit(result['readings'], self.payload, result['sources'], self.as_of)
        self.assertEqual(audit['counts']['all_work_count'], 1)
        self.assertEqual(result['readings'][0]['text_scope'], 'complete_available_pdf_text')
        self.assertNotIn(str(self.cache), encode(result))
        self.assertFalse(audit['private_source_reverified'])

    def test_unknown_identity_allows_source_but_rejects_reading(self):
        value = self.with_reading()
        value['sources'][0]['identity_check'] = {'status': 'not_checked'}
        with self.assertRaisesRegex(ValueError, 'identity_checked_source'):
            self.validate(value)
        value['readings'] = []
        self.assertEqual(self.validate(value)['sources'][0]['identity_status'], 'not_checked')

    def test_prepared_is_never_read(self):
        for mutate in [lambda row: row.update(reading_status='prepared'), lambda row: row.update(preparation_status='completed')]:
            value = self.with_reading()
            mutate(value['readings'][0])
            with self.assertRaises(ValueError):
                self.validate(value)

    def test_bad_magic_truncation_and_unparseable_pdf(self):
        for raw in (b'<html>Not a PDF</html>', self.raw[:-10], b'%PDF-1.7\ninvalid\n%%EOF'):
            with self.assertRaises(ValueError):
                pdf.extract_pdf(raw)

    def test_cache_hash_mismatch(self):
        (self.cache / 'paper.pdf').write_bytes(self.raw + b' ')
        with self.assertRaisesRegex(ValueError, 'cache_hash_mismatch'):
            self.validate()

    def test_actual_link_required_even_matching_filename(self):
        value = copy.deepcopy(self.input)
        value['sources'][0]['pdf']['url'] = 'https://files.example.org/guessed.pdf'
        with self.assertRaisesRegex(ValueError, 'not_actually_linked'):
            self.validate(value)

    def replace_html(self, value, raw):
        (self.cache / 'paper.html').write_bytes(raw)
        landing = value['sources'][0]['landing']
        landing['sha256'] = pdf.sha256(raw)
        landing['transport'].update(response_bytes=len(raw), content_length=len(raw))

    def test_related_work_pdf_anchor_is_not_primary_citation(self):
        value = copy.deepcopy(self.input)
        target = 'https://files.example.org/related.pdf'
        value['sources'][0]['pdf']['url'] = target
        self.replace_html(value, self.html.replace(b'</body>', b'<aside><a href="https://files.example.org/related.pdf">Download PDF</a></aside></body>'))
        with self.assertRaisesRegex(ValueError, 'not_actually_linked_from_landing_citation'):
            self.validate(value)

    def test_landing_title_DOI_year_and_venue_bound_to_catalog(self):
        for before, after, reason in [(b'Test Robotics Paper', b'Different Related Paper', 'title_mismatch'),
                                     (b'10.1234/test', b'10.1234/wrong', 'DOI_mismatch'),
                                     (b'2024/07/15', b'2025/07/15', 'year_mismatch'),
                                     (b'Robotics: Science and Systems', b'Some Different Conference', 'venue_mismatch')]:
            value = copy.deepcopy(self.input)
            self.replace_html(value, self.html.replace(before, after))
            with self.assertRaisesRegex(ValueError, reason):
                self.validate(value)

    def test_HTTP_citation_and_actual_HTTPS_anchor_resolve_same_resource(self):
        value = copy.deepcopy(self.input)
        self.replace_html(value, self.html.replace(b'content="https://files.example.org/paper.pdf"',
                                                   b'content="http://files.example.org/paper.pdf"'))
        source = self.validate(value)['sources'][0]
        self.assertEqual(source['pdf_link_evidence']['citation_pdf_url'], 'http://files.example.org/paper.pdf')
        self.assertEqual(source['source_url'], 'https://files.example.org/paper.pdf')

    def test_manifestation_work_and_unrelated_landing_rejected(self):
        for mutate in [lambda row: row.update(manifestation_id='unknown'),
                       lambda row: row.update(work_id='work:other'),
                       lambda row: row['landing'].update(url='https://unrelated.example.org/paper.html')]:
            value = copy.deepcopy(self.input)
            mutate(value['sources'][0])
            with self.assertRaises(ValueError):
                self.validate(value)

    def test_full_reading_requires_every_page_and_page_bound_judgments(self):
        for pages in ([1], [1, 1, 2], [1, 2, 3], [True, 2], [2, 1]):
            value = self.with_reading()
            value['readings'][0]['read_pages'] = pages
            with self.assertRaises(ValueError):
                self.validate(value)
        value = self.with_reading()
        value['readings'][0]['findings_zh'][0]['source_pages'] = [3]
        with self.assertRaises(ValueError):
            self.validate(value)

    def test_explicit_reading_and_source_hash_tampering(self):
        value = self.with_reading()
        value['readings'][0]['page_text_sha256']['2'] = 'f' * 64
        with self.assertRaisesRegex(ValueError, 'binding_mismatch'):
            self.validate(value)
        result = self.validate()
        result['sources'][0]['page_text_sha256']['1'] = 'f' * 64
        with self.assertRaisesRegex(ValueError, 'metadata_hash_mismatch'):
            pdf.public_audit([], self.payload, result['sources'], self.as_of)
        result = self.validate(self.with_reading())
        result['readings'][0]['findings_zh'][0]['text_zh'] = '篡改阅读判断。'
        with self.assertRaisesRegex(ValueError, 'declaration_hash_mismatch'):
            pdf.public_audit(result['readings'], self.payload, result['sources'], self.as_of)

    def test_declared_extractor_or_hash_must_match_reextraction(self):
        for key, value in [('extractor_version', 'made-up'), ('document_text_sha256', 'a' * 64), ('page_count', 99)]:
            declaration = copy.deepcopy(self.input)
            declaration['sources'][0][key] = value
            with self.assertRaisesRegex(ValueError, 'extraction_hash_mismatch'):
                self.validate(declaration)

    def test_transport_complete_and_typed_booleans(self):
        for key, value in [('complete', 1), ('truncated', 0), ('returncode', False), ('returncode', 18),
                           ('content_length', len(self.raw) - 1), ('response_bytes', True), ('http_status', 403)]:
            declaration = copy.deepcopy(self.input)
            declaration['sources'][0]['pdf']['transport'][key] = value
            with self.assertRaises(ValueError):
                self.validate(declaration)
        for key in ('human_reviewed', 'supplementary_materials_inspected'):
            declaration = self.with_reading()
            declaration['readings'][0][key] = 0
            with self.assertRaises(ValueError):
                self.validate(declaration)

    def test_future_read_source_identity_and_reversed_time_rejected(self):
        for kind in ('read', 'source', 'identity'):
            value = self.with_reading()
            if kind == 'read':
                value['readings'][0]['read_completed_at'] = '2026-09-15T01:30:00Z'
            elif kind == 'source':
                value['sources'][0]['pdf']['observed_at'] = '2026-09-15T01:30:00Z'
            else:
                value['sources'][0]['identity_check']['checked_at'] = '2026-09-15T01:30:00Z'
            with self.assertRaises(ValueError):
                self.validate(value)
        value = self.with_reading()
        value['readings'][0]['read_completed_at'] = '2026-09-14T00:59:59Z'
        with self.assertRaises(ValueError):
            self.validate(value)

    def test_public_future_timestamps_and_changed_judgment_pages_rejected(self):
        result = self.validate(self.with_reading())
        result['readings'][0]['read_completed_at'] = '2026-09-15T01:30:00Z'
        with self.assertRaisesRegex(ValueError, 'time_invalid_or_future'):
            pdf.public_audit(result['readings'], self.payload, result['sources'], self.as_of)
        result = self.validate()
        result['sources'][0]['observed_at'] = '2026-09-15T01:30:00Z'
        with self.assertRaisesRegex(ValueError, 'time_invalid_or_future'):
            pdf.public_audit([], self.payload, result['sources'], self.as_of)
        result = self.validate(self.with_reading())
        result['readings'][0]['findings_zh'][0]['source_pages'] = [1]
        with self.assertRaisesRegex(ValueError, 'declaration_hash_mismatch'):
            pdf.public_audit(result['readings'], self.payload, result['sources'], self.as_of)

    def test_source_identity_is_not_just_title_boolean(self):
        for key in ('authors_checked', 'identifier_or_venue_checked', 'title_checked'):
            value = copy.deepcopy(self.input)
            value['sources'][0]['identity_check'][key] = False
            with self.assertRaises(ValueError):
                self.validate(value)

    def test_private_cache_symlink_and_traversal(self):
        link = self.cache / 'link.pdf'
        link.symlink_to(self.cache / 'paper.pdf')
        for path in (str(link), str(self.cache / '..' / 'cache' / 'paper.pdf'), '/etc/hosts'):
            with self.assertRaises((ValueError, OSError)):
                pdf.private_bytes(path, self.cache)
        nested = self.cache / 'alias'
        nested.symlink_to(self.cache, target_is_directory=True)
        with self.assertRaises((ValueError, OSError)):
            pdf.private_bytes(str(nested / 'paper.pdf'), self.cache)

    def test_private_auth_and_unknown_fields_rejected_publicly(self):
        for extra in ({'cache_ref': '/Users/private.pdf'}, {'authorization': 'secret'}, {'unknown': True}):
            result = self.validate()
            result['sources'][0].update(extra)
            with self.assertRaises(ValueError):
                pdf.public_audit([], self.payload, result['sources'], self.as_of)
        value = copy.deepcopy(self.input)
        value['sources'][0]['pdf']['url'] = 'https://user:password@files.example.org/paper.pdf'
        with self.assertRaises(ValueError):
            self.validate(value)
        value['sources'][0]['pdf']['url'] = 'https://files.example.org/paper.pdf?token=secret'
        with self.assertRaises(ValueError):
            self.validate(value)

    def test_duplicate_source_and_reading_rejected(self):
        result = self.validate(self.with_reading())
        with self.assertRaisesRegex(ValueError, 'duplicate_public_source'):
            pdf.public_audit([], self.payload, result['sources'] * 2, self.as_of)
        with self.assertRaisesRegex(ValueError, 'duplicate_public_reading'):
            pdf.public_audit(result['readings'] * 2, self.payload, result['sources'], self.as_of)
        value = copy.deepcopy(self.input)
        value['sources'] *= 2
        with self.assertRaisesRegex(ValueError, 'duplicate_source'):
            self.validate(value)

    def test_apply_idempotence_dry_run_and_validate_all_before_write(self):
        source_out, reading_out = self.root / 'sources.jsonl', self.root / 'readings.jsonl'
        def run(value, apply=False):
            return pdf.import_reviews(value, self.payload, source_out, reading_out, cache_root=self.cache,
                                      apply=apply, as_of=self.as_of)
        value = self.with_reading()
        self.assertFalse(run(value)['applied'])
        self.assertFalse(source_out.exists())
        self.assertEqual(run(value, True)['added'], {'sources': 1, 'readings': 1})
        before = [path.read_bytes() for path in (source_out, reading_out)]
        self.assertEqual(run(value, True)['added'], {'sources': 0, 'readings': 0})
        value['readings'][0]['read_pages'] = [1]
        with self.assertRaises(ValueError):
            run(value, True)
        self.assertEqual(before, [path.read_bytes() for path in (source_out, reading_out)])

    def test_existing_conflict_and_unsafe_output(self):
        source_out, reading_out = self.root / 'sources.jsonl', self.root / 'readings.jsonl'
        value = self.with_reading()
        pdf.import_reviews(value, self.payload, source_out, reading_out, cache_root=self.cache, apply=True, as_of=self.as_of)
        value['readings'][0]['findings_zh'][0]['text_zh'] = '另一条不同判断。'
        with self.assertRaisesRegex(ValueError, 'existing_ledger_conflict'):
            pdf.import_reviews(value, self.payload, source_out, reading_out, cache_root=self.cache, apply=True, as_of=self.as_of)
        linked = self.root / 'linked.jsonl'
        linked.symlink_to(source_out)
        with self.assertRaises(ValueError):
            pdf.import_reviews(self.input, self.payload, linked, reading_out, cache_root=self.cache, apply=True, as_of=self.as_of)

    def test_arxiv_abs_pdf_version_preserved_not_invented(self):
        self.payload['works'][0]['identifiers']['arxiv'] = '2409.11952'
        self.payload['works'][0]['identifiers']['doi'] = None
        address = 'https://arxiv.org/abs/2409.11952'
        self.payload['manifestations'][0].update(url=address, venue='arXiv', kind='preprint')
        self.payload['source-records'][0]['url'] = address
        self.payload['text-snapshots'] = [{'work_id': 'work:test', 'source_url': address + 'v1', 'version': 'v1'}]
        value = copy.deepcopy(self.input)
        value['sources'][0]['landing']['url'] = address + 'v1'
        value['sources'][0]['pdf']['url'] = 'https://arxiv.org/pdf/2409.11952v1'
        raw = self.html.replace(b'https://files.example.org/paper.pdf', b'https://arxiv.org/pdf/2409.11952v1')
        (self.cache / 'paper.html').write_bytes(raw)
        landing = value['sources'][0]['landing']
        landing['sha256'] = pdf.sha256(raw)
        landing['transport'].update(response_bytes=len(raw), content_length=len(raw))
        self.assertEqual(self.validate(value)['sources'][0]['version'], 'v1')
        value['sources'][0]['landing']['url'] = address + 'v2'
        with self.assertRaises(ValueError):
            self.validate(value)
        value['sources'][0]['landing']['url'] = address + 'v999'
        value['sources'][0]['pdf']['url'] = 'https://arxiv.org/pdf/2409.11952v999'
        self.replace_html(value, raw.replace(b'11952v1', b'11952v999'))
        with self.assertRaisesRegex(ValueError, 'version_not_in_catalog_history'):
            self.validate(value)

    def arxiv_v2_dated_fixture(self):
        from versioned_text import snapshot_from_payload
        work = self.payload['works'][0]
        work['identifiers'].update(arxiv='2409.11952', doi=None)
        work['source_record_ids'] = ['source:test', 'source:version-v2']
        address = 'https://arxiv.org/abs/2409.11952'
        self.payload['manifestations'][0].update(url=address, venue=None, kind='preprint', year=None)
        self.payload['source-records'][0]['url'] = address
        source = {'source_record_id': 'source:version-v2', 'url': address + 'v2', 'version': 'v2',
                  'source_type': 'official_arxiv_version_metadata', 'published_at': '2026-09-04', 'date_precision': 'day'}
        snapshot = snapshot_from_payload(work, source, {'arxiv_id': '2409.11952', 'version': 'v2',
            'title': work['title'], 'abstract': 'Synthetic version-specific abstract.', 'authors': work['authors'],
            'submitted_at': '2024-09-14', 'updated_at': '2026-09-04'})
        source['payload_hash'] = fingerprint(snapshot)
        source['text_content_digest'] = fingerprint({key: snapshot[key] for key in ('title', 'abstract')})
        self.payload['source-records'].append(source)
        self.payload['text-snapshots'] = [snapshot]
        self.input['sources'][0]['landing']['url'] = address + 'v2'
        self.input['sources'][0]['pdf']['url'] = 'https://arxiv.org/pdf/2409.11952v2'
        self.html = self.html.replace(b'https://files.example.org/paper.pdf', b'https://arxiv.org/pdf/2409.11952v2').replace(b'2024/07/15', b'2026/09/04')
        self.replace_html(self.input, self.html)
        return snapshot

    def test_arxiv_null_series_year_uses_bound_v2_date_without_mutating_manifestation(self):
        snapshot = self.arxiv_v2_dated_fixture()
        before = copy.deepcopy(self.payload)
        source = self.validate()['sources'][0]
        self.assertIsNone(source['edition']['year'])
        self.assertIsNone(self.payload['manifestations'][0]['year'])
        self.assertEqual(source['version'], 'v2')
        self.assertEqual(source['edition_label'], 'arXiv v2')
        proof = source['edition']['arxiv_version_date_provenance']
        self.assertEqual(proof['year'], 2026)
        self.assertEqual(proof['text_snapshot_sources'][0]['snapshot_id'], snapshot['snapshot_id'])
        self.assertEqual(proof['text_snapshot_sources'][0]['available_at'], '2026-09-04')
        self.assertEqual(source['source_record_id'], 'source:test')
        result = self.validate(self.with_reading())
        self.assertEqual(pdf.public_audit(result['readings'], self.payload, result['sources'], self.as_of)['counts']['receipt_count'], 1)
        self.assertEqual(self.payload, before)

    def test_arxiv_dated_version_rejects_wrong_landing_year_and_unknown_version(self):
        self.arxiv_v2_dated_fixture()
        self.replace_html(self.input, self.html.replace(b'2026/09/04', b'2025/09/04'))
        with self.assertRaisesRegex(ValueError, 'publication_year_mismatch'):
            self.validate()
        self.replace_html(self.input, self.html.replace(b'11952v2', b'11952v3'))
        self.input['sources'][0]['landing']['url'] = 'https://arxiv.org/abs/2409.11952v3'
        self.input['sources'][0]['pdf']['url'] = 'https://arxiv.org/pdf/2409.11952v3'
        with self.assertRaisesRegex(ValueError, 'version_not_in_catalog_history'):
            self.validate()

    def test_arxiv_year_fallback_requires_real_source_bound_publication_date(self):
        self.arxiv_v2_dated_fixture()
        original = copy.deepcopy(self.payload)
        for change in ('undated', 'retrieval_only', 'wrong_work', 'wrong_version', 'bad_source_hash', 'unowned_source', 'date_tampered'):
            with self.subTest(change=change):
                self.payload = copy.deepcopy(original)
                snapshot = self.payload['text-snapshots'][0]
                if change == 'undated': snapshot.update(available_at=None, date_precision='unknown')
                elif change == 'retrieval_only': snapshot['basis'] = 'source_bound_metadata:archived_observation_only'
                elif change == 'wrong_work': snapshot['work_id'] = 'work:other'
                elif change == 'wrong_version': snapshot['version'] = 'v1'
                elif change == 'bad_source_hash': self.payload['source-records'][-1]['payload_hash'] = 'f' * 64
                elif change == 'unowned_source': self.payload['works'][0]['source_record_ids'] = ['source:test']
                else: snapshot['available_at'] = '2026-09-05'
                with self.assertRaises(ValueError): self.validate()

    def test_arxiv_version_date_does_not_relax_title_DOI_or_URL_checks(self):
        self.arxiv_v2_dated_fixture()
        self.payload['works'][0]['identifiers']['doi'] = '10.1234/test'
        for before, after, reason in ((b'Test Robotics Paper', b'Other Paper', 'title_mismatch'),
                                      (b'10.1234/test', b'10.1234/wrong', 'DOI_mismatch')):
            self.replace_html(self.input, self.html.replace(before, after))
            with self.assertRaisesRegex(ValueError, reason): self.validate()
        self.replace_html(self.input, self.html)
        self.input['sources'][0]['pdf']['url'] = 'https://arxiv.org/pdf/2409.99999v2'
        with self.assertRaises(ValueError): self.validate()

    def test_non_arxiv_conference_and_journal_years_remain_required(self):
        for kind in ('conference', 'journal'):
            with self.subTest(kind=kind):
                self.payload['manifestations'][0].update(kind=kind, year=None)
                with self.assertRaisesRegex(ValueError, 'publication_year_mismatch_or_missing'):
                    self.validate()
        self.arxiv_v2_dated_fixture()
        self.payload['manifestations'][0]['kind'] = 'conference'
        with self.assertRaisesRegex(ValueError, 'publication_year_mismatch_or_missing'):
            self.validate()

    def test_textless_pages_need_explicit_visual_check(self):
        from pypdf import PdfWriter
        writer, stream = PdfWriter(), io.BytesIO()
        writer.add_blank_page(width=100, height=100)
        writer.write(stream)
        raw = stream.getvalue()
        (self.cache / 'paper.pdf').write_bytes(raw)
        item = self.input['sources'][0]['pdf']
        item['sha256'] = pdf.sha256(raw)
        item['transport'].update(response_bytes=len(raw), content_length=len(raw))
        value = self.with_reading()
        row = value['readings'][0]
        row.update(read_pages=[1], visual_pages_checked=[])
        row['findings_zh'][0]['source_pages'] = [1]
        row['limitations_zh'][0]['source_pages'] = [1]
        with self.assertRaisesRegex(ValueError, 'textless_page_requires_visual_check'):
            self.validate(value)
        row['visual_pages_checked'] = [1]
        self.assertEqual(len(self.validate(value)['readings']), 1)

    def test_public_audit_runs_with_pdf_import_forbidden(self):
        result = self.validate(self.with_reading())
        fixture = self.root / 'public.json'
        fixture.write_text(encode({'payload': self.payload, **result}))
        program = '''
import builtins,json,sys
real_import=builtins.__import__
def guarded(name,*args,**kwargs):
    if name.split('.')[0] in ('pypdf','bs4'):
        raise AssertionError('public audit attempted private parser import')
    return real_import(name,*args,**kwargs)
builtins.__import__=guarded
import pdf_reading_reviews as p
v=json.load(open(sys.argv[1]))
assert p.public_audit(v['readings'],v['payload'],v['sources'],'2026-09-14')['counts']['receipt_count']==1
'''
        process = subprocess.run([sys.executable, '-c', "import sys;sys.path.insert(0," + repr(str(Path(pdf.__file__).parent)) + ");" + program, str(fixture)], capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr)


if __name__ == '__main__':
    unittest.main()
