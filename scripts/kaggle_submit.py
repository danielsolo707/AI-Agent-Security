"""Build, push, and submit the competition notebook (CPU only)."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KERNEL_DIR = ROOT / "notebooks" / "submit_kernel"
KERNEL = "danielsolo1770/agent-security-phase0"
COMP = "ai-agent-security-multi-step-tool-attacks"


def run(cmd: list[str]) -> str:
    print("+", " ".join(cmd))
    p = subprocess.run(cmd, capture_output=True, text=True)
    out = (p.stdout or "") + (p.stderr or "")
    print(out)
    if p.returncode != 0:
        raise SystemExit(f"Command failed ({p.returncode}): {cmd}")
    return out


def main() -> None:
    message = sys.argv[1] if len(sys.argv) > 1 else "auto submit"
    run([sys.executable, str(ROOT / "scripts" / "build_kaggle_kernel.py")])
    push_out = run(["kaggle", "kernels", "push", "-p", str(KERNEL_DIR)])
    # Parse version from "Kernel version N successfully pushed"
    version = None
    for line in push_out.splitlines():
        if "Kernel version" in line and "pushed" in line:
            for tok in line.split():
                if tok.isdigit():
                    version = int(tok)
                    break
    if version is None:
        version = 1
        print("WARNING: could not parse version; defaulting to 1")

    # Wait for kernel COMPLETE
    for _ in range(40):
        status = run(["kaggle", "kernels", "status", KERNEL])
        if "COMPLETE" in status:
            break
        if "ERROR" in status or "CANCEL" in status:
            raise SystemExit(f"Kernel failed: {status}")
        time.sleep(15)
    else:
        raise SystemExit("Timed out waiting for kernel")

    # Submit via Python API for clearer errors
    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()
    resp = api.competition_submit_code(
        file_name="submission.csv",
        message=message,
        competition=COMP,
        kernel=KERNEL,
        kernel_version=version,
        quiet=False,
    )
    print("Submitted:", resp)
    run(["kaggle", "competitions", "submissions", "-c", COMP])


if __name__ == "__main__":
    main()
