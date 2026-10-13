"""Offline recovery checks: no production env, registries, data, or network."""
import importlib.util,json,os,subprocess,sys,tempfile,time,unittest
from datetime import date,datetime,timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import weekly_runtime as runtime
import run_weekly_v3 as weekly

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.env=patch.dict(os.environ,{'GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_SYSTEM':'/dev/null'},clear=True);self.env.start();self.addCleanup(self.env.stop)
    def test_query_deadline_escapes_broad_retry_handler_and_restores_alarm(self):
        import signal
        prior=signal.getsignal(signal.SIGALRM)
        with self.assertRaises(runtime.QueryBudgetExpired):
            with runtime.query_budget(.02):
                try:time.sleep(.2)
                except Exception:self.fail('Deadline swallowed by broad network retry')
        self.assertEqual(signal.getsignal(signal.SIGALRM),prior)
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL),(0.0,0.0))
    def test_worker_timeout_terminates_process_group(self):
        with tempfile.TemporaryDirectory() as folder:
            start=time.monotonic()
            with self.assertRaises(subprocess.TimeoutExpired):
                runtime.run_process([sys.executable,'-c','import time;time.sleep(10)'],cwd=folder,timeout=.03)
            self.assertLess(time.monotonic()-start,2)
    def test_partial_worker_keeps_observed_counts_but_never_complete_cutoff(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            def worker(command,**kwargs):
                source=command[command.index('--collect-source')+1]
                path=Path(command[command.index('--source-result')+1])
                path.write_text(json.dumps({'source':source,'requested_cutoff':'2026-10-12','status':'ok','complete':True,'observed_records':2,'source_data_through':'2026-10-12'}))
                if source=='arxiv':raise subprocess.TimeoutExpired(command,1)
            with patch.object(runtime,'run_process',side_effect=worker):
                results=runtime.bounded_sources(root,date(2026,10,12),datetime.now(timezone.utc),[],source_seconds=1,total_seconds=10)
            self.assertEqual(len(results),5);self.assertEqual(results[0]['status'],'partial')
            self.assertFalse(results[0]['complete']);self.assertIsNone(results[0]['source_data_through'])
            self.assertEqual(results[0]['observed_records'],2)
    def test_resource_pause_starts_no_workers_and_marks_every_source_incomplete(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(runtime,'resource_reason',return_value='logger_memory_reserve'),patch.object(runtime,'run_process') as worker:
            checks=runtime.bounded_sources(Path(folder),date(2026,10,12),datetime.now(timezone.utc),[])
            worker.assert_not_called();self.assertEqual(len(checks),5)
            self.assertTrue(all(not c['complete'] and c['error_type']=='logger_memory_reserve' for c in checks))
    def test_arxiv_resume_keeps_exact_query_scope_and_completed_pages(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);raw=root/'raw';raw.mkdir()
            fake=SimpleNamespace(RAW=raw,REGISTRY={'window':{},'arxiv_sources':{'queries':[{'id':'one','query':'robot'}]}},OUTPUT=root/'preprints.json',COVERAGE=root/'coverage.json',classify=lambda rows:None,summarize=lambda rows:{"count":len(rows)},merge_record=lambda a,b,q:{**a,**b})
            calls=[];failed=[False]
            def fetch(q,query,month,offset,size):
                calls.append((month,offset))
                if month=='2026-09' and offset==1 and not failed[0]:
                    failed[0]=True;raise runtime.QueryBudgetExpired()
                return json.dumps({'total':2 if month=='2026-09' else 0,'rows':[{'arxiv_id':'a' if offset==0 else 'b','first_submitted':month+'-01'}] if month=='2026-09' else []})
            fake.fetch=fetch;fake.parse_feed=lambda body:(json.loads(body)['total'],json.loads(body)['rows'])
            with patch.object(weekly,'ROOT',root),patch.object(weekly.importlib,'import_module',return_value=fake),patch.object(weekly,'resource_reason',return_value=None):
                first=weekly.collect_arxiv(date(2026,10,12),bounded=True)
                self.assertFalse(first['complete'])
                calls.clear();second=weekly.collect_arxiv(date(2026,10,12),bounded=True)
                self.assertTrue(second['complete']);self.assertEqual(calls,[('2026-09',1)])
                rows=json.loads(fake.OUTPUT.read_text());self.assertEqual({r['arxiv_id'] for r in rows},{'a','b'})
                calls.clear();weekly.collect_arxiv(date(2026,10,13),bounded=True)
                self.assertIn(('2026-09',0),calls)
    def test_resume_refuses_foreign_changes_and_changed_owned_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            def git(*args):subprocess.run(['git',*args],cwd=root,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            git('init','-q');git('config','user.name','Fixture');git('config','user.email','fixture@example.test')
            (root/'.gitignore').write_text('.research/\n');(root/'data').mkdir();f=root/'data/example.json';f.write_text('{}')
            git('add','.');git('commit','-qm','fixture')
            f.write_text('{"partial":1}')
            self.assertTrue(runtime.owned_resume(root,['data'],save=True))
            self.assertTrue(runtime.owned_resume(root,['data']))
            f.write_text('{"user":1}');self.assertFalse(runtime.owned_resume(root,['data']))
            f.write_text('{"partial":1}');(root/'notes.txt').write_text('user notes')
            self.assertFalse(runtime.owned_resume(root,['data']));self.assertFalse(runtime.owned_resume(root,['data'],save=True))
    def test_total_pipeline_deadline_and_context_reset(self):
        with patch.object(runtime.time,'monotonic',side_effect=[10,12]):
            with runtime.pipeline_budget(1):
                self.assertTrue(runtime.COLLECTION_MODE.get());self.assertEqual(runtime.remaining_pipeline_budget(),0)
        self.assertFalse(runtime.COLLECTION_MODE.get());self.assertIsNone(runtime.remaining_pipeline_budget())
    def test_mini_schedule_preserves_real_four_am_and_has_no_credentials(self):
        import install_weekly_launchd as installer
        root=Path('/fixture/weekly')
        p=installer.build_mini_plist(root,'/fixture/python','/fixture/node','/fixture/npm')
        self.assertEqual(p['StartCalendarInterval'],{'Weekday':1,'Hour':4,'Minute':0})
        self.assertEqual(p['ProgramArguments'],['/fixture/python','/fixture/weekly/scripts/run_mini_weekly.py','--run'])
        self.assertEqual(p['Nice'],15);self.assertTrue(p['LowPriorityIO']);self.assertFalse(p['RunAtLoad'])
        self.assertNotIn('FEISHU_APP_SECRET',p['EnvironmentVariables'])
        self.assertNotIn('--env-file',p['ProgramArguments'])
    def test_wrong_hardware_is_rejected_before_any_mutation(self):
        import run_mini_weekly as mini
        with patch.object(mini.sys,'platform','darwin'),patch.object(mini.subprocess,'check_output',side_effect=[json.dumps({'SPHardwareDataType':[{'machine_name':'MacBook Pro','machine_model':'MacBookPro18,3'}]}),'main']),patch.object(mini.shutil,'which',return_value='/fixture/bin'):
            self.assertIn('unverified_mini_hardware',mini.preflight(Path('/fixture')))
    def test_status_cache_preserves_real_clock_and_cutoff_identity(self):
        from weekly_status_cache import fetchers
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);calls=[]
            mf,_,clock,_=fetchers(root,'2026-10-12',lambda ids:calls.append(ids) or [{'arxiv_id':ids[0]}],lambda *_:None)
            self.assertEqual(mf(['2401.00001']),[{'arxiv_id':'2401.00001'}])
            cache=next(root.glob('*.json'));r=json.loads(cache.read_text());r['observed_at']='2026-10-12T01:02:03+00:00';cache.write_text(json.dumps(r))
            again,_,old_clock,_=fetchers(root,'2026-10-12',lambda _:self.fail('Cached batch must not fetch'),lambda *_:None)
            again(['2401.00001']);self.assertEqual(old_clock(),'2026-10-12T01:02:03+00:00')
            fresh,_,_,_=fetchers(root,'2026-10-13',lambda ids:calls.append(ids) or [],lambda *_:None)
            fresh(['2401.00001']);self.assertEqual(len(calls),2)
    def test_cached_response_clocks_are_audit_fields_not_research_revisions(self):
        a={'source':'arxiv_research_status','status':'partial','response_observed_from':'2026-10-12T00:00:00Z','response_observed_until':'2026-10-12T01:00:00Z'}
        b={**a,'response_observed_from':'2026-10-13T00:00:00Z','response_observed_until':'2026-10-13T01:00:00Z'}
        self.assertEqual(weekly.content_hash(a),weekly.content_hash(b))
