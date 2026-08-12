"""Apply a configs/variants.json preset onto src/attack.py module constants.

Writes results/variants/<name>/attack.py ready for packaging/submit.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "attack.py"
VARIANTS = ROOT / "configs" / "variants.json"
OUT_ROOT = ROOT / "results" / "variants"

# Map JSON keys -> Python assignment names in attack.py
KEY_MAP = {
    "MARGIN_S": "MARGIN_S",
    "FILL_BUDGET_FRAC": "FILL_BUDGET_FRAC",
    "REPLAY_SAFE_FRAC": "REPLAY_SAFE_FRAC",
    "PROBE_HOPS": "PROBE_HOPS",
    "REPLAY_COST_COEF": "REPLAY_COST_COEF",
    "SLOW_MULTIPOST_N": "SLOW_MULTIPOST_N",
    "SPLIT_BY_LATENCY": "SPLIT_BY_LATENCY",
    "SPLIT_THRESHOLD_S": "SPLIT_THRESHOLD_S",
    "FALLBACK_N": "FALLBACK_N",
    "DIVERSITY_BUDGET_FRAC": "DIVERSITY_BUDGET_FRAC",
}


def _fmt(value: object) -> str:
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        return str(value)
    raise TypeError(type(value))


def apply_variant(source: str, preset: dict) -> str:
    text = source
    for key, py_name in KEY_MAP.items():
        if key not in preset:
            continue
        val = _fmt(preset[key])
        # Match: NAME: Final[...] = <value>
        pattern = rf"^({re.escape(py_name)}:\s*Final\[[^\]]+\]\s*=\s*).+$"
        text, n = re.subn(pattern, rf"\g<1>{val}", text, count=1, flags=re.M)
        if n != 1:
            # Fallback simpler assignment form
            pattern2 = rf"^({re.escape(py_name)}\s*=\s*).+$"
            text, n2 = re.subn(pattern2, rf"\g<1>{val}", text, count=1, flags=re.M)
            if n2 != 1:
                raise RuntimeError(f"Could not patch constant {py_name}")

    if preset.get("_force_frame_template"):
        # Point TEMPLATE at FRAME_TEMPLATE body by replacing TEMPLATE string constant.
        # Safer: set SPLIT off and rewrite TEMPLATE = FRAME content.
        frame_match = re.search(
            r'^FRAME_TEMPLATE:\s*Final\[str\]\s*=\s*\((.*?)\)\s*$',
            text,
            flags=re.M | re.S,
        )
        if frame_match:
            text = re.sub(
                r'^TEMPLATE:\s*Final\[str\]\s*=\s*\((.*?)\)\s*$',
                f"TEMPLATE: Final[str] = ({frame_match.group(1)})",
                text,
                count=1,
                flags=re.M | re.S,
            )
    return text


def main() -> None:
    name = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    data = json.loads(VARIANTS.read_text(encoding="utf-8"))
    if name not in data["variants"]:
        raise SystemExit(f"Unknown variant {name}. Choose from: {list(data['variants'])}")
    preset = data["variants"][name]
    src = SRC.read_text(encoding="utf-8")
    out_text = apply_variant(src, preset)
    out_dir = OUT_ROOT / name
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "attack.py"
    out_path.write_text(out_text, encoding="utf-8")
    (out_dir / "preset.json").write_text(json.dumps(preset, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
