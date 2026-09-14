#!/usr/bin/env python3
"""Preview a Monday 00:00 Asia/Shanghai LaunchAgent; install only with --install."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
LABEL = "org.joen.embodied-ai-radar.v3.weekly"


def build_plist(root: Path, python: str, node: str, npm: str, env_file: Path, *, loggerbot: bool = False) -> dict:
    binary_paths = list(dict.fromkeys([str(Path(python).parent), str(Path(node).parent), str(Path(npm).parent), "/usr/bin", "/bin", "/usr/sbin", "/sbin"]))
    return {
        "Label": LABEL,
        "ProgramArguments": [python, str(root / "scripts/run_weekly_v3.py"), "--publish", "--loggerbot-env-file" if loggerbot else "--env-file", str(env_file)],
        "WorkingDirectory": str(root),
        "StartCalendarInterval": {"Weekday": 1, "Hour": 0, "Minute": 0},
        "EnvironmentVariables": {"PATH": ":".join(binary_paths), "TZ": "Asia/Shanghai", "V3_PYTHON": python},
        "StandardOutPath": str(root / "logs/weekly-v3.log"),
        "StandardErrorPath": str(root / "logs/weekly-v3.error.log"),
        "RunAtLoad": False,
        "ProcessType": "Background",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", action="store_true", help="Write and load the LaunchAgent after all preflight checks")
    parser.add_argument("--dry-run", action="store_true", help="Preview only (default)")
    configuration = parser.add_mutually_exclusive_group()
    configuration.add_argument("--env-file", type=Path, default=Path.home() / ".config/embodied-ai-radar/runtime.env")
    configuration.add_argument("--loggerbot-env-file", type=Path, help="Reference an existing external LoggerBot configuration; only model fields are loaded")
    args = parser.parse_args(argv)
    if args.install and args.dry_run:
        parser.error("--install and --dry-run are mutually exclusive")
    python = str(ROOT / ".venv/bin/python") if (ROOT / ".venv/bin/python").exists() else sys.executable
    node, npm = shutil.which("node"), shutil.which("npm")
    if not node or not npm:
        raise SystemExit("Node.js 24 and npm must be available before installing the schedule.")
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    zone = str(Path("/etc/localtime").resolve())
    issues = []
    if sys.platform != "darwin": issues.append("launchd requires macOS")
    if not zone.endswith("/Asia/Shanghai"): issues.append("macOS system timezone must be Asia/Shanghai; TZ alone does not change calendar triggers")
    if branch != "main": issues.append("the scheduled checkout must be main")
    configuration_file = args.loggerbot_env_file or args.env_file
    if configuration_file.resolve().is_relative_to(ROOT): issues.append("runtime credentials must be outside the repository")
    payload = build_plist(ROOT, python, node, npm, configuration_file.resolve(), loggerbot=bool(args.loggerbot_env_file))
    target = Path.home() / "Library/LaunchAgents" / (LABEL + ".plist")
    if not args.install:
        print(json.dumps({"mode": "dry_run", "schedule": "Monday 00:00 Asia/Shanghai", "target": str(target), "preflight_issues": issues,
                          "llm_configuration_present": configuration_file.exists(), "note": "No plist was written and no job was loaded. Missing LLM settings use the data-only fallback.", "plist": payload}, ensure_ascii=False, indent=2))
        return 0
    if issues:
        raise SystemExit("Cannot install: " + "; ".join(issues))
    target.parent.mkdir(parents=True, exist_ok=True)
    (ROOT / "logs").mkdir(exist_ok=True)
    content = plistlib.dumps(payload, fmt=plistlib.FMT_XML)
    domain = f"gui/{os.getuid()}"
    loaded = subprocess.run(["launchctl", "print", f"{domain}/{LABEL}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    if target.exists() and target.read_bytes() != content:
        shutil.copy2(target, target.with_suffix(".plist.bak"))
    if loaded:
        subprocess.run(["launchctl", "bootout", f"{domain}/{LABEL}"], check=True)
    target.write_bytes(content)
    subprocess.run(["plutil", "-lint", str(target)], check=True)
    subprocess.run(["launchctl", "bootstrap", domain, str(target)], check=True)
    print(json.dumps({"status": "installed", "label": LABEL, "schedule": "Monday 00:00 Asia/Shanghai", "target": str(target)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
