"""Copy src/attack.py into results/submission/ for Kaggle upload."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "attack.py"
OUT_DIR = ROOT / "results" / "submission"
OUT = OUT_DIR / "attack.py"


def main() -> None:
    if not SRC.is_file():
        raise SystemExit(f"Missing {SRC}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SRC, OUT)
    size = OUT.stat().st_size
    print(f"Wrote {OUT} ({size} bytes)")
    print("Upload this attack.py (or a notebook that writes it to /kaggle/working/attack.py).")


if __name__ == "__main__":
    main()
