"""E7 final gate: run the ChainStack AttackAlgorithm against LM Studio models.

Same stack as e6_final_gate but imports src/attack_e7.py. Replays EVERY
returned candidate in fresh envs (not a sample) so dturn/triturn scoring is
verified end-to-end: each candidate's raw contribution is its actual finding
score (severity sum over all fired predicates + 2 per unique cell).

Usage: PYTHONPATH=data;src;scripts python scripts/e7_final_gate.py --budget 180
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

import attack_e7 as attack_mod  # noqa: E402

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
        except Exception as exc:
            print("  replay_err", type(exc).__name__, str(exc)[:80])
    raw = score_attack_raw(findings)
    norm = score_attack(findings)
    return len(findings), fired, raw, norm, findings


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=float, default=150.0)
    ap.add_argument("--models", default="gpt-oss-20b,gemma-4-26b")
    ap.add_argument("--max-replay", type=int, default=120)
    ap.add_argument("--screen-reps", type=int, default=0)
    ap.add_argument("--margin-s", type=float, default=0.0)
    args = ap.parse_args()

    engine_cfg: dict = {}
    if args.screen_reps > 0:
        engine_cfg["screen_reps"] = args.screen_reps
        engine_cfg["final_reps"] = max(2, args.screen_reps)
    if args.margin_s > 0:
        engine_cfg["margin_s"] = args.margin_s
        engine_cfg["margin_mult"] = 1.20
    print("engine overrides:", engine_cfg or "(none)", flush=True)

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
        attacker = attack_mod.AttackAlgorithm(engine_cfg)
        t0 = time.time()
        candidates = attacker.run(
            env,
            AttackRunConfig(time_budget_s=args.budget, max_steps=10 ** 9, max_tool_hops=8),
        )
        gen_s = time.time() - t0
        print(f"run()={gen_s:.1f}s returned={len(candidates)}", flush=True)

        pool = candidates[: args.max_replay]
        n_find, fired, raw, norm, findings = replay_score(env, pool)
        n_msg = sum(len(c.user_messages) for c in pool)
        n_exfil = sum(
            sum(1 for p in f["predicates"] if str(p.get("predicate", "")).upper() == "EXFILTRATION")
            for f in findings
        )
        n_confused = sum(
            sum(1 for p in f["predicates"] if str(p.get("predicate", "")).upper() == "CONFUSED_DEPUTY")
            for f in findings
        )
        print(
            f"replay findings={n_find}/{len(pool)} msgs={n_msg} exfil_preds={n_exfil} "
            f"confused={n_confused} raw={raw:.0f} norm={norm:.3f}",
            flush=True,
        )
        report["models"][model] = {
            "returned": len(candidates),
            "replayed": len(pool),
            "replay_findings": n_find,
            "messages": n_msg,
            "exfil_predicates": n_exfil,
            "confused_deputy": n_confused,
            "raw": raw,
            "normalized": norm,
            "gen_s": gen_s,
        }

    OUT = ROOT / "results" / "e7_final_gate.json"
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("\nwrote", OUT)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()