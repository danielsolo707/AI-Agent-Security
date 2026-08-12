"""FINAL GATE ONLY: fire-rate + short live-fill on gpt-oss-20b then gemma-4-26b.

Requires LM Studio server with models available at http://127.0.0.1:1234/v1
"""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = ("gpt-oss-20b", "gemma-4-26b")
OUT = ROOT / "results" / "final_lmstudio_gate.json"


def models_available() -> list[str]:
    try:
        with urllib.request.urlopen("http://127.0.0.1:1234/v1/models", timeout=5) as r:
            data = json.loads(r.read().decode("utf-8"))
        return [m.get("id", "") for m in data.get("data", [])]
    except Exception as exc:
        raise SystemExit(f"LM Studio not reachable: {exc}") from exc


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.check_call(cmd, cwd=str(ROOT))


def main() -> None:
    available = models_available()
    print("lmstudio models:", available)
    py = sys.executable
    env_prefix = {
        "PYTHONPATH": f"{ROOT / 'data'};{ROOT / 'src'};{ROOT / 'scripts'}",
    }
    import os

    os.environ.update(env_prefix)

    reports = []
    for model in MODELS:
        if model not in available:
            print(f"SKIP {model} (not loaded/listed)")
            reports.append({"model": model, "skipped": True})
            continue
        fire_out = ROOT / "results" / f"final_fire_{model}.json"
        fill_out = ROOT / "results" / f"final_fill_{model}.json"
        run(
            [
                py,
                str(ROOT / "scripts" / "run_fire_rate.py"),
                "--backend",
                "lmstudio",
                "--model",
                model,
                "--n",
                "6",
                "--out",
                str(fire_out),
            ]
        )
        run(
            [
                py,
                str(ROOT / "scripts" / "run_live_fill.py"),
                "--backend",
                "lmstudio",
                "--model",
                model,
                "--budget-s",
                "90",
                "--hard-n-cap",
                "20",
                "--out",
                str(fill_out),
            ]
        )
        fire = json.loads(fire_out.read_text(encoding="utf-8"))
        fill = json.loads(fill_out.read_text(encoding="utf-8"))
        verbose = next((r for r in fire if r.get("template") == "verbose"), {})
        reports.append(
            {
                "model": model,
                "verbose_fire_rate": verbose.get("fire_rate"),
                "verbose_exfil_rate": verbose.get("exfil_rate"),
                "verbose_mean_lat": verbose.get("mean_latency_s"),
                "fill_candidates": fill.get("candidates"),
                "fill_proj_9000": fill.get("proj_9000"),
                "pass_fire": (verbose.get("fire_rate") or 0) >= 0.7,
                "pass_fill": (fill.get("candidates") or 0) > 0,
            }
        )

    OUT.write_text(json.dumps(reports, indent=2), encoding="utf-8")
    print(json.dumps(reports, indent=2))
    print("wrote", OUT)
    failed = [r for r in reports if not r.get("skipped") and not (r.get("pass_fire") and r.get("pass_fill"))]
    if failed:
        print("FINAL GATE: FAIL", [r["model"] for r in failed])
        raise SystemExit(2)
    print("FINAL GATE: PASS")


if __name__ == "__main__":
    main()
