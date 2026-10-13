"""Mini-only data-only weekly entry; existing push workflow owns publication."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import socket
from datetime import datetime,timezone
from weekly_runtime import resource_reason

ROOT=Path(__file__).resolve().parents[1]
VERIFIED_MINI={}

def preflight(root=ROOT,*,verify_hardware=False):
    issues=[]
    if sys.platform!='darwin':
        issues.append('requires_mac_mini')
    else:
        identity=root/'.research/weekly-v3/mini-host.json'
        if identity.exists() and not verify_hardware:
            binding=json.loads(identity.read_text())
            if binding.get('hostname')!=socket.gethostname() or not binding.get('model','').startswith('Macmini'):
                issues.append('mini_host_identity_mismatch')
        else:
            try:
                hardware=json.loads(subprocess.check_output(['/usr/sbin/system_profiler','SPHardwareDataType','-json'],text=True,timeout=15))
                rows=hardware.get('SPHardwareDataType',[])
                model=next((r['machine_model'] for r in rows if r.get('machine_name')=='Mac mini' and r.get('machine_model','').startswith('Macmini')),None)
                if not model:issues.append('unverified_mini_hardware')
                else:VERIFIED_MINI.update(hostname=socket.gethostname(),model=model,verified_at=datetime.now(timezone.utc).isoformat())
            except (OSError,ValueError,subprocess.SubprocessError):
                issues.append('hardware_probe_unavailable')
    if sys.version_info<(3,12): issues.append('requires_python_3_12')
    if not shutil.which('node') or not shutil.which('npm'): issues.append('node_and_npm_required')
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=root,text=True).strip()
    if branch!='main': issues.append('requires_dedicated_main_checkout')
    return issues

def save_host_binding(root):
    if VERIFIED_MINI.get('hostname')!=socket.gethostname() or not VERIFIED_MINI.get('model','').startswith('Macmini'):
        raise RuntimeError('Mini hardware must be verified in this installer process')
    path=root/'.research/weekly-v3/mini-host.json';path.parent.mkdir(parents=True,exist_ok=True)
    pending=path.with_suffix('.tmp');pending.write_text(json.dumps(VERIFIED_MINI));pending.replace(path)


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
    os.environ['V3_PYTHON']=sys.executable
    why=resource_reason()
    if why:
        print(json.dumps({'status':'paused_resource_pressure','reason':why}),flush=True)
        return 75
    if os.getpriority(os.PRIO_PROCESS,0)<15: os.nice(15-os.getpriority(os.PRIO_PROCESS,0))
    # No model or notification config is loaded on this host.
    return subprocess.call([sys.executable,str(ROOT/'scripts/run_weekly_v3.py'),
                            '--publish','--data-only','--resume-owned'],cwd=ROOT,env=dict(os.environ))

if __name__=='__main__':raise SystemExit(main())
