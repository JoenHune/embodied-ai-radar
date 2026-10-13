"""Mini-only data-only weekly entry; existing push workflow owns publication."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from weekly_runtime import resource_reason

ROOT=Path(__file__).resolve().parents[1]

def preflight(root=ROOT):
    issues=[]
    if sys.platform!='darwin':
        issues.append('requires_mac_mini')
    else:
        hardware=json.loads(subprocess.check_output(['/usr/sbin/system_profiler','SPHardwareDataType','-json'],text=True,timeout=15))
        rows=hardware.get('SPHardwareDataType',[])
        if not any(r.get('machine_name')=='Mac mini' and r.get('machine_model','').startswith('Macmini') for r in rows): issues.append('unverified_mini_hardware')
    if sys.version_info<(3,12): issues.append('requires_python_3_12')
    if not shutil.which('node') or not shutil.which('npm'): issues.append('node_and_npm_required')
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=root,text=True).strip()
    if branch!='main': issues.append('requires_dedicated_main_checkout')
    return issues

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',action='store_true')
    args=parser.parse_args(argv)
    issues=preflight()
    if not args.run:
        print(json.dumps({'mode':'dry_run','issues':issues,'data_only':True,
                          'schedule':'Monday 04:00 Asia/Shanghai',
                          'publication':'existing main push Pages/Feishu workflow; no direct messages'}))
        return 0
    if issues: raise SystemExit('Mini weekly preflight: '+','.join(issues))
    os.environ['RADAR_WEEKLY_RESOURCE_GUARD']='1'
    why=resource_reason()
    if why:
        print(json.dumps({'status':'paused_resource_pressure','reason':why}),flush=True)
        return 75
    if os.getpriority(os.PRIO_PROCESS,0)<15: os.nice(15-os.getpriority(os.PRIO_PROCESS,0))
    # No model or notification config is loaded on this host.
    return subprocess.call([sys.executable,str(ROOT/'scripts/run_weekly_v3.py'),
                            '--publish','--data-only','--resume-owned'],cwd=ROOT,env=dict(os.environ))

if __name__=='__main__':raise SystemExit(main())
