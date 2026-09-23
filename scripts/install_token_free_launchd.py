#!/usr/bin/env python3
"""Install the private token-free research batch as a macOS LaunchAgent."""
from __future__ import annotations

import argparse
import json
import os
import plistlib
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LABEL = "org.joen.embodied-ai-radar.token-free-research"
INTERVAL_SECONDS = 5 * 60


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", action="store_true", help="Write and load the LaunchAgent")
    args = parser.parse_args(argv)
    if sys.platform != "darwin":
        parser.error("This installer requires macOS")

    python = ROOT / ".venv/bin/python"
    if not python.is_file():
        parser.error("Create .venv and install requirements-v3.txt first")
    logs = ROOT / "logs"
    target = Path.home() / "Library/LaunchAgents" / f"{LABEL}.plist"
    plist = {
        "Label": LABEL,
        "ProgramArguments": [str(python), str(ROOT / "scripts/run_token_free_scheduled.py")],
        "WorkingDirectory": str(ROOT),
        "StartInterval": INTERVAL_SECONDS,
        "RunAtLoad": True,
        "ProcessType": "Background",
        "EnvironmentVariables": {"PATH": "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"},
        "StandardOutPath": str(logs / "token-free-research.log"),
        "StandardErrorPath": str(logs / "token-free-research.error.log"),
    }
    if not args.install:
        print(json.dumps({"mode": "dry_run", "target": str(target), "plist": plist},
                         ensure_ascii=False, indent=2))
        return 0

    logs.mkdir(mode=0o700, exist_ok=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = plistlib.dumps(plist, fmt=plistlib.FMT_XML)
    domain = f"gui/{os.getuid()}"
    service = f"{domain}/{LABEL}"
    previous = target.read_bytes() if target.exists() else None
    with tempfile.NamedTemporaryFile(dir=target.parent, prefix=LABEL + ".",
                                     suffix=".plist", delete=False) as stream:
        stream.write(payload)
        candidate = Path(stream.name)
    candidate.chmod(0o600)
    try:
        subprocess.run(["plutil", "-lint", str(candidate)], check=True)
        loaded = subprocess.run(["launchctl", "print", service], stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL).returncode == 0
        if previous is not None and previous != payload:
            target.with_suffix(".plist.bak").write_bytes(previous)
        if loaded:
            subprocess.run(["launchctl", "bootout", service], check=True)
        candidate.replace(target)
        try:
            subprocess.run(["launchctl", "bootstrap", domain, str(target)], check=True)
        except subprocess.CalledProcessError:
            if previous is None:
                target.unlink(missing_ok=True)
            else:
                target.write_bytes(previous)
                target.chmod(0o600)
            if loaded and previous is not None:
                subprocess.run(["launchctl", "bootstrap", domain, str(target)], check=True)
            raise
    finally:
        candidate.unlink(missing_ok=True)
    print(json.dumps({"status": "installed", "service": service,
                      "interval_seconds": INTERVAL_SECONDS, "target": str(target)},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
