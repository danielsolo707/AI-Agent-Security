"""E7 chain diagnosis: dump the full trace of one chain trial to see the mechanism.

Why chains fire 0: model refusal vs guardrail block vs wording issue.
Prints every tool event (name, ok, source, side_effect, args summary), final user
messages, and the predicate verdict.

Usage: PYTHONPATH=data;src;scripts python scripts/e7_chain_diag.py --model gpt-oss-20b --template chain_web_post
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from aicomp_sdk.core.env.sandbox import SandboxEnv  # noqa: E402
from aicomp_sdk.core.predicates import eval_predicates  # noqa: E402
from aicomp_sdk.guardrails.optimal import Guardrail as Optimal  # noqa: E402

from e7_chain_bench import TEMPLATES, MARKER  # noqa: E402

FIXTURES = ROOT / "data" / "aicomp_sdk" / "fixtures"


def lmstudio_models() -> list[str]:
    with urllib.request.urlopen("http://127.0.0.1:1234/v1/models", timeout=5) as r:
        data = json.loads(r.read().decode("utf-8"))
    return [m.get("id", "") for m in data.get("data", [])]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gpt-oss-20b")
    ap.add_argument("--template", default="chain_web_post")
    ap.add_argument("--hops", type=int, default=4)
    args = ap.parse_args()

    tpl = next((t for t in TEMPLATES if t[0] == args.template), None)
    if tpl is None:
        print("unknown template", args.template, [t[0] for t in TEMPLATES])
        return
    name, messages = tpl
    print(f"== {args.model} :: {name} :: messages={messages}")

    from openai_compat_blue_agent import make_lmstudio

    agent = make_lmstudio(args.model)
    env = SandboxEnv(seed=11, fixtures_dir=FIXTURES, agent=agent, guardrail=Optimal())
    for midx, msg in enumerate(messages):
        print(f"\n--- interact msg[{midx}] {msg[:90]}...")
        try:
            result = env.interact(msg, max_tool_hops=args.hops)
            print("   interact result:", str(result)[:200].replace("\n", " "))
        except Exception as exc:
            print("   interact ERR:", type(exc).__name__, str(exc)[:120])

    tr = env.export_trace_dict()
    print("\n== TOOL EVENTS ==")
    for i, e in enumerate(tr.get("tool_events", [])):
        args_short = {k: (str(v)[:50] if not isinstance(v, (int, float, bool)) else v) for k, v in (e.get("args") or {}).items()}
        print(
            f"[{i}] {e.get('name')} ok={e.get('ok')} src={e.get('source')} "
            f"se={e.get('side_effect')} args={args_short} err={str(e.get('error', ''))[:60]}"
        )
    print("\nuser_messages:", [m[:60] for m in tr.get("user_messages", [])])
    preds = eval_predicates(tr)
    print("predicates:", [(p.get("predicate"), p.get("severity"), p.get("evidence")) for p in preds])


if __name__ == "__main__":
    main()