"""Push the submit kernel via kaggle CLI with explicit token auth.

Reads ~/.kaggle/access_token (fallback: KAGGLE_MCP_TOKEN env) and sets
KAGGLE_API_TOKEN for the subprocess. Prints the pushed version number.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KERNEL_DIR = ROOT / "notebooks" / "submit_kernel"


def _kernel_dir() -> Path:
    if "--dir" in sys.argv:
        return Path(sys.argv[sys.argv.index("--dir") + 1])
    return KERNEL_DIR


def _candidates() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    mcp = (os.environ.get("KAGGLE_MCP_TOKEN") or "").strip()
    if mcp:
        out.append(("mcp", mcp))
    tok_file = Path.home() / ".kaggle" / "access_token"
    if tok_file.exists():
        t = tok_file.read_text(encoding="utf-8").strip()
        if t:
            out.append(("file", t))
    return out


def main() -> int:
    attempts = _candidates()
    if not attempts:
        print("NO_TOKEN: no access_token file and no KAGGLE_MCP_TOKEN")
        return 2
    kdir = _kernel_dir()
    last_out = ""
    for label, tok in attempts:
        env = dict(os.environ)
        env["KAGGLE_API_TOKEN"] = tok
        env["PYTHONUTF8"] = "1"
        print(f"--- push attempt via {label} token (len={len(tok)}) dir={kdir} ---")
        p = subprocess.run(
            ["kaggle", "kernels", "push", "-p", str(kdir)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=300,
        )
        out = (p.stdout or "") + (p.stderr or "")
        last_out = out
        print(out)
        if p.returncode == 0:
            version = None
            for line in out.splitlines():
                if "Kernel version" in line and "pushed" in line:
                    for tok_ in line.split():
                        if tok_.isdigit():
                            version = int(tok_)
                            break
            print("PUSHED_VERSION:", version)
            return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
