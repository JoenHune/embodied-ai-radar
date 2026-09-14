import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from fulltext_reading_reviews import (ASSURANCE, NORMALIZATION, TEXT_SCOPE, article_text, import_readings,
                                       public_audit, sha256, validate_readings)


class FulltextReadingReviewsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.cache = self.root / 'cache'
        (self.cache / 'objects').mkdir(parents=True)
        self.url = 'https://arxiv.org/html/2407.02648v1'
        self.wid = 'arxiv:2407.02648'
        self.html = (b'<html><head><meta name="citation_arxiv_id" content="2407.02648v1"></head><body>'
                     b'<article id="paper"><nav id="nav">DO_NOT_READ_NAV</nav><script>SECRET_SCRIPT</script><style>SECRET_STYLE</style>'
                     b'<div class="ltx_abstract" id="abstract"><h2>Abstract</h2><p>ABSTRACT.</p></div>'
                     b'<section id="S1"><h2>1 Introduction</h2><p id="p1">Repeated.\n  whitespace. Repeated.</p>'
                     b'<math alttext="x^2"><mi>x</mi><annotation>x^2</annotation></math>'
                     b'<table id="T1"><tr><th>Method</th><th>Score</th></tr><tr><td>A</td><td>88</td></tr></table>'
                     b'<table class="ltx_eqn_table" id="EQ1"><tr><td>Equation layout</td></tr></table></section>'
                     b'<section id="S2"><h2>2 Related Work</h2><p>RELATED_WORK.</p></section>'
                     b'<section id="A1"><h2>Appendix</h2><p>APPENDIX.</p></section>'
                     b'<section id="bib"><h2>References</h2><p>REFERENCE.</p></section></article></body></html>')
        self.raw_path = self.cache / 'objects' / 'source.html'
        self.raw_path.write_bytes(self.html)
        self.blocks = [{'section_id': 'body', 'text': 'Original v2 body block'}]
        blockpath = self.cache / 'objects' / 'blocks.json'
        blockpath.write_text(json.dumps(self.blocks))
        self.obs = {'work_id': self.wid, 'source_url': self.url, 'effective_url': self.url, 'version': 'v1',
                    'raw_sha256': sha256(self.html), 'observed_at': '2026-09-14T01:00:00Z',
                    'status': 'full_text_available', 'cache_ref': str(self.raw_path), 'blocks_ref': str(blockpath),
                    'text_sha256': sha256(self.blocks[0]['text'].encode()), 'transport_verification': 'legacy_unrecorded'}
        self.observations = self.cache / 'observations.jsonl'
        self.observations.write_text(json.dumps(self.obs) + '\n')
        self.payload = {'works': [{'work_id': self.wid, 'identifiers': {'arxiv': '2407.02648'}}]}
        text = article_text(self.html)
        self.record = {'work_id': self.wid, 'source_url': self.url, 'version': 'v1', 'raw_sha256': sha256(self.html),
                       'observed_at': self.obs['observed_at'], 'read_completed_at': '2026-09-14T02:00:00Z',
                       'reading_status': 'completed', 'reader_kind': 'AI', 'text_scope': TEXT_SCOPE,
                       'article_normalization': NORMALIZATION, 'article_chars': len(text),
                       'article_text_sha256': sha256(text.encode()),
                       'read_ranges': [{'start': 0, 'end': 40}, {'start': 40, 'end': len(text)}],
                       'checked_table_ids': ['T1'], 'math_source_note_zh': '已阅读原始MathML与TeX；没有看公式截图。',
                       'images_inspected': False, 'supplementary_materials_inspected': False,
                       'findings_zh': [{'text_zh': '表中A方法得分为88。', 'source_locator': 'T1'}],
                       'limitations_zh': [{'text_zh': '附录细节不代表已完成独立复现。', 'source_locator': 'A1'}]}
        self.batch = {'schema_version': '1', 'readings': [self.record]}
        self.output = self.root / 'public' / 'fulltext-readings.jsonl'

    def tearDown(self):
        self.temp.cleanup()

    def validate(self):
        return validate_readings(self.batch, self.payload, [self.obs], self.cache)

    def test_exact_article_text_keeps_whitespace_repetition_math_context_and_appendix(self):
        text = article_text(self.html)
        self.assertIn('Repeated.\n  whitespace. Repeated.', text)
        self.assertIn('x x^2', text)
        for part in ('ABSTRACT.', 'RELATED_WORK.', 'APPENDIX.', 'REFERENCE.'):
            self.assertIn(part, text)
        for part in ('DO_NOT_READ_NAV', 'SECRET_SCRIPT', 'SECRET_STYLE'):
            self.assertNotIn(part, text)

    def test_private_validation_and_idempotent_import_never_write_source(self):
        before = {path: path.read_bytes() for path in (self.raw_path, self.observations)}
        dry = import_readings(self.batch, self.payload, self.observations, self.output)
        self.assertFalse(dry['applied'])
        self.assertFalse(self.output.exists())
        first = import_readings(self.batch, self.payload, self.observations, self.output, apply=True)
        original = self.output.read_bytes()
        second = import_readings(self.batch, self.payload, self.observations, self.output, apply=True)
        self.assertEqual(first['added'], 1)
        self.assertEqual(second['added'], 0)
        self.assertEqual(self.output.read_bytes(), original)
        self.assertEqual({path: path.read_bytes() for path in before}, before)

    def test_public_receipt_is_explicitly_self_attested_not_human_or_cognition_proof(self):
        row = self.validate()[0]
        self.assertEqual(row['assurance'], ASSURANCE)
        self.assertFalse(row['understanding_verified'])
        self.assertFalse(row['human_reviewed'])
        self.assertFalse(row['tables_exhaustive'])
        self.assertEqual(row['checked_table_count'], 1)
        self.assertIn('T1', row['findings_zh'][0]['locator_text_sha256'])
        for secret in ('cache_ref', 'blocks_ref', 'SECRET_SCRIPT', 'RELATED_WORK.', str(self.cache)):
            self.assertNotIn(secret, json.dumps(row))

    def test_prepared_abstract_human_and_uninspected_media_claims_fail(self):
        for key, value in [('reading_status', 'prepared'), ('reader_kind', 'human'),
                           ('text_scope', 'only_abstract'), ('article_normalization', 'prepared-packet-text'),
                           ('preparation_status', 'prepared_not_read'), ('images_inspected', True),
                           ('supplementary_materials_inspected', True)]:
            with self.subTest(key=key):
                old = self.record.copy()
                self.record[key] = value
                with self.assertRaises(ValueError): self.validate()
                self.record.clear(); self.record.update(old)
        packet = {'schema_version': '1', 'packets': [{'preparation_status': 'prepared_not_read'}]}
        with self.assertRaises(ValueError): validate_readings(packet, self.payload, [self.obs], self.cache)

    def test_gaps_overlaps_out_of_bounds_bytes_bool_and_missing_ranges_fail(self):
        n = self.record['article_chars']
        for ranges in ([], [{'start': 1, 'end': n}], [{'start': 0, 'end': n - 1}],
                       [{'start': 0, 'end': 50}, {'start': 49, 'end': n}],
                       [{'start': 0, 'end': 50}, {'start': 51, 'end': n}],
                       [{'start': 0, 'end': n + 1}], [{'start': False, 'end': n}],
                       [{'start': 0, 'end': n, 'unit': 'byte'}]):
            with self.subTest(ranges=ranges):
                self.record['read_ranges'] = ranges
                with self.assertRaises(ValueError): self.validate()

    def test_hash_count_identity_version_and_chronology_fail_closed(self):
        for key, value in [('raw_sha256', 'f' * 64), ('article_text_sha256', 'f' * 64),
                           ('article_chars', self.record['article_chars'] + 1), ('work_id', 'unknown'),
                           ('version', 'v2'), ('read_completed_at', '2026-09-14T00:00:00Z'),
                           ('source_url', 'https://example.com/private.html'),
                           ('source_url', self.url + '?private=1'), ('source_url', self.url + '#S1')]:
            with self.subTest(key=key, value=value):
                old = self.record.copy(); self.record[key] = value
                with self.assertRaises(ValueError): self.validate()
                self.record.clear(); self.record.update(old)

    def test_actual_raw_page_identity_not_only_observation_metadata_is_checked(self):
        raw = self.html.replace(b'content="2407.02648v1"', b'content="2407.99999v1"')
        self.raw_path.write_bytes(raw)
        self.obs['raw_sha256'] = self.record['raw_sha256'] = sha256(raw)
        with self.assertRaisesRegex(ValueError, 'raw_page_identity'):
            self.validate()

    def test_numbered_abstract_only_html_is_rejected_even_with_complete_offsets(self):
        raw = b'<meta name="citation_arxiv_id" content="2407.02648v1"><article><section id="A"><h2>1 Abstract</h2><p>Only abstract.</p></section></article>'
        self.raw_path.write_bytes(raw)
        self.obs['raw_sha256'] = self.record['raw_sha256'] = sha256(raw)
        with self.assertRaisesRegex(ValueError, 'only_abstract'):
            self.validate()

    def test_unsafe_cache_paths_and_symlinks_inside_or_outside_objects_fail(self):
        for target in ('outside', 'inside_link', 'directory_link'):
            with self.subTest(target=target):
                old = self.obs['cache_ref']
                if target == 'outside':
                    path = self.root / 'outside.html'; path.write_bytes(self.html)
                elif target == 'inside_link':
                    path = self.cache / 'objects' / 'link.html'; path.symlink_to(self.raw_path)
                else:
                    link = self.cache / 'objects' / 'linked'; link.symlink_to(self.cache / 'objects', target_is_directory=True)
                    path = link / 'source.html'
                self.obs['cache_ref'] = str(path)
                with self.assertRaises(ValueError): self.validate()
                self.obs['cache_ref'] = old

    def test_unknown_table_formula_layout_and_unknown_locator_are_rejected(self):
        for ids in (['unknown'], ['EQ1'], ['T1', 'T1']):
            self.record['checked_table_ids'] = ids
            with self.assertRaises(ValueError): self.validate()
        self.record['checked_table_ids'] = []
        self.assertEqual(self.validate()[0]['checked_table_count'], 0)
        self.record['findings_zh'][0]['source_locator'] = 'unknown'
        with self.assertRaises(ValueError): self.validate()

    def test_verified_v2_body_locator_is_allowed_without_dom_id(self):
        self.record['limitations_zh'][0]['source_locator'] = 'body'
        self.assertIn('body', self.validate()[0]['limitations_zh'][0]['locator_text_sha256'])
        self.obs['text_sha256'] = 'f' * 64
        with self.assertRaisesRegex(ValueError, 'original_body_blocks_hash'):
            self.validate()

    def test_private_strings_and_non_chinese_or_unbound_judgments_fail(self):
        for text in ('English-only finding', '判断来源 /Users/private/source.html'):
            self.record['findings_zh'][0]['text_zh'] = text
            with self.assertRaises(ValueError): self.validate()

    def test_known_incomplete_transport_cannot_claim_complete_article_reading(self):
        self.obs['transport_returncode'] = 18
        with self.assertRaisesRegex(ValueError, 'incomplete_source_transport'):
            self.validate()

    def test_conflicting_existing_receipt_fails_without_overwrite(self):
        import_readings(self.batch, self.payload, self.observations, self.output, apply=True)
        before = self.output.read_bytes()
        self.record['findings_zh'][0]['text_zh'] = '修改过的独立判断。'
        with self.assertRaisesRegex(ValueError, 'receipt_conflict'):
            import_readings(self.batch, self.payload, self.observations, self.output, apply=True)
        self.assertEqual(before, self.output.read_bytes())

    def test_public_audit_runs_without_cache_and_is_not_a_private_source_recheck(self):
        receipts = self.validate()
        self.raw_path.unlink()
        result = public_audit(receipts, self.payload, [self.obs], '2026-09-14')
        self.assertEqual(result['counts']['AI_read_work_count'], 1)
        self.assertFalse(result['private_source_reverified'])
        self.assertFalse(result['understanding_verified'])
        self.assertEqual(public_audit(receipts, self.payload, [self.obs], '2026-09-13')['counts']['AI_read_work_count'], 0)
        self.assertEqual(public_audit([], self.payload, [], '2026-09-14')['counts']['AI_read_work_count'], 0)

    def test_public_audit_rejects_private_fields_human_forged_ranges_and_missing_lineage(self):
        row = self.validate()[0]
        cases = [{'excerpt': 'raw source'}, {'cache_ref': str(self.cache)}, {'human_reviewed': True},
                 {'reader_kind': 'human'}, {'raw_sha256': 'f' * 64},
                 {'read_ranges': [{'start': 1, 'end': row['article_chars']}]},
                 {'read_completed_at': '2026-09-13T00:00:00Z'}, {'checked_table_count': 99}]
        cases.append({'transport_verification': 'complete'})
        for changes in cases:
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    public_audit([{**row, **changes}], self.payload, [self.obs], '2026-09-14')
        with self.assertRaisesRegex(ValueError, 'source_observation_mismatch'):
            public_audit([row], self.payload, [], '2026-09-14')
        with self.assertRaises(ValueError):
            public_audit([row, row], self.payload, [self.obs], '2026-09-14')


if __name__ == '__main__':
    unittest.main()
