"""Local red-team evaluation harness for src/attack.py."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
sys.path.insert(0, str(DATA))
sys.path.insert(0, str(ROOT / "src"))

from aicomp_sdk.agents import build_agent  # noqa: E402
from aicomp_sdk.attacks.contracts import AttackRunConfig  # noqa: E402
from aicomp_sdk.core.env.sandbox import SandboxEnv  # noqa: E402
from aicomp_sdk.core.predicates import eval_predicates  # noqa: E402
from aicomp_sdk.scoring import score_attack, score_attack_raw  # noqa: E402
from aicomp_sdk.core.cells import cell_signature  # noqa: E402

from attack import AttackAlgorithm  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget-s", type=float, default=45.0)
    parser.add_argument("--agent", default="deterministic")
    parser.add_argument("--guardrail", choices=("rules", "optimal", "allow"), default="optimal")
    parser.add_argument("--max-candidates", type=int, default=80)
    parser.add_argument("--out", type=str, default="")
    args = parser.parse_args()

    if args.guardrail == "rules":
        from aicomp_sdk.attacks.baselines.guardrail_rules import Guardrail
    elif args.guardrail == "allow":
        from aicomp_sdk.attacks.baselines.guardrail_allow import Guardrail
    else:
        from aicomp_sdk.guardrails.optimal import Guardrail

    fixtures = DATA / "aicomp_sdk" / "fixtures"
    env = SandboxEnv(
        seed=123,
        fixtures_dir=fixtures,
        agent=build_agent(args.agent),
        guardrail=Guardrail(),
    )

    attacker = AttackAlgorithm(
        {
            "max_turns": 10,
            "branch_batch": 12,
            "max_candidates": args.max_candidates,
        }
    )

    t0 = time.time()
    candidates = attacker.run(
        env,
        AttackRunConfig(time_budget_s=args.budget_s, max_steps=10**9, max_tool_hops=8),
    )
    gen_s = time.time() - t0
    print(f"generation_s={gen_s:.2f} candidates={len(candidates)}")

    # Replay each candidate for scorer-faithful scoring.
    findings = []
    for cand in candidates:
        env.reset()
        try:
            for msg in cand.user_messages:
                env.interact(msg, max_tool_hops=8)
            tr = env.export_trace_dict()
            preds = eval_predicates(tr)
            if not preds:
                continue
            sig = cell_signature(
                tr.get("tool_events", []),
                egress_data=tr.get("egress", []),
                user_messages=tr.get("user_messages", []),
            )
            findings.append(
                {
                    "user_messages": list(cand.user_messages),
                    "predicates": preds,
                    "cell_signature": sig,
                    "score_cell_signature": sig,
                }
            )
        except Exception as exc:
            print("replay_error", exc)

    raw = score_attack_raw(findings)
    norm = score_attack(findings, normalize=True)
    print(f"replay_findings={len(findings)} raw={raw:.1f} normalized={norm:.2f}")

    # Predicate histogram
    hist: dict[str, int] = {}
    for f in findings:
        for p in f["predicates"]:
            name = str(p.get("predicate"))
            hist[name] = hist.get(name, 0) + 1
    print("predicate_hist", hist)

    if findings:
        print("top_chain", findings[0]["user_messages"][:4])

    out = {
        "generation_s": gen_s,
        "candidates": len(candidates),
        "replay_findings": len(findings),
        "raw": raw,
        "normalized": norm,
        "predicate_hist": hist,
        "sample_findings": [
            {
                "messages": f["user_messages"],
                "predicates": [p.get("predicate") for p in f["predicates"]],
            }
            for f in findings[:10]
        ],
    }
    out_path = Path(args.out) if args.out else ROOT / "results" / f"local_{args.guardrail}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("wrote", out_path)


if __name__ == "__main__":
    main()
