"""Detach-launch scripts/monitor.py with output to results/monitor_live.txt."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
out = (ROOT / "results" / "monitor_live.txt").open("w", encoding="utf-8")
err = (ROOT / "results" / "monitor_live_err.txt").open("w", encoding="utf-8")
subprocess.Popen(
    [sys.executable, str(ROOT / "scripts" / "monitor.py"), "--minutes", "300", "--interval-s", "300"],
    stdout=out,
    stderr=err,
    cwd=str(ROOT),
)
print("monitor launched")
