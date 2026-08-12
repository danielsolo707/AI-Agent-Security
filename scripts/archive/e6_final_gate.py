"""E6 final gate: run the real AttackAlgorithm against LM Studio target models.

For each of gpt-oss-20b / gemma-4-26b:
  1. Build SandboxEnv(agent=lmstudio(model), guardrail=Optimal) — same stack as host.
  2. Run AttackAlgorithm.run() with a short budget (fill portion exercised).
  3. Replay every returned candidate in fresh envs; count EXFIL filters.
  4. Print selected template, returned N, live-fill rate, replay fire rate.

Usage: PYTHONPATH=data;src;scripts python scripts/e6_final_gate.py --budget 150
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from aicomp_sdk.agents import build_agent  # noqa: E402
from aicomp_sdk.attacks.contracts import AttackRunConfig  # noqa: E402
from aicomp_sdk.core.cells import cell_signature  # noqa: E402
from aicomp_sdk.core.env.sandbox import SandboxEnv  # noqa: E402
from aicomp_sdk.core.predicates import eval_predicates  # noqa: E402
from aicomp_sdk.guardrails.optimal import Guardrail as Optimal  # noqa: E402
from aicomp_sdk.scoring import score_attack, score_attack_raw  # noqa: E402

import attack as attack_mod  # noqa: E402

FIXTURES = ROOT / "data" / "aicomp_sdk" / "fixtures"


def lmstudio_models() -> list[str]:
    with urllib.request.urlopen("http://127.0.0.1:1234/v1/models", timeout=5) as r:
        data = json.loads(r.read().decode("utf-8"))
    return [m.get("id", "") for m in data.get("data", [])]


def replay_score(env: SandboxEnv, candidates, hops: int = 8, sample: int | None = 40) -> tuple[int, float, float]:
    findings = []
    pool = candidates[:sample] if sample else candidates
    for cand in pool:
        env.reset()
        try:
            for msg in cand.user_messages:
                env.interact(msg, max_tool_hops=hops)
            tr = env.export_trace_dict()
            preds = eval_predicates(tr)
            if not preds:
                continue
            sig = cell_signature(
                tr.get("tool_events", []),
                egress_data=tr.get("egress", []),
                user_messages=tr.get("user_messages", []),
            )
            findings.append({"predicates": preds, "cell_signature": sig, "score_cell_signature": sig})
        except Exception as exc:
            print("  replay_err", type(exc).__name__, str(exc)[:80])
    raw = score_attack_raw(findings)
    norm = score_attack(findings)
    return len(findings), raw, norm


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=float, default=90.0)
    ap.add_argument("--models", default="gpt-oss-20b,gemma-4-26b")
    ap.add_argument("--sample", type=int, default=25)
    args = ap.parse_args()

    available = lmstudio_models()
    print("LM Studio:", available, flush=True)
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    report = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "budget": args.budget, "models": {}}

    for model in models:
        if model not in available:
            print(f"SKIP {model}", flush=True)
            continue
        print(f"\n==== {model} ====", flush=True)
        from openai_compat_blue_agent import make_lmstudio
        agent = make_lmstudio(model)
        env = SandboxEnv(seed=11, fixtures_dir=FIXTURES, agent=agent, guardrail=Optimal())
        attacker = attack_mod.AttackAlgorithm({})
        t0 = time.time()
        candidates = attacker.run(
            env,
            AttackRunConfig(time_budget_s=args.budget, max_steps=10 ** 9, max_tool_hops=8),
        )
        gen_s = time.time() - t0
        print(f"run()={gen_s:.1f}s returned={len(candidates)}", flush=True)

        n_find, raw, norm = replay_score(env, candidates, sample=args.sample)
        print(f"replay findings={n_find}/{min(len(candidates), args.sample)} raw={raw:.0f} norm={norm:.3f}", flush=True)
        report["models"][model] = {
            "returned": len(candidates),
            "replay_findings": n_find,
            "raw": raw,
            "normalized": norm,
            "gen_s": gen_s,
        }

    OUT = ROOT / "results" / "e6_final_gate.json"
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("\nwrote", OUT)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()