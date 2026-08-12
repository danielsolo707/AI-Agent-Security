"""Run AttackAlgorithm live-fill against a blue agent; write throughput report."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from aicomp_sdk.attacks.contracts import AttackRunConfig  # noqa: E402
from aicomp_sdk.core.env.sandbox import SandboxEnv  # noqa: E402
from aicomp_sdk.guardrails.optimal import Guardrail as Optimal  # noqa: E402

import attack as attack_mod  # noqa: E402
from openai_compat_blue_agent import make_deepseek_flash, make_lmstudio  # noqa: E402

FIXTURES = ROOT / "data" / "aicomp_sdk" / "fixtures"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--backend", choices=("deepseek", "lmstudio"), default="deepseek")
    p.add_argument("--model", default="")
    p.add_argument("--budget-s", type=float, default=90.0)
    p.add_argument("--hard-n-cap", type=int, default=40)
    p.add_argument("--out", default="")
    args = p.parse_args()

    if args.backend == "deepseek":
        agent = make_deepseek_flash()
        label = "deepseek-v4-flash"
    else:
        if not args.model:
            raise SystemExit("--model required for lmstudio")
        agent = make_lmstudio(args.model)
        label = args.model

    env = SandboxEnv(
        seed=123,
        fixtures_dir=FIXTURES,
        agent=agent,
        guardrail=Optimal(),
    )
    atk = attack_mod.AttackAlgorithm(
        {
            "hard_n_cap": args.hard_n_cap,
            "fill_budget_frac": 0.95,
            "probe_hops": 1,
            "replay_safe_sizing": True,
            "replay_safe_frac": 0.97,
            "diversity_budget_frac": 0.0,
            "split_by_latency": True,
        }
    )
    t0 = time.time()
    cands = atk.run(env, AttackRunConfig(time_budget_s=args.budget_s, max_tool_hops=4))
    elapsed = time.time() - t0
    report = {
        "backend": args.backend,
        "model": label,
        "budget_s": args.budget_s,
        "elapsed_s": elapsed,
        "candidates": len(cands),
        "per_cand_s": elapsed / max(1, len(cands)),
        "proj_9000": int(len(cands) / max(elapsed, 1e-6) * 9000),
        "est_public_score": round(0.09 * len(cands), 3),  # if all unique EXFIL cells
        "sample": list(cands[0].user_messages) if cands else [],
    }
    print(json.dumps(report, indent=2))
    out = (
        Path(args.out)
        if args.out
        else ROOT / "results" / f"live_fill_{args.backend}_{label.replace('/', '_')}.json"
    )
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
