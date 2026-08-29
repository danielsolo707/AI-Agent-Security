"""Detach-launch the quota watcher and the monitor with redirected output."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

procs = [
    (
        [sys.executable, str(ROOT / "scripts" / "quota_watch.py")],
        ROOT / "results" / "quota_watch_out.txt",
        ROOT / "results" / "quota_watch_err.txt",
    ),
    (
        [sys.executable, str(ROOT / "scripts" / "monitor.py"), "--minutes", "600", "--interval-s", "300"],
        ROOT / "results" / "monitor_live.txt",
        ROOT / "results" / "monitor_live_err.txt",
    ),
]

for args, out, err in procs:
    subprocess.Popen(
        args,
        stdout=open(out, "w", encoding="utf-8"),
        stderr=open(err, "w", encoding="utf-8"),
        cwd=str(ROOT),
    )
    print("launched:", " ".join(args[1:]))
