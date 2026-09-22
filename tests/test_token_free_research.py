import contextlib
import gzip
import io
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import token_free_research as runner
from collect_hardware_sources import digest
from prepare_fulltext_reading import build_reading_packet

WID = 'arxiv:2609.04545'
DICTIONARY = {'schema_version':'1', 'entries':[{
    'dictionary_id':'model:g1','name':'Unitree G1','aliases':['G1'],
    'context_terms':['robot','Unitree'],'category':'robot_platform','identity_level':'model_specified'}]}


class TokenFreeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.catalog, self.cache, self.output = base/'catalog', base/'cache', base/'output'
        self.catalog.mkdir()
        (self.cache/'objects').mkdir(parents=True)
        self.work = {'work_id':WID,'title':'World model on a robot','abstract':'Metadata only',
                     'identifiers':{'arxiv':'2609.04545'},'relevance':'included',
                     'first_public_date':'2026-09-05','first_public_date_precision':'day'}
        self.other = {'work_id':'doi:10.1/external','title':'Public technical report',
                      'abstract':'','identifiers':{},'relevance':'excluded'}
        (self.catalog/'works.jsonl').write_text('\n'.join(map(json.dumps,[self.work,self.other]))+'\n')
        self.raw = b'''<html><head><meta name="citation_arxiv_id" content="2609.04545v1"></head>
        <article><h1>World model</h1><section id="S1"><h2>Methods</h2>
        <p>We use a Unitree G1 robot in simulation. NVIDIA RTX 9876 GPU is an unknown name.</p>
        <table id="T1"><tr><th>Count</th></tr><tr><td>17</td></tr></table></section>
        <section id="A1" class="ltx_appendix"><h2>Appendix</h2></section>
        <section id="bib" class="ltx_bibliography"><h2>References</h2><p>Other Unitree G1 robot.</p></section>
        </article></html>'''
        path = self.cache/'objects'/f'{digest(self.raw)}.html'
        path.write_bytes(self.raw)
        self.source = {'work_id':WID,'arxiv_id':'2609.04545','version':'v1',
            'source_url':'https://arxiv.org/html/2609.04545v1','status':'full_text_available',
            'observed_at':'2026-09-15T00:00:00Z','raw_sha256':digest(self.raw),
            'transport_verification':'complete','cache_ref':str(path)}
        self.write_source()

    def write_source(self):
        (self.cache/'observations.jsonl').write_text(json.dumps(self.source)+'\n')

    def run_it(self, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return runner.run(self.catalog,self.cache,self.output,DICTIONARY,**kwargs)

    def test_offline_never_initializes_network_and_preserves_inputs(self):
        before = {p:p.read_bytes() for d in [self.catalog,self.cache] for p in d.rglob('*') if p.is_file()}
        with patch.object(runner,'Collector',side_effect=AssertionError('Network forbidden')):
            result = self.run_it()
        self.assertEqual(result['model_calls'],0)
        self.assertEqual(result['catalog_work_count'],2)
        self.assertEqual(result['new_complete_reading_receipts'],0)
        self.assertEqual(result['processing_states'],{'extracted_not_read':1,'source_needed':1})
        for p, raw in before.items():
            self.assertEqual(p.read_bytes(),raw)

    def test_full_text_and_warnings_retained_without_verification(self):
        self.run_it()
        card = json.loads(gzip.decompress(next((self.output/'cards').glob('*.gz')).read_bytes()))
        self.assertFalse(card['article_read_complete'])
        self.assertIn('empty_section:A1',card['warnings'])
        self.assertTrue(any('17' in b['text'] for b in card['blocks']))
        self.assertTrue(any('Other Unitree G1' in b['text'] for b in card['blocks']))
        self.assertTrue(card['unknown_name_candidates'])
        self.assertTrue(any(c['context_only'] for c in card['hardware_candidates']))
        queue = [json.loads(l) for l in (self.output/'source-review-queue.jsonl').read_text().splitlines()]
        self.assertIn('empty_section:A1',next(r for r in queue if r['work_id']==WID)['reason'])

    def test_frequency_deduplicates_work_and_keeps_sources(self):
        self.run_it()
        ranks = json.loads((self.output/'hardware-candidate-frequency.json').read_text())
        self.assertEqual(ranks[0]['candidate_work_count'],1)
        sources = [json.loads(l) for l in (self.output/'hardware-candidate-sources.jsonl').read_text().splitlines()]
        self.assertEqual(len(sources),2)
        self.assertTrue(all(not s['usage_verified'] for s in sources))

    def test_resume_no_reparse(self):
        self.run_it()
        with patch.object(runner,'build_reading_packet',side_effect=AssertionError('Repeated parse')):
            self.assertEqual(self.run_it()['run']['counts']['reused'],1)

    def test_changed_source_invalidates_old_candidates_and_fulltext(self):
        self.run_it()
        self.source.update(status='unavailable',observed_at='2026-09-16T00:00:00Z')
        self.write_source()
        self.run_it()
        self.assertEqual(json.loads((self.output/'hardware-candidate-frequency.json').read_text()),[])
        self.assertEqual(self.run_it(query='Unitree G1')['results'],[])

    def test_missing_card_rebuilt_and_no_duplicates(self):
        self.run_it()
        next((self.output/'cards').glob('*.gz')).unlink()
        self.assertEqual(self.run_it()['run']['counts']['extracted_not_read'],1)
        self.assertEqual(json.loads((self.output/'hardware-candidate-frequency.json').read_text())[0]['candidate_work_count'],1)

    def test_published_receipt_survives_cache_cleanup_and_flags_changed_rules(self):
        self.source['observation_id'] = 'hardware-source:' + 'a' * 32
        self.write_source()
        self.run_it()
        with sqlite3.connect(self.output/'research.sqlite') as db:
            processing_key = db.execute('SELECT source_key FROM works WHERE work_id=?', (WID,)).fetchone()[0]
            db.execute('UPDATE works SET reason=NULL WHERE work_id=?', (WID,))
            db.commit()
        receipt = {'work_id':WID, 'observation_id':self.source['observation_id'],
                   'processing_key':processing_key, 'record_sha256':'b'*64,
                   'commit_sha':'c'*40, 'published_at':'2026-09-22T00:00:00Z',
                   'process_state':'extracted_not_read'}
        (self.output/'published-receipts.jsonl').write_text(json.dumps(receipt)+'\n')
        next((self.output/'cards').glob('*.gz')).unlink()
        Path(self.source['cache_ref']).unlink()
        with patch.object(runner,'build_reading_packet',side_effect=AssertionError('Repeated parse')):
            result = self.run_it()
            self.assertEqual(result['run']['counts']['published_compacted'],1)
            self.assertEqual(result['processing_states']['published_compacted'],1)
            self.assertEqual(result['source_states']['full_text_available'],1)
            queue = [json.loads(line) for line in (self.output/'source-review-queue.jsonl').read_text().splitlines()]
            self.assertNotIn(WID, [row['work_id'] for row in queue])
            with patch.object(runner,'pipeline_hash',return_value='changed-rules'):
                changed = self.run_it()
                repeated = self.run_it()
        self.assertEqual(changed['processing_states']['refresh_needed'],1)
        self.assertEqual(repeated['run']['counts']['refresh_needed'],1)
        queue = [json.loads(line) for line in (self.output/'source-review-queue.jsonl').read_text().splitlines()]
        self.assertEqual(next(row for row in queue if row['work_id'] == WID)['process_state'], 'refresh_needed')

    def test_conflicting_published_receipts_rejected(self):
        receipt = {'work_id':WID, 'observation_id':'hardware-source:'+'a'*32,
                   'processing_key':'a'*64, 'record_sha256':'b'*64,
                   'commit_sha':'c'*40, 'published_at':'2026-09-22T00:00:00Z',
                   'process_state':'extracted_not_read'}
        self.output.mkdir()
        (self.output/'published-receipts.jsonl').write_text(
            json.dumps(receipt)+'\n'+json.dumps({**receipt,'record_sha256':'d'*64})+'\n')
        with self.assertRaisesRegex(ValueError,'conflicting_published_receipt'):
            runner.read_published_receipts(self.output)

    def test_search_fulltext_and_chinese_alias(self):
        self.run_it()
        self.assertEqual(self.run_it(query='Unitree G1')['results'][0]['work_id'],WID)
        self.assertEqual(self.run_it(query='世界模型')['results'][0]['work_id'],WID)
        self.assertEqual(self.run_it(query='" OR *')['results'],[])

    def test_hash_mismatch_is_failure_not_reading(self):
        Path(self.source['cache_ref']).write_bytes(b'changed')
        result = self.run_it()
        self.assertEqual(result['processing_states']['extraction_failed'],1)
        self.assertEqual(result['new_verified_usage_assertions'],0)

    def test_no_hit_is_still_unreviewed(self):
        packet = build_reading_packet(self.raw,self.source,self.work)
        empty = {'schema_version':'1','entries':[]}
        card = runner.analyse_packet(packet,empty)
        self.assertFalse(card['article_read_complete'])
        self.assertEqual(card['hardware_candidates'],[])

    def test_incomplete_tail_preserved_corrupt_middle_rejected(self):
        path = self.cache/'observations.jsonl'
        raw = path.read_bytes()+b'{"work_id":'
        path.write_bytes(raw)
        self.assertTrue(runner.read_log(path)[1])
        self.assertEqual(path.read_bytes(),raw)
        path.write_bytes(b'BAD\n'+raw)
        with self.assertRaisesRegex(ValueError,'corrupt_observation_log'):
            runner.read_log(path)

    def test_blocked_source_prevents_new_network_calls(self):
        self.source['status']='blocked'
        self.write_source()
        with patch.object(runner,'Collector',side_effect=AssertionError('Blocked')):
            result=self.run_it(fetch=True)
        self.assertEqual(result['run']['fetch']['attempted'],0)

    def test_symlink_output_rejected(self):
        self.output.mkdir()
        (self.output/'research.sqlite').symlink_to(self.catalog/'works.jsonl')
        with self.assertRaisesRegex(ValueError,'symlink_output_forbidden'):
            self.run_it()

    def test_current_catalog_relevance_shape(self):
        self.assertEqual(runner.relevance({'relevance':{'status':'included'}}),'included')

    def test_new_source_only_collection_and_no_retry(self):
        third = {**self.work,'work_id':'arxiv:2609.99999','identifiers':{'arxiv':'2609.99999'}}
        with (self.catalog/'works.jsonl').open('a') as f:
            f.write(json.dumps(third)+'\n')
        with patch.object(runner,'Collector') as collector:
            collector.return_value.run.return_value={'attempted':0}
            self.run_it(fetch=True,fetch_limit=2)
            targets=collector.return_value.run.call_args.args[0]
            self.assertEqual([t['work_id'] for t in targets],[third['work_id']])
            self.assertNotIn('retry_failed',collector.return_value.run.call_args.kwargs)


if __name__=='__main__':
    unittest.main()
