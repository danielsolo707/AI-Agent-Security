"""Auto-submit watcher: poll kernel status; submit when COMPLETE.

Usage: python scripts/auto_submit.py <version> "<message>" [--kernel <slug>]
Logs to results/auto_submit.log. Polls every 5 min for up to 16 h.
Uses the file token (~/.kaggle/access_token) via KAGGLE_API_TOKEN.
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
DEFAULT_KERNEL = "danielsolo1770/agent-security-phase0"
LOG = ROOT / "results" / "auto_submit.log"


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


def run(args: list[str], timeout: int = 180) -> tuple[int, str]:
    env = dict(os.environ)
    env["KAGGLE_API_TOKEN"] = token()
    env["PYTHONUTF8"] = "1"
    p = subprocess.run(
        args, capture_output=True, text=True, encoding="utf-8",
        errors="replace", env=env, timeout=timeout,
    )
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def kernel_status(kernel: str) -> str:
    for _ in range(4):
        try:
            rc, out = run(["kaggle", "kernels", "status", kernel])
            text = (out or "").strip()
            if "COMPLETE" in text:
                return "COMPLETE"
            if "ERROR" in text:
                return "ERROR"
            if "CANCEL" in text:
                return "CANCEL"
            return "RUNNING"
        except Exception as exc:
            log(f"status error: {exc!r}")
            time.sleep(30)
    return "UNKNOWN"


def submit(version: int, message: str, kernel: str) -> bool:
    attempts = [
        ["kaggle", "competitions", "submit", "-c", COMP, "-f", "submission.csv",
         "-k", kernel, "-v", str(version), "-m", message],
        ["kaggle", "competitions", "submit", "-f", "submission.csv",
         "-k", kernel, "-v", str(version), "-m", message],
        ["kaggle", "competitions", "submit", "-c", COMP, "-f", "submission.csv",
         "-k", kernel, "-v", str(version)],
    ]
    for i, args in enumerate(attempts):
        try:
            rc, out = run(args, timeout=300)
        except Exception as exc:
            log(f"submit attempt {i} exc: {exc!r}")
            continue
        log(f"submit attempt {i} rc={rc}: {out.strip()[:600]}")
        if rc == 0 and (
            "Successfully submitted" in out
            or "fully submitted" in out
            or "submissions remaining" in out
        ):
            return True
        time.sleep(20)
    return False


def main() -> int:
    version = int(sys.argv[1])
    message = sys.argv[2] if len(sys.argv) > 2 else "auto submit"
    kernel = DEFAULT_KERNEL
    if "--kernel" in sys.argv:
        kernel = sys.argv[sys.argv.index("--kernel") + 1]
    log(f"auto_submit start: kernel={kernel} v{version} msg={message!r}")
    deadline = time.monotonic() + 16 * 3600
    while time.monotonic() < deadline:
        st = kernel_status(kernel)
        if st == "COMPLETE":
            log("kernel COMPLETE — submitting")
            time.sleep(60)
            ok = submit(version, message, kernel)
            log("SUBMIT_OK" if ok else "SUBMIT_FAILED")
            return 0 if ok else 3
        if st in ("ERROR", "CANCEL"):
            log(f"kernel {st} — aborting (no submit)")
            return 4
        time.sleep(300)
    log("timed out waiting for kernel")
    return 5


if __name__ == "__main__":
    sys.exit(main())
