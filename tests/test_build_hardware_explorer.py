import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_hardware_explorer import build,citation_index,select_citation,month,PRESENTATION_OVERRIDES
from test_export_token_free_public import record
class ExplorerTests(unittest.TestCase):
 def test_citation_identity_zero_conflict_and_provenance(self):
  p={'work_id':'doi:example','doi':'example','semantic_scholar_id':'a'*40,'citation_count_snapshot':0,'citation_snapshot_date':'2026-08-31'}
  w={'work_id':'arxiv:2609.00001','aliases':['doi:example']}
  c=select_citation(w,citation_index([p]));self.assertEqual(c['count'],0);self.assertIsNone(c['queried_at']);self.assertEqual(c['source_url'],'https://www.semanticscholar.org/paper/'+'a'*40)
  self.assertIsNone(select_citation(w,citation_index([p,{**p,'semantic_scholar_id':'b'*40}])))
  self.assertIsNone(select_citation(w,citation_index([p,{**p,'citation_count_snapshot':2}])))
  self.assertIsNone(select_citation({'work_id':'different','aliases':[]},citation_index([p])))
 def test_display_only_join_keeps_public_hash_source_and_unknown_dates(self):
  with tempfile.TemporaryDirectory() as folder:
   r=Path(folder);(r/'catalog/works').mkdir(parents=True)
   source=r/'records.jsonl';source.write_text(json.dumps(record())+'\n');before=source.read_bytes()
   (r/'catalog/works/00.jsonl').write_text(json.dumps({'work_id':'arxiv:2609.00001','title':'Paper','first_public_date':'2026','first_public_date_precision':'year','identifiers':{'arxiv':'2609.00001'},'aliases':[]})+'\n')
   (r/'publications.json').write_text('[]');(r/'dictionary.json').write_text('{"entries":[]}')
   v=build(source,r/'catalog',r/'publications.json',r/'dictionary.json',r/'api')
   self.assertEqual(source.read_bytes(),before);self.assertIsNone(v['rows'][0]['month']);self.assertIsNone(v['rows'][0]['citation']);self.assertEqual(v['usage_verified_count'],0);self.assertFalse(v['rows'][0]['matches'][0]['usage_verified'])
   self.assertEqual(v['unknown_month_count'],1)
 def test_month_precision_not_invented_and_invalid_dates_rejected(self):
  self.assertIsNone(month({'first_public_date':'2026','first_public_date_precision':'year'}))
  self.assertIsNone(month({'first_public_date':'2026-02-30','first_public_date_precision':'day'}))
  self.assertEqual(month({'first_public_date':'2026-02','first_public_date_precision':'month'}),'2026-02')
  self.assertEqual(PRESENTATION_OVERRIDES['model:aloha-system'],'arms')
  self.assertNotIn('model:mobile-aloha-system',PRESENTATION_OVERRIDES)
