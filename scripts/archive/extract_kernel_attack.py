"""Extract attack.py-like source from a pulled Kaggle notebook."""

from __future__ import annotations

import base64
import json
import re
import sys
from pathlib import Path


def main() -> None:
    folder = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else folder / "extracted_attack.py"
    nbs = list(folder.glob("*.ipynb"))
    if not nbs:
        raise SystemExit(f"No notebook in {folder}")
    nb = json.loads(nbs[0].read_text(encoding="utf-8"))
    for cell in nb.get("cells", []):
        src = "".join(cell.get("source", []))
        if "%%writefile" in src and "attack.py" in src.split("\n", 1)[0]:
            body = src.split("\n", 1)[1] if "\n" in src else ""
            out.write_text(body, encoding="utf-8")
            print(f"writefile -> {out} ({len(body)} bytes)")
            return
        m = re.search(r'ATTACK_PY_B64\s*=\s*"""(.*?)"""', src, re.S)
        if m:
            code = base64.b64decode(m.group(1)).decode("utf-8")
            out.write_text(code, encoding="utf-8")
            print(f"b64 -> {out} ({len(code)} bytes)")
            return
        if "class AttackAlgorithm" in src and "def run" in src and len(src) > 500:
            # maybe triple-quoted assignment
            m2 = re.search(r"src\s*=\s*'''\\?(.*?)'''", src, re.S)
            if m2:
                code = m2.group(1)
                out.write_text(code, encoding="utf-8")
                print(f"triple -> {out} ({len(code)} bytes)")
                return
            out.write_text(src, encoding="utf-8")
            print(f"cell -> {out} ({len(src)} bytes)")
            return
    raise SystemExit("No attack source found")


if __name__ == "__main__":
    main()
