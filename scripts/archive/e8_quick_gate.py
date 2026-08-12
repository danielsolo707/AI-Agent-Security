"""E8 quick gate: verify MsgStack selection + replay raw on ONE model.

Fixes e8_final_gate overload problem: full replay of 1800+ candidates hammers
LM Studio (URLError 10061). Since all returned candidates come from ONE
template, replaying the first ~40 and projecting is a faithful check:

1. run() with a modest budget -> what template does the raw/s screen pick?
2. Replay first N candidates in fresh envs -> observed raw/finding.
3. Projected: mean_raw_per_finding * candidate_count -> host-estimate normalized.

Usage: PYTHONPATH=data;src;scripts python scripts/e8_quick_gate.py --model gemma-4-26b --budget 300 --n 40
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from aicomp_sdk.attacks.contracts import AttackRunConfig  # noqa: E402
from aicomp_sdk.core.env.sandbox import SandboxEnv  # noqa: E402
from aicomp_sdk.core.predicates import eval_predicates  # noqa: E402
from aicomp_sdk.guardrails.optimal import Guardrail as Optimal  # noqa: E402

import attack_e8 as attack_mod  # noqa: E402

FIXTURES = ROOT / "data" / "aicomp_sdk" / "fixtures"


def lmstudio_models() -> list[str]:
    with urllib.request.urlopen("http://127.0.0.1:1234/v1/models", timeout=5) as r:
        data = json.loads(r.read().decode("utf-8"))
    return [m.get("id", "") for m in data.get("data", [])]


def replay_raw(env: SandboxEnv, candidates, hops: int = 8) -> tuple[list[int], list[float]]:
    """Return per-candidate raw scores by replaying in fresh envs (host semantics)."""
    raws: list[int] = []
    lats: list[float] = []
    for idx, cand in enumerate(candidates):
        env.reset()
        t0 = time.monotonic()
        try:
            for msg in cand.user_messages:
                env.interact(msg, max_tool_hops=hops)
            tr = env.export_trace_dict()
            preds = eval_predicates(tr)
            total = 0
            for p in preds:
                total += attack_mod.SEVERITY_W.get(int(p.get("severity", 1)), 1)
            raws.append(total + 2 if total else 0)
        except Exception as exc:  # noqa: BLE001
            print(f"  replay exc: {type(exc).__name__}: {exc}", flush=True)
            raws.append(0)
        lats.append(time.monotonic() - t0)
        if idx % 5 == 4:
            time.sleep(2.0)  # pace: avoid LM Studio connection-refused overload
            sys.stdout.flush()
    return raws, lats


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gemma-4-26b")
    ap.add_argument("--budget", type=float, default=300.0)
    ap.add_argument("--n", type=int, default=40, help="candidates to replay")
    ap.add_argument("--hops", type=int, default=8)
    args = ap.parse_args()

    available = lmstudio_models()
    print("LM Studio:", available, flush=True)
    assert args.model in available, f"{args.model} not loaded"

    from openai_compat_blue_agent import make_lmstudio

    agent = make_lmstudio(args.model)
    env = SandboxEnv(seed=11, fixtures_dir=FIXTURES, agent=agent, guardrail=Optimal())
    attack = attack_mod.AttackAlgorithm()
    cfg = AttackRunConfig(time_budget_s=args.budget, max_tool_hops=args.hops)

    started = time.monotonic()
    candidates = attack.run(env, cfg)
    run_s = time.monotonic() - started

    msgs = [c.user_messages for c in candidates[:2]]
    lens = {len(c.user_messages) for c in candidates}
    print(f"\nrun() returned {len(candidates)} candidates in {run_s:.1f}s "
          f"msg_lens={sorted(lens)} sample={msgs}", flush=True)

    # Replay a sample in fresh envs (paced to avoid LM Studio overload).
    n = min(args.n, len(candidates))
    replay_env = SandboxEnv(seed=12, fixtures_dir=FIXTURES, agent=agent, guardrail=Optimal())
    raws, lats = replay_raw(replay_env, candidates[:n], hops=args.hops)
    fired = sum(1 for r in raws if r > 0)
    mean_raw = statistics.mean(raws) if raws else 0.0
    mean_lat = statistics.mean(lats) if lats else 0.0
    host_est = (mean_raw * len(candidates)) / 200000.0 * 1000.0 if mean_raw else 0.0
    print(f"replay n={n}: fired={fired}/{n} mean_raw/finding={mean_raw:.1f} "
          f"mean_lat={mean_lat:.1f}s", flush=True)
    print(f"PROJECTED host normalized (mean_raw x {len(candidates)} candidates): {host_est:.0f}", flush=True)

    report = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model": args.model,
        "budget": args.budget,
        "returned": len(candidates),
        "msg_lens": sorted(lens),
        "sample": msgs,
        "run_s": round(run_s, 1),
        "replay_n": n,
        "replay_fired": fired,
        "mean_raw_per_finding": round(mean_raw, 2),
        "mean_replay_lat": round(mean_lat, 2),
        "projected_normalized": round(host_est, 1),
    }
    out = ROOT / "results" / "e8_quick_gate.json"
    out.write_text(json.dumps(report, indent=2))
    print(f"\nwrote {out}", flush=True)


if __name__ == "__main__":
    main()