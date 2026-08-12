"""Refresh MORNING_REPORT stats from mining_results.json (run when you wake)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MINING = ROOT / "results" / "mining_results.json"
DEPUTY = ROOT / "results" / "confused_deputy_probe.json"
OUT = ROOT / "results" / "MORNING_SUMMARY.txt"


def main() -> None:
    lines = []
    lines.append("=== MORNING SUMMARY ===\n")

    lines.append("## Submit files")
    lines.append("  B: src/attack_submit_b.py  (N=900, safe=0.95) → est ~81")
    lines.append("  C: src/attack_submit_c.py  (N=1050, safe=0.93) → est ~94.5")
    lines.append("  backup: results/submits/attack_backup_750.py (N=750, 67.5)")
    lines.append("")

    if MINING.is_file():
        d = json.loads(MINING.read_text(encoding="utf-8"))
        lines.append("## Mining (gpt-oss frame)")
        for k in (
            "attempts",
            "fires",
            "errors",
            "fire_rate_excluding_errors",
            "mean_latency_s",
            "p50_latency_s",
            "p95_latency_s",
            "miss_count",
            "end_exclusive",
        ):
            if k in d:
                lines.append(f"  {k}: {d[k]}")
        # dead zones: consecutive misses
        recs = d.get("records") or []
        miss_runs = []
        run = 0
        for r in recs:
            if not r.get("fired"):
                run += 1
            else:
                if run:
                    miss_runs.append(run)
                run = 0
        if run:
            miss_runs.append(run)
        lines.append(f"  max_consecutive_misses: {max(miss_runs) if miss_runs else 0}")
        lines.append("")
    else:
        lines.append("## Mining: results/mining_results.json not found yet\n")

    if DEPUTY.is_file():
        d = json.loads(DEPUTY.read_text(encoding="utf-8"))
        lines.append("## Confused deputy probe")
        lines.append(f"  hits: {d.get('hits')}/{d.get('n')} rate={d.get('hit_rate')}")
        lines.append("")
    else:
        lines.append("## Confused deputy: not run (run overnight_confused_deputy.py after mining)\n")

    lines.append("## Recommended next submit")
    lines.append("  → Submit B first (N=900). Only go to C if B has no timeout.")
    lines.append("")

    text = "\n".join(lines)
    OUT.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
