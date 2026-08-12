"""E8 final gate: run MsgStack (src/attack_e8.py) against LM Studio models.

Mirrors e7_final_gate but imports attack_e8. Verifies:
1. The raw/s screen picks stack3/duo on gemma and single on gpt-oss.
2. Full replay of EVERY returned candidate in fresh envs gives the projected
   raw (34-50 per gemma finding vs 18 singles).

Usage: PYTHONPATH=data;src;scripts python scripts/e8_final_gate.py --budget 240
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

from aicomp_sdk.attacks.contracts import AttackRunConfig  # noqa: E402
from aicomp_sdk.core.cells import cell_signature  # noqa: E402
from aicomp_sdk.core.env.sandbox import SandboxEnv  # noqa: E402
from aicomp_sdk.core.predicates import eval_predicates  # noqa: E402
from aicomp_sdk.guardrails.optimal import Guardrail as Optimal  # noqa: E402
from aicomp_sdk.scoring import score_attack, score_attack_raw  # noqa: E402

import attack_e8 as attack_mod  # noqa: E402

FIXTURES = ROOT / "data" / "aicomp_sdk" / "fixtures"


def lmstudio_models() -> list[str]:
    with urllib.request.urlopen("http://127.0.0.1:1234/v1/models", timeout=5) as r:
        data = json.loads(r.read().decode("utf-8"))
    return [m.get("id", "") for m in data.get("data", [])]


def replay_score(env: SandboxEnv, candidates, hops: int = 8) -> tuple[int, int, float, float, list]:
    findings = []
    fired = 0
    t0 = time.monotonic()
    for cand in candidates:
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
            fired += 1
        except Exception as exc:  # noqa: BLE001
            print(f"  replay exc: {type(exc).__name__}: {exc}", flush=True)
    elapsed = time.monotonic() - t0
    raw = score_attack_raw(findings)
    norm = score_attack(findings)
    return fired, len(findings), raw, norm, findings


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=float, default=240.0)
    ap.add_argument("--models", default="gpt-oss-20b,gemma-4-26b")
    ap.add_argument("--hops", type=int, default=8)
    args = ap.parse_args()

    available = lmstudio_models()
    print("LM Studio:", available, flush=True)
    models = [m.strip() for m in args.models.split(",") if m.strip() in available]

    report: dict = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "budget": args.budget, "models": {}}

    for model in models:
        print(f"\n==== {model} ====", flush=True)
        from openai_compat_blue_agent import make_lmstudio

        agent = make_lmstudio(model)
        env = SandboxEnv(seed=11, fixtures_dir=FIXTURES, agent=agent, guardrail=Optimal())
        attack = attack_mod.AttackAlgorithm()
        cfg = AttackRunConfig(time_budget_s=args.budget, max_tool_hops=args.hops)

        started = time.monotonic()
        candidates = attack.run(env, cfg)
        run_s = time.monotonic() - started
        msgs = [c.user_messages for c in candidates[:3]]
        lens = {len(c.user_messages) for c in candidates}
        print(f"run() returned {len(candidates)} candidates in {run_s:.1f}s "
              f"msg_lens={sorted(lens)} sample={msgs}", flush=True)

        # Full replay of every returned candidate in FRESH envs (host semantics).
        replay_env = SandboxEnv(seed=12, fixtures_dir=FIXTURES, agent=agent, guardrail=Optimal())
        fired, n_findings, raw, norm, findings = replay_score(replay_env, candidates, hops=args.hops)
        replay_s = time.monotonic() - started - run_s
        print(f"replay: fired={fired}/{len(candidates)} findings={n_findings} "
              f"raw={raw:.0f} normalized={norm:.1f} replay_s={replay_s:.1f}s", flush=True)
        report["models"][model] = {
            "returned": len(candidates),
            "msg_lens": sorted(lens),
            "sample": msgs,
            "run_s": round(run_s, 1),
            "fired": fired,
            "findings": n_findings,
            "raw": raw,
            "normalized": round(norm, 1),
            "replay_s": round(replay_s, 1),
        }

    out = ROOT / "results" / "e8_final_gate.json"
    out.write_text(json.dumps(report, indent=2))
    print(f"\nwrote {out}", flush=True)


if __name__ == "__main__":
    main()