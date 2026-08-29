"""Golden T4 re-roll loop: push -> wait COMPLETE -> submit -> repeat.

Adopts an already-running submit-kernel version (default 48), submits it, then
keeps cycling: push a fresh golden T4 version, wait for COMPLETE, submit it.
Stops when the day's submission slots are exhausted (sleeps until UTC midnight
for the reset), when GPU quota drains again, or after --deadline-h hours.
Logs to results/quota_watch.log.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMP = "ai-agent-security-multi-step-tool-attacks"
SUBMIT_KERNEL = "danielsolo1770/agent-security-phase0"
SUBMIT_DIR = ROOT / "notebooks" / "submit_kernel"
LOG = ROOT / "results" / "quota_watch.log"
SUFFIXES = ["v", "w", "x", "y", "z", "aa", "ab", "ac", "ad", "ae", "af", "ag"]


def log(msg: str) -> None:
    line = f"[{datetime.now(timezone.utc).strftime('%m-%d %H:%M:%SZ')}] {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def token() -> str:
    t = (Path.home() / ".kaggle" / "access_token").read_text(encoding="utf-8").strip()
    if not t:
        t = (os.environ.get("KAGGLE_MCP_TOKEN") or "").strip()
    return t


def run(args: list[str], timeout: int = 300) -> tuple[int, str]:
    env = dict(os.environ)
    env["KAGGLE_API_TOKEN"] = token()
    env["PYTHONUTF8"] = "1"
    p = subprocess.run(
        args, capture_output=True, text=True, encoding="utf-8",
        errors="replace", env=env, timeout=timeout,
    )
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def kernel_status(kernel: str) -> str:
    try:
        rc, out = run(["kaggle", "kernels", "status", kernel], timeout=120)
    except Exception as exc:
        log(f"status exc: {exc!r}")
        return "UNKNOWN"
    text = (out or "").strip()
    if "COMPLETE" in text:
        return "COMPLETE"
    if "ERROR" in text:
        return "ERROR"
    if "CANCEL" in text:
        return "CANCEL"
    return "RUNNING"


def push_version() -> int | None:
    """Push golden; return version number, or None if blocked (quota etc.)."""
    try:
        rc, out = run(["kaggle", "kernels", "push", "-p", str(SUBMIT_DIR)])
    except Exception as exc:
        log(f"push exc: {exc!r}")
        return None
    if rc == 0:
        version = None
        for line in out.splitlines():
            if "Kernel version" in line and "pushed" in line:
                for tok_ in line.split():
                    if tok_.isdigit():
                        version = int(tok_)
                        break
        log(f"PUSH OK — version {version}")
        return version
    tail = out.strip().splitlines()[-1] if out.strip() else "(no output)"
    log(f"push blocked: {tail[:160]}")
    return None


def submit(version: int, message: str) -> int:
    """Submit; returns remaining slots (-1 on hard failure)."""
    args = ["kaggle", "competitions", "submit", "-c", COMP, "-f", "submission.csv",
            "-k", SUBMIT_KERNEL, "-v", str(version), "-m", message]
    for i in range(3):
        try:
            rc, out = run(args, timeout=300)
        except Exception as exc:
            log(f"submit attempt {i} exc: {exc!r}")
            time.sleep(30)
            continue
        log(f"submit v{version} attempt {i} rc={rc}: {out.strip()[:300]}")
        if rc == 0 and ("submitted" in out or "remaining" in out):
            remaining = -1
            for tok_ in out.split():
                if tok_.isdigit():
                    remaining = int(tok_)
                    break
            return remaining
        time.sleep(30)
    return -1


def wait_complete(version: int, deadline: float) -> str:
    while time.monotonic() < deadline:
        st = kernel_status(SUBMIT_KERNEL)
        if st in ("COMPLETE", "ERROR", "CANCEL"):
            log(f"v{version} status: {st}")
            return st
        time.sleep(300)
    log(f"v{version} wait timed out")
    return "TIMEOUT"


def main() -> int:
    start_version = int(sys.argv[1]) if len(sys.argv) > 1 else 48
    deadline_hours = float(sys.argv[2]) if len(sys.argv) > 2 else 36.0
    deadline = time.monotonic() + deadline_hours * 3600
    log(f"re-roll loop start: adopt v{start_version}, deadline {deadline_hours:.0f} h")

    version = start_version
    idx = 0
    remaining = None
    while time.monotonic() < deadline:
        name = "E18" + SUFFIXES[idx % len(SUFFIXES)]
        st = wait_complete(version, deadline)
        if st == "COMPLETE":
            remaining = submit(version, f"{name} golden T4 re-roll v{version}")
            if remaining == -1:
                log("submit failed hard — retry cycle")
                time.sleep(600)
                continue
            idx += 1
            log(f"submitted v{version} as {name}; {remaining} slots remaining today")
        elif st in ("ERROR", "CANCEL"):
            log(f"v{version} {st} — skipping submit")
            idx += 1

        if remaining == 0:
            # sleep until next UTC midnight + 10 min for slot reset
            now = datetime.now(timezone.utc)
            nxt = now.replace(hour=0, minute=10, second=0, microsecond=0)
            secs = (nxt.timestamp() + 86400) - now.timestamp()
            log(f"out of slots — sleeping {secs/3600:.1f} h for UTC reset")
            time.sleep(max(60, secs))
            remaining = None

        if time.monotonic() >= deadline:
            break
        # push next golden version (retry on transient blocks)
        pushed = None
        while pushed is None and time.monotonic() < deadline:
            pushed = push_version()
            if pushed is None:
                time.sleep(900)
        if pushed is None:
            break
        version = pushed
    log("re-roll loop end")
    return 0


if __name__ == "__main__":
    sys.exit(main())

