"""Bounded weekly workers. No credentials, notifications, or production config."""
from __future__ import annotations
import contextlib
import hashlib
import math
import json
import os
import re
import signal
import subprocess
import sys
import time
from contextvars import ContextVar
from pathlib import Path

COLLECTION_MODE = ContextVar('weekly_collection_mode',default=False)
PIPELINE_DEADLINE = ContextVar('weekly_pipeline_deadline',default=None)

@contextlib.contextmanager
def pipeline_budget(seconds=5400):
    mode=COLLECTION_MODE.set(True)
    deadline=PIPELINE_DEADLINE.set(time.monotonic()+seconds)
    try:
        yield
    finally:
        PIPELINE_DEADLINE.reset(deadline)
        COLLECTION_MODE.reset(mode)

def remaining_pipeline_budget():
    deadline=PIPELINE_DEADLINE.get()
    return None if deadline is None else max(0,deadline-time.monotonic())

def owned_resume(root, allowed, *, save=False):
    """Resume only exact, previously recorded data changes; never user/code edits."""
    manifest=root/'.research/weekly-v3/owned-resume.json'
    def git(*args):
        return subprocess.check_output(['git',*args],cwd=root,text=True).strip()
    raw=subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all'],cwd=root)
    paths={}
    for entry in raw.split(b'\0'):
        if not entry: continue
        status=entry[:2].decode();name=entry[3:].decode()
        if 'R' in status or 'C' in status:
            return False
        if not any(name==a or name.startswith(a+'/') for a in allowed):
            return False
        p=root/name
        if p.is_symlink() or not p.resolve().is_relative_to(root.resolve()): return False
        paths[name]=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
    value={'base_sha':git('rev-parse','HEAD'),'paths':paths}
    if save:
        manifest.parent.mkdir(parents=True,exist_ok=True)
        pending=manifest.with_suffix('.tmp');pending.write_text(json.dumps(value,sort_keys=True));pending.replace(manifest)
        return True
    if not manifest.exists(): return False
    return json.loads(manifest.read_text())==value

class QueryBudgetExpired(BaseException):
    """Not swallowed by collectors' broad network retry handlers."""

@contextlib.contextmanager
def query_budget(seconds=60):
    def expired(*_):
        raise QueryBudgetExpired()
    old = signal.signal(signal.SIGALRM, expired)
    prior = signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, *prior)
        signal.signal(signal.SIGALRM, old)

def run_process(command, *, cwd, timeout, env=None):
    """Kill the complete worker group on timeout, including subprocesses."""
    process = subprocess.Popen(command, cwd=cwd, env=env, start_new_session=True)
    try:
        code = process.wait(timeout=timeout)
    except BaseException as error:
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=5)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
        error.returncode = process.returncode
        raise
    if code:
        raise subprocess.CalledProcessError(code, command)

def cpu_idle_iostat(text):
    if not re.search(r'\bus\s+sy\s+id\b',text):raise ValueError('iostat_cpu_header_missing')
    rows=[line.split() for line in text.splitlines() if re.match(r'^\s*\d',line)]
    if len(rows)<2 or len(rows[-1])<6:raise ValueError('iostat_current_cpu_sample_missing')
    idle=float(rows[-1][-4])
    if not math.isfinite(idle) or not 0<=idle<=100:raise ValueError('iostat_cpu_idle_invalid')
    return idle


def resource_reason():
    if os.environ.get('RADAR_WEEKLY_RESOURCE_GUARD') != '1':
        return None
    if sys.platform != 'darwin':
        return 'resource_probe_platform_unsupported'
    try:
        def probe(argv):
            return subprocess.check_output(argv, text=True, timeout=20)
        free = int(re.search(r'free percentage:\s*(\d+)%', probe(['/usr/bin/memory_pressure', '-Q'])).group(1))
        idle = cpu_idle_iostat(probe(['/usr/sbin/iostat','-c','2','-w','1']))
        rows = []
        for line in probe(['/bin/ps','-axo','pid,ppid,rss,%cpu,command']).splitlines()[1:]:
            parts = line.split(None,4)
            if len(parts)==5:
                rows.append((int(parts[0]),int(parts[1]),int(parts[2]),float(parts[3]),parts[4]))
        names = {'run_weekly_v3.py','run_mini_weekly.py','run_token_free_scheduled.py',
                 'governed_token_free_research.py','publish_token_free_batch.py','token_free_research.py'}
        owned = {os.getpid()}
        logger = set()
        for pid,ppid,rss,cpu,command in rows:
            argv=command.split()
            if argv and 'python' in Path(argv[0]).name.lower() and any(Path(x).name in names for x in argv[1:]):
                owned.add(pid)
            if '/loggerbot/' in command or '/LoggerBot/' in command:
                logger.add(pid)
        for _ in range(16):
            owned.update(p for p,parent,*_ in rows if parent in owned)
            logger.update(p for p,parent,*_ in rows if parent in logger)
        print(json.dumps({'status':'resource_observation','free_percent':free,'cpu_busy_percent':round(100-idle,2),'pipeline_rss_mib':round(sum(rss for pid,_,rss,_,_ in rows if pid in owned)/1024,1)}),flush=True)
        if free<50: return 'logger_memory_reserve'
        if 100-idle>50: return 'cpu_headroom'
        if sum(rss for pid,_,rss,_,_ in rows if pid in owned)/1024>1280: return 'pipeline_memory_budget'
        if sum(cpu for pid,_,_,cpu,_ in rows if pid in logger)>300: return 'logger_busy'
    except (OSError,ValueError,AttributeError,subprocess.SubprocessError) as error:
        detail={'status':'resource_probe_failed','error_type':type(error).__name__}
        if isinstance(error,(subprocess.TimeoutExpired,subprocess.CalledProcessError)):
            detail['command']=error.cmd
            detail['exit_code']=getattr(error,'returncode',None)
            detail['timeout_seconds']=getattr(error,'timeout',None)
        print(json.dumps(detail),flush=True)
        return 'resource_probe_failed'
    return None

def wait_resource_headroom(seconds=60):
    deadline=time.monotonic()+max(0,seconds)
    why=resource_reason()
    while why in {'cpu_headroom','logger_busy','logger_memory_reserve','pipeline_memory_budget'} and time.monotonic()<deadline:
        print(json.dumps({'status':'waiting_resource_pressure','reason':why}),flush=True)
        time.sleep(min(10,max(0,deadline-time.monotonic())))
        why=resource_reason()
    return why


def bounded_sources(root, cutoff, now, baseline, *, source_seconds=300, total_seconds=1800):
    """One worker per source, with durable partial progress on interruption."""
    deadline=time.monotonic()+total_seconds
    folder=root/'.research/weekly-v3'/cutoff.isoformat()
    folder.mkdir(parents=True,exist_ok=True)
    baseline_path=folder/'status-baseline.json'
    # Preserve the pre-arXiv baseline across retries of this same cutoff.
    if not baseline_path.exists():
        pending=baseline_path.with_suffix('.tmp');pending.write_text(json.dumps(baseline));pending.replace(baseline_path)
    results=[]
    for source in ('arxiv','arxiv_research_status','publications','official_groups','corl'):
        remaining=deadline-time.monotonic()
        why=wait_resource_headroom(min(60,max(0,remaining)))
        remaining=deadline-time.monotonic()
        if remaining<=0 or why:
            results.append({'source':source,'status':'failed','complete':False,
                            'error_type':why or 'TotalCollectionBudgetExceeded','source_data_through':None})
            continue
        result_path=folder/(source+'-result.json')
        result_path.unlink(missing_ok=True)
        command=[sys.executable,str(root/'scripts/run_weekly_v3.py'),'--collect-source',source,
                 '--as-of',cutoff.isoformat(),'--source-result',str(result_path),
                 '--status-baseline',str(baseline_path)]
        print(json.dumps({'status':'source_started','source':source,'budget_seconds':min(source_seconds,remaining)}),flush=True)
        error=None
        try:
            run_process(command,cwd=root,timeout=min(source_seconds,remaining))
        except subprocess.TimeoutExpired:
            error='SourceBudgetExceeded'
        except subprocess.CalledProcessError:
            error='SourceWorkerFailed'
        value=json.loads(result_path.read_text()) if result_path.exists() else {}
        if value.get('source')!=source or value.get('requested_cutoff')!=cutoff.isoformat():
            value={'source':source,'status':'failed','complete':False,'source_data_through':None}
        if error:
            value.update(status='partial' if value.get('observed_records',0) else 'failed',
                         complete=False,source_data_through=None,error_type=error)
        results.append(value)
        print(json.dumps({'status':'source_finished','source':source,'result':value.get('status'),
                          'error_type':value.get('error_type')}),flush=True)
    return results
