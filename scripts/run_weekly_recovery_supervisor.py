"""Detached, bounded Mini recovery supervisor with a durable final exit record."""
from __future__ import annotations
import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from run_mini_weekly import preflight
from run_weekly_v3 import STAGED_PATHS
from weekly_runtime import owned_resume

ROOT = Path(__file__).resolve().parents[1]


def run_supervised(command, root, record_path, *, seconds=5400):
    def now(): return datetime.now(timezone.utc).isoformat()
    record = {'supervisor_pid':os.getpid(),'started_at':now(),'status':'starting','budget_seconds':seconds}
    def persist(**values):
        record.update(values);record_path.parent.mkdir(parents=True,exist_ok=True)
        pending=record_path.with_suffix('.tmp');pending.write_text(json.dumps(record,sort_keys=True));pending.replace(record_path)
    def interrupted(signum, _frame): raise RuntimeError('SupervisorInterruptedSignal:' + str(signum))
    previous={sig:signal.signal(sig,interrupted) for sig in (signal.SIGTERM,signal.SIGHUP)}
    process=None;clock=time.monotonic()
    try:
        process=subprocess.Popen(command,cwd=root,start_new_session=True)
        persist(status='running',pid=process.pid)
        code=process.wait(timeout=seconds)
        persist(status='completed' if code==0 else 'failed',exit_code=code,finished_at=now(),elapsed_seconds=round(time.monotonic()-clock,3))
        return code
    except BaseException as error:
        if process is not None and process.poll() is None:
            os.killpg(process.pid,signal.SIGTERM)
            try:process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);process.wait()
        persist(status='failed',exit_code=process.returncode if process else None,error_type=type(error).__name__,finished_at=now(),elapsed_seconds=round(time.monotonic()-clock,3))
        raise
    finally:
        for sig,handler in previous.items():signal.signal(sig,handler)


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--audit',type=Path,required=True)
    parser.add_argument('--catalog-hash',required=True)
    parser.add_argument('--as-of',required=True)
    parser.add_argument('--record',type=Path,required=True)
    args=parser.parse_args(argv)
    issues=preflight(ROOT)
    if issues:raise SystemExit('Mini recovery preflight: '+','.join(issues))
    if not owned_resume(ROOT,STAGED_PATHS):raise SystemExit('Recovery ownership changed')
    if os.getpriority(os.PRIO_PROCESS,0)<15:os.nice(15-os.getpriority(os.PRIO_PROCESS,0))
    os.environ.update(RADAR_WEEKLY_RESOURCE_GUARD='1',V3_PYTHON=sys.executable)
    lock_path=ROOT/'.research/weekly-v3/recovery-supervisor.lock'
    with lock_path.open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        command=[sys.executable,'-u',str(ROOT/'scripts/run_weekly_v3.py'),'--publish','--data-only','--resume-owned',
                 '--resume-collected',str(args.audit),'--resume-ingested-hash',args.catalog_hash,'--resume-exported','--as-of',args.as_of]
        return run_supervised(command,ROOT,args.record)


if __name__=='__main__':raise SystemExit(main())
