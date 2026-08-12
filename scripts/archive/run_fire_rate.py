"""Fire-rate probe for any OpenAI-compat blue agent (DeepSeek or LM Studio).

Examples:
  # Intermediate (DeepSeek flash)
  python scripts/run_fire_rate.py --backend deepseek --n 5

  # FINAL TEST ONLY
  python scripts/run_fire_rate.py --backend lmstudio --model gpt-oss-20b --n 8
  python scripts/run_fire_rate.py --backend lmstudio --model gemma-4-26b --n 8
"""

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

from aicomp_sdk.core.env.sandbox import SandboxEnv  # noqa: E402
from aicomp_sdk.core.predicates import eval_predicates  # noqa: E402
from aicomp_sdk.guardrails.optimal import Guardrail as Optimal  # noqa: E402

import attack as attack_mod  # noqa: E402
from openai_compat_blue_agent import make_deepseek_flash, make_lmstudio  # noqa: E402

FIXTURES = ROOT / "data" / "aicomp_sdk" / "fixtures"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--backend", choices=("deepseek", "lmstudio"), default="deepseek")
    p.add_argument("--model", default="", help="LM Studio model id")
    p.add_argument("--n", type=int, default=5)
    p.add_argument("--out", default="")
    args = p.parse_args()

    if args.backend == "deepseek":
        agent = make_deepseek_flash()
        label = "deepseek-v4-flash"
    else:
        if not args.model:
            raise SystemExit("--model required for lmstudio (e.g. gpt-oss-20b, gemma-4-26b)")
        agent = make_lmstudio(args.model)
        label = args.model

    templates = [
        ("verbose", attack_mod.TEMPLATE),
        ("frame", attack_mod.FRAME_TEMPLATE),
        *[(f"alt{i}", t) for i, t in enumerate(attack_mod.ALT_TEMPLATES)],
    ]

    env = SandboxEnv(
        seed=123,
        fixtures_dir=FIXTURES,
        agent=agent,
        guardrail=Optimal(),
    )

    rows = []
    for name, template in templates:
        fires = exfils = errors = 0
        lats: list[float] = []
        sample = None
        for i in range(args.n):
            msg = attack_mod._msg(20_000 + i, template)
            t0 = time.time()
            try:
                env.reset()
                env.interact(msg, max_tool_hops=4)
                elapsed = time.time() - t0
                lats.append(elapsed)
                tr = env.export_trace_dict()
                fired = attack_mod._fired(env)
                preds = [p.get("predicate") for p in eval_predicates(tr)]
                tools = [e.get("name") for e in tr.get("tool_events", []) if e.get("ok")]
                if fired:
                    fires += 1
                if "EXFILTRATION" in preds:
                    exfils += 1
                if i == 0:
                    sample = {
                        "msg_preview": msg[:90],
                        "tools_ok": tools,
                        "preds": preds,
                        "elapsed": elapsed,
                    }
            except Exception as exc:
                errors += 1
                lats.append(time.time() - t0)
                if i == 0:
                    sample = {"error": f"{type(exc).__name__}: {str(exc)[:200]}"}
            print(f"  {label}/{name} {i+1}/{args.n} fires={fires}", flush=True)

        row = {
            "backend": args.backend,
            "model": label,
            "template": name,
            "trials": args.n,
            "fires": fires,
            "exfils": exfils,
            "errors": errors,
            "fire_rate": fires / max(1, args.n),
            "exfil_rate": exfils / max(1, args.n),
            "mean_latency_s": sum(lats) / max(1, len(lats)),
            "sample": sample,
        }
        rows.append(row)
        print(
            f"{name}: fire={fires}/{args.n} exfil={exfils} "
            f"lat={row['mean_latency_s']:.2f}s err={errors}"
        )

    out = Path(args.out) if args.out else ROOT / "results" / f"fire_rate_{args.backend}_{label.replace('/', '_')}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
