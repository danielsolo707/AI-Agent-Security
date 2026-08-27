"""Generate validator v11: golden (src/attack.py) vs E23 (src/attack_e23_stackturn.py).

Rewrites the GOLDEN_GZ64 / CAND_GZ64 payload blocks inside
notebooks/local_validation/local_validation.py, then compile-checks the script.
"""

from __future__ import annotations

import base64
import gzip
import re
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "notebooks" / "local_validation" / "local_validation.py"


def gz64(path: Path) -> str:
    return base64.b64encode(gzip.compress(path.read_bytes(), 9)).decode("ascii")


def chunk(s: str, n: int = 96) -> str:
    return "\n".join('    "%s"' % x for x in textwrap.wrap(s, n))


def main() -> None:
    g = gz64(ROOT / "src" / "attack.py")
    c = gz64(ROOT / "src" / "attack_e23_stackturn.py")
    src = NB.read_text(encoding="utf-8")
    src, n1 = re.subn(
        r"GOLDEN_GZ64 = \(\n(?:    \"[^\"]*\"\n)+\)",
        "GOLDEN_GZ64 = (\n" + chunk(g) + "\n)",
        src,
        count=1,
    )
    src, n2 = re.subn(
        r"CAND_GZ64 = \(\n(?:    \"[^\"]*\"\n)+\)",
        "CAND_GZ64 = (\n" + chunk(c) + "\n)",
        src,
        count=1,
    )
    if n1 != 1 or n2 != 1:
        raise SystemExit(f"payload block replace failed: golden={n1} cand={n2}")
    NB.write_text(src, encoding="utf-8")
    compile(src, str(NB), "exec")
    print(f"validator v11 written: {NB} ({len(src)} chars)")
    print(f"golden gz64 {len(g)} chars, e23 gz64 {len(c)} chars")


if __name__ == "__main__":
    main()
