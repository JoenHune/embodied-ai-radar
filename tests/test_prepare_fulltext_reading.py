import copy
import contextlib
import io
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from prepare_fulltext_reading import (build_reading_packet, encode, load_packet, main, packet_filename,
                                     prepare_packets, reading_record_template, render_range, sha256,
                                     trusted_file, write_packet)

AID = '2407.02648'
WID = 'arxiv:' + AID
URL = 'https://arxiv.org/html/' + AID + 'v1'


def html(extra=''):
    return (f'<html><head><meta name="citation_arxiv_id" content="{AID}v1"></head><body>'
            '<nav>OUTSIDE_NAV</nav><article class="ltx_document" id="paper">'
            '<header><h1 id="title">Complete reading fixture</h1><p id="author">Author name</p></header>'
            '<nav>INSIDE_NAV</nav><script>FORBIDDEN_SCRIPT()</script><style>FORBIDDEN_STYLE</style>'
            '<div class="ltx_abstract" id="abstract"><h6>Abstract</h6><p id="abs-p">ABSTRACT_RETAINED.</p></div>'
            '<section id="S1"><h2>1 Introduction</h2><p id="intro">INTRO_RETAINED.</p>'
            '<div class="ltx_para" id="wrap"><p id="repeat-a">Repeated sentence.</p><p id="repeat-b">Repeated sentence.</p></div>'
            '<p id="equation">Formula <math id="m1" alttext="x^2"><semantics><mi>x</mi><annotation encoding="application/x-tex">x^2</annotation></semantics></math> ends.</p>'
            '<table id="T1"><caption>Table 1. Native values.</caption><thead><tr id="th1"><th rowspan="2">Model</th><th colspan="2">Results</th></tr></thead>'
            '<tbody><tr id="tr1"><th scope="row">Robot-A</th><td id="cell-a">33.3</td><td>44.4</td></tr></tbody></table>'
            '<figure id="T2" class="ltx_table"><figcaption>Table 2. Span values.</figcaption><p><span><span class="ltx_tabular" id="span-table">'
            '<span class="ltx_tr" id="span-head"><span class="ltx_td ltx_th ltx_th_column">Method</span><span class="ltx_td ltx_th ltx_th_column ltx_colspan_2">Scores</span></span>'
            '<span class="ltx_tr" id="span-row"><span class="ltx_td ltx_th_row">Beta</span><span class="ltx_td">55.5</span><span class="ltx_td">66.6</span></span>'
            '</span></span></p></figure>'
            '<figure id="F1"><a href="full.png"><img id="image-1" src="thumb.png" alt="Robot and object"></a><figcaption id="cap-1">FIGURE_CAPTION_RETAINED.</figcaption></figure>'
            '<dl id="definitions"><dt>Definition term</dt><dd>Definition content.</dd></dl></section>'
            '<section id="S2"><h2>2 Related Work</h2><p id="related">RELATED_RETAINED cites other devices.</p><section id="S2.1"><h3>Earlier work</h3><p>NESTED_CONTEXT.</p></section></section>'
            '<section id="S3"><h2>3 Conclusion</h2><p>CONCLUSION_RETAINED.</p></section>'
            '<section class="ltx_appendix" id="A1"><h2>Appendix A</h2><p>APPENDIX_RETAINED.</p></section>'
            '<section class="ltx_bibliography" id="references"><h2>References</h2><ol><li id="bib1">REFERENCE_RETAINED <a href="https://doi.org/10.1/example">paper</a>.</li></ol></section>'
            + extra + '</article><footer>OUTSIDE_FOOTER</footer></body></html>').encode()


def inputs(raw=None):
    raw = raw or html()
    observation = {'work_id': WID, 'arxiv_id': AID, 'version': 'v1', 'source_url': URL,
                   'effective_url': URL, 'observed_at': '2026-09-14T01:00:00Z', 'raw_sha256': sha256(raw),
                   'status': 'full_text_available', 'transport_verification': 'legacy_unrecorded'}
    work = {'work_id': WID, 'identifiers': {'arxiv': AID}, 'aliases': [WID]}
    return raw, observation, work


def disk_fixture(root):
    raw, observation, work = inputs()
    cache = root / '.research/source-cache'
    (cache / 'objects').mkdir(parents=True)
    raw_path = cache / 'objects' / (sha256(raw) + '.html')
    raw_path.write_bytes(raw)
    observation['cache_ref'] = str(raw_path)
    observation_path = cache / 'observations.jsonl'
    observation_path.write_text(encode(observation) + '\n')
    catalog = root / 'catalog'
    catalog.mkdir()
    (catalog / 'works.jsonl').write_text(encode(work) + '\n')
    output = root / '.research/fulltext-reading'
    return cache, observation_path, catalog, output, raw_path


class FulltextReadingPacketTests(unittest.TestCase):
    def packet(self, raw=None, **kwargs):
        return build_reading_packet(*inputs(raw), **kwargs)

    def test_complete_article_scope_retains_context_conclusion_appendix_and_excludes_ui(self):
        packet = self.packet()
        text = '\n'.join(block['text'] for block in packet['blocks'])
        for value in ('ABSTRACT_RETAINED', 'INTRO_RETAINED', 'RELATED_RETAINED', 'NESTED_CONTEXT',
                      'CONCLUSION_RETAINED', 'APPENDIX_RETAINED', 'REFERENCE_RETAINED', 'Author name'):
            self.assertIn(value, text)
        for value in ('OUTSIDE_NAV', 'INSIDE_NAV', 'FORBIDDEN_SCRIPT', 'FORBIDDEN_STYLE', 'OUTSIDE_FOOTER'):
            self.assertNotIn(value, text)
        for block in packet['blocks']:
            if 'RELATED_RETAINED' in block['text'] or 'NESTED_CONTEXT' in block['text'] or 'REFERENCE_RETAINED' in block['text']:
                self.assertEqual(block['evidence_role'], 'context_not_usage')
        self.assertEqual(packet['preparation_status'], 'prepared_not_read')
        self.assertFalse(packet['reading_coverage']['article_read_complete'])

    def test_dom_accounting_preserves_repeated_paragraphs_without_parent_duplication(self):
        packet = self.packet()
        blocks = [block for block in packet['blocks'] if block['text'] == 'Repeated sentence.']
        self.assertEqual([block['dom_id'] for block in blocks], ['repeat-a', 'repeat-b'])
        coverage = packet['extraction_coverage']
        self.assertEqual(coverage['eligible_dom_text_nodes'], coverage['accounted_for_dom_text_nodes'])
        self.assertEqual(coverage['unaccounted_dom_text_nodes'], 0)
        self.assertEqual(coverage['duplicate_text_groups_preserved'], 1)

    def test_native_and_span_tables_preserve_cells_spans_and_do_not_flatten_twice(self):
        packet = self.packet()
        tables = [block for block in packet['blocks'] if block['kind'] == 'table']
        self.assertEqual(len(tables), 2)
        native, span = tables
        self.assertEqual(native['table']['headers'][0]['cells'][0]['rowspan'], 2)
        self.assertEqual(native['table']['headers'][0]['cells'][1]['colspan'], 2)
        self.assertEqual(native['table']['rows'][0]['cells'][1]['text'], '33.3')
        self.assertEqual(span['table']['source_representation'], 'latexml_tabular')
        self.assertEqual(span['table']['headers'][0]['cells'][1]['colspan'], 2)
        self.assertEqual(span['table']['rows'][0]['cells'][0]['text'], 'Beta')
        text = '\n'.join(block['text'] for block in packet['blocks'])
        for number in ('33.3', '44.4', '55.5', '66.6'):
            self.assertEqual(text.count(number), 1)
        self.assertEqual(packet['extraction_coverage']['native_html_table_count'], 1)
        self.assertEqual(packet['extraction_coverage']['semantic_table_count'], 2)

    def test_unmarked_table_headers_are_not_guessed_and_dl_grid_is_retained(self):
        raw = html('<div role="table" id="dl-table"><dl><dt id="dterm">Metric</dt><dd>77.7</dd></dl></div>'
                   '<span class="ltx_tabular" id="unmarked"><span class="ltx_tr"><span class="ltx_td">Model</span><span class="ltx_td">Value</span></span>'
                   '<span class="ltx_tr"><span class="ltx_td">Gamma</span><span class="ltx_td">88.8</span></span></span>')
        packet = self.packet(raw)
        table = next(block['table'] for block in packet['blocks'] if block['dom_id'] == 'unmarked')
        self.assertEqual(table['headers'], [])
        self.assertEqual(table['headers_status'], 'unmarked_not_inferred')
        self.assertEqual(len(table['rows']), 2)
        dl = next(block['table'] for block in packet['blocks'] if block['dom_id'] == 'dl-table')
        self.assertEqual([cell['text'] for cell in dl['rows'][0]['cells']], ['Metric', '77.7'])

    def test_nested_tables_and_caption_are_each_extracted_once(self):
        raw = html('<table id="outer"><tr><td>OUTER_CELL<table id="inner"><tr><td>INNER_CELL</td></tr></table></td></tr></table>')
        packet = self.packet(raw)
        self.assertEqual(len([block for block in packet['blocks'] if block['dom_id'] == 'inner']), 1)
        text = '\n'.join(block['text'] for block in packet['blocks'])
        self.assertEqual(text.count('INNER_CELL'), 1)
        self.assertEqual(text.count('OUTER_CELL'), 1)
        self.assertEqual(text.count('FIGURE_CAPTION_RETAINED'), 1)

    def test_equation_layout_tables_are_retained_but_never_named_result_table_counts(self):
        raw = html('<div class="ltx_equationgroup" id="equations"><table id="equation-table"><tr><td><math alttext="a=b"><mi>a</mi><mo>=</mo><mi>b</mi></math></td></tr></table></div>'
                   '<table id="direct-equation" class="ltx_eqn_table"><tr><td>c = d</td></tr></table>')
        packet = self.packet(raw)
        coverage = packet['extraction_coverage']
        self.assertEqual(coverage['semantic_table_count'], 4)
        self.assertEqual(coverage['equation_layout_table_count'], 2)
        self.assertEqual(coverage['other_table_structure_count'], 2)
        self.assertIn('NOT a count of research-result tables', coverage['table_count_definition'])
        table = next(block['table'] for block in packet['blocks'] if block['dom_id'] == 'equation-table')
        self.assertEqual(table['equation_container']['dom_id'], 'equations')
        self.assertEqual(table['semantic_kind'], 'equation_layout')
        self.assertIn('a=b', '\n'.join(block['text'] for block in packet['blocks']))

    def test_math_alternatives_figure_caption_and_image_links_are_preserved_not_inspected(self):
        packet = self.packet()
        math_block = next(block for block in packet['blocks'] if block['dom_id'] == 'equation')
        self.assertEqual(math_block['text'].count('x^2'), 1)
        self.assertEqual(math_block['math'][0]['dom_id'], 'm1')
        figure = next(block for block in packet['blocks'] if block['dom_id'] == 'F1')
        self.assertIn('FIGURE_CAPTION_RETAINED', figure['text'])
        self.assertEqual(figure['images'][0]['alt'], 'Robot and object')
        self.assertEqual(figure['images'][0]['source_url'], 'https://arxiv.org/html/thumb.png')
        self.assertEqual(figure['images'][0]['link_url'], 'https://arxiv.org/html/full.png')
        self.assertFalse(figure['images'][0]['image_inspected'])
        self.assertEqual(packet['extraction_coverage']['image_count'], 1)
        self.assertEqual(packet['extraction_coverage']['math_count'], 1)

    def test_conversion_and_missing_structure_gaps_are_reported_not_successfully_reviewed(self):
        packet = self.packet(html('<span id="bad" class="ltx_ERROR">UNKNOWN_MACRO</span>'
                                  '<math id="m2"><mi>y</mi><mo>+</mo><mn>1</mn></math>'
                                  '<figure class="ltx_table" id="image-table"><figcaption>Table 8. Image-only results.</figcaption><img src="results.png"></figure>'))
        codes = {issue['code'] for issue in packet['issues']}
        self.assertTrue({'html_conversion_error_marker', 'math_without_alttext_or_tex', 'image_alt_missing', 'table_container_without_recognized_tabular_structure'} <= codes)
        self.assertIn('UNKNOWN_MACRO', '\n'.join(block['text'] for block in packet['blocks']))
        self.assertEqual(packet['extraction_coverage']['unparsed_table_structure_count'], 1)
        self.assertEqual(packet['reading_coverage']['tables_read'], 0)

    def test_raw_hash_canonical_identity_and_version_mismatches_fail_closed(self):
        for target in ('hash', 'work', 'id', 'version', 'page_proof', 'url'):
            with self.subTest(target=target):
                raw, obs, work = inputs()
                if target == 'hash': obs['raw_sha256'] = 'f' * 64
                elif target == 'work': work['work_id'] = 'another-work'
                elif target == 'id':
                    work['identifiers']['arxiv'] = '2407.99999'; work['aliases'] = []
                elif target == 'version': obs['version'] = 'v2'
                elif target == 'page_proof':
                    raw = raw.replace((AID + 'v1').encode(), b'2407.99999v1', 1); obs['raw_sha256'] = sha256(raw)
                else: obs['effective_url'] = 'https://example.org/html/' + AID + 'v1'
                with self.assertRaises(ValueError): build_reading_packet(raw, obs, work)

    def test_segments_are_lossless_bounded_and_eof_does_not_record_reading(self):
        packet = self.packet(html('<p id="long">' + ('Long source paragraph. ' * 90) + '</p>'), segment_chars=200)
        chunks = {}
        for segment in packet['reading_segments']:
            block = packet['blocks'][segment['block_index'] - 1]
            text = block['text'][segment['start_char']:segment['end_char']]
            self.assertLessEqual(len(text), 200)
            chunks.setdefault(segment['block_index'], []).append(text)
        for block in packet['blocks']:
            self.assertEqual(''.join(chunks[block['block_index']]), block['text'])
        before = copy.deepcopy(packet)
        self.assertIn('NEXT --start 2', render_range(packet, 1, 1))
        self.assertIn('EOF', render_range(packet, len(packet['reading_segments']), len(packet['reading_segments'])))
        self.assertEqual(packet, before)
        with self.assertRaises(ValueError): render_range(packet, 1, 0)

    def test_preparation_is_deterministic_idempotent_and_never_changes_source_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            cache, observations, catalog, output, raw_path = disk_fixture(Path(directory))
            before = {path: path.read_bytes() for path in (raw_path, observations)}
            first = prepare_packets(observations, cache, catalog, output, work_ids=[WID])
            second = prepare_packets(observations, cache, catalog, output, work_ids=[WID])
            self.assertEqual(first['prepared_count'], 1)
            self.assertTrue(first['prepared'][0]['changed'])
            self.assertFalse(second['prepared'][0]['changed'])
            self.assertEqual(first['prepared'][0]['packet_sha256'], second['prepared'][0]['packet_sha256'])
            self.assertEqual({path: path.read_bytes() for path in before}, before)
            self.assertFalse(load_packet(output, WID)['reading_coverage']['article_read_complete'])
            self.assertEqual(stat.S_IMODE((output / 'packets' / packet_filename(WID)).stat().st_mode), 0o600)

    def test_cache_symlink_traversal_and_output_symlink_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache, observations, catalog, output, raw_path = disk_fixture(root)
            linked = cache / 'objects/link.html'; linked.symlink_to(raw_path)
            with self.assertRaisesRegex(ValueError, 'symlink'): trusted_file(linked, cache / 'objects')
            with self.assertRaisesRegex(ValueError, 'traversal'): trusted_file(cache / 'objects/../objects' / raw_path.name, cache / 'objects')
            outside = root / 'outside.html'; outside.write_bytes(raw_path.read_bytes())
            with self.assertRaisesRegex(ValueError, 'outside_root'): trusted_file(outside, cache / 'objects')
            output.mkdir(); (output / 'packets').symlink_to(cache / 'objects', target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'symlink'): write_packet(self.packet(), output)

    def test_output_cannot_be_inside_source_cache_and_append_tail_is_not_repaired(self):
        with tempfile.TemporaryDirectory() as directory:
            cache, observations, catalog, output, _ = disk_fixture(Path(directory))
            with self.assertRaisesRegex(ValueError, 'modify_source_cache'):
                prepare_packets(observations, cache, catalog, cache / 'packets', work_ids=[WID])
            observations.write_text(observations.read_text() + '{"work_id":')
            before = observations.read_bytes()
            result = prepare_packets(observations, cache, catalog, output, work_ids=[WID])
            self.assertTrue(result['observation_snapshot_incomplete_tail'])
            self.assertEqual(result['prepared_count'], 1)
            self.assertEqual(observations.read_bytes(), before)

    def test_reading_record_is_unsubmitted_template_without_auto_claims_or_ranges(self):
        packet = self.packet()
        record = reading_record_template(packet)
        self.assertEqual(record['record_status'], 'template_only_not_a_read_record')
        self.assertEqual(record['source']['raw_sha256'], packet['source']['raw_sha256'])
        self.assertEqual(record['declared_read_ranges'], [])
        self.assertEqual(record['verified_claims'], [])
        self.assertEqual(record['images_inspected'], [])
        self.assertIsNone(record['declared_eof_reached'])
        self.assertIsNone(record['reader_id'])

    def test_cli_summary_show_template_are_readonly_and_private_output_is_required(self):
        with tempfile.TemporaryDirectory() as directory:
            cache, observations, catalog, output, _ = disk_fixture(Path(directory))
            prepare_packets(observations, cache, catalog, output, work_ids=[WID])
            saved = output / 'packets' / packet_filename(WID)
            before = saved.read_bytes()
            for action in ('--summary', '--show', '--record-template'):
                with contextlib.redirect_stdout(io.StringIO()) as stream:
                    self.assertEqual(main([action, WID, '--output', str(output), '--start', '1', '--end', '1']), 0)
                self.assertTrue(stream.getvalue())
                self.assertEqual(saved.read_bytes(), before)
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main(['--all-cached', '--output', str(Path(directory) / 'docs/public')])

    def test_relative_cli_paths_are_resolved_from_working_directory_not_doubled(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache, observations, catalog, output, _ = disk_fixture(root)
            previous = Path.cwd()
            try:
                os.chdir(root)
                result = prepare_packets(observations.relative_to(root), cache.relative_to(root),
                                         catalog.relative_to(root), output.relative_to(root), work_ids=[WID])
                self.assertEqual(result['prepared_count'], 1)
                self.assertEqual(load_packet(output.relative_to(root), WID)['work_id'], WID)
            finally:
                os.chdir(previous)


if __name__ == '__main__':
    unittest.main()
