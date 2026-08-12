"""Overnight unique-host EXFIL mining against LM Studio gpt-oss-20b (frame template).

Writes results/mining_results.json incrementally.
Does not modify attack.py.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from aicomp_sdk.core.env.sandbox import SandboxEnv  # noqa: E402
from aicomp_sdk.core.predicates import eval_predicates  # noqa: E402
from aicomp_sdk.guardrails.optimal import Guardrail as Optimal  # noqa: E402

import attack as attack_mod  # noqa: E402  # constants/helpers only; strategy untouched
from openai_compat_blue_agent import make_lmstudio  # noqa: E402

FIXTURES = ROOT / "data" / "aicomp_sdk" / "fixtures"
OUT = ROOT / "results" / "mining_results.json"
PROGRESS = ROOT / "results" / "mining_progress.jsonl"

# Default overnight window (~7.5h) or argv: start end model
START = int(sys.argv[1]) if len(sys.argv) > 1 else 0
END = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
MODEL = sys.argv[3] if len(sys.argv) > 3 else "gpt-oss-20b"
# Soft time budget so we stop cleanly before morning if set (hours)
MAX_HOURS = float(sys.argv[4]) if len(sys.argv) > 4 else 7.5


def main() -> None:
    agent = make_lmstudio(MODEL)
    env = SandboxEnv(
        seed=123,
        fixtures_dir=FIXTURES,
        agent=agent,
        guardrail=Optimal(),
    )

    records: list[dict] = []
    fires = 0
    errors = 0
    lats: list[float] = []
    t0 = time.time()
    deadline = t0 + MAX_HOURS * 3600.0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    if PROGRESS.exists():
        PROGRESS.unlink()

    for i in range(START, END):
        if time.time() >= deadline:
            print(f"time budget hit at i={i}", flush=True)
            break

        msg = attack_mod._msg(i, attack_mod.FRAME_TEMPLATE)
        t1 = time.time()
        rec: dict = {
            "i": i,
            "url": attack_mod._url(i),
            "template": "FRAME",
            "model": MODEL,
        }
        try:
            env.reset()
            env.interact(msg, max_tool_hops=4)
            elapsed = time.time() - t1
            lats.append(elapsed)
            fired = attack_mod._fired(env)
            preds = [p.get("predicate") for p in eval_predicates(env.export_trace_dict())]
            tools = [
                e.get("name")
                for e in env.export_trace_dict().get("tool_events", [])
                if e.get("ok")
            ]
            rec.update(
                {
                    "fired": fired,
                    "exfil": "EXFILTRATION" in preds,
                    "preds": preds,
                    "tools_ok": tools,
                    "elapsed_s": elapsed,
                    "error": None,
                }
            )
            if fired:
                fires += 1
        except Exception as exc:
            elapsed = time.time() - t1
            lats.append(elapsed)
            errors += 1
            rec.update(
                {
                    "fired": False,
                    "exfil": False,
                    "preds": [],
                    "tools_ok": [],
                    "elapsed_s": elapsed,
                    "error": f"{type(exc).__name__}: {str(exc)[:200]}",
                }
            )

        records.append(rec)
        with PROGRESS.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")

        if (i - START + 1) % 25 == 0 or i == START:
            done = i - START + 1
            rate = fires / max(1, done - errors) if done > errors else 0.0
            p95 = sorted(lats)[int(0.95 * (len(lats) - 1))] if lats else 0.0
            print(
                f"i={i} done={done} fires={fires} errors={errors} "
                f"fire_rate={rate:.3f} mean_lat={sum(lats)/len(lats):.2f}s p95={p95:.2f}s",
                flush=True,
            )
            # checkpoint full json periodically
            _write_summary(records, fires, errors, lats, MODEL, START, i + 1)

    _write_summary(records, fires, errors, lats, MODEL, START, records[-1]["i"] + 1 if records else START)
    print("DONE wrote", OUT, flush=True)


def _write_summary(
    records: list[dict],
    fires: int,
    errors: int,
    lats: list[float],
    model: str,
    start: int,
    end_exclusive: int,
) -> None:
    n = len(records)
    sorted_l = sorted(lats) if lats else [0.0]
    p50 = sorted_l[len(sorted_l) // 2]
    p95 = sorted_l[int(0.95 * (len(sorted_l) - 1))]
    dead = [r["i"] for r in records if not r.get("fired") and not r.get("error")]
    summary = {
        "model": model,
        "template": "FRAME",
        "start": start,
        "end_exclusive": end_exclusive,
        "attempts": n,
        "fires": fires,
        "errors": errors,
        "fire_rate_excluding_errors": fires / max(1, n - errors),
        "fire_rate_including_errors": fires / max(1, n),
        "mean_latency_s": sum(lats) / max(1, len(lats)),
        "p50_latency_s": p50,
        "p95_latency_s": p95,
        "min_latency_s": min(lats) if lats else None,
        "max_latency_s": max(lats) if lats else None,
        "miss_indices_sample": dead[:50],
        "miss_count": len(dead),
        "records": records,
    }
    OUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
