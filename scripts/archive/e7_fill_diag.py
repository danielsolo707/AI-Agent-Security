"""Reproduce e7_final_gate validation-fill fired=0 bug with visible errors."""
from __future__ import annotations

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
from aicomp_sdk.guardrails.optimal import Guardrail as Optimal  # noqa: E402

import attack_e7 as attack_mod  # noqa: E402

FIXTURES = ROOT / "data" / "aicomp_sdk" / "fixtures"


def main() -> None:
    from openai_compat_blue_agent import make_lmstudio

    agent = make_lmstudio("gpt-oss-20b")
    env = SandboxEnv(seed=11, fixtures_dir=FIXTURES, agent=agent, guardrail=Optimal())
    attacker = attack_mod.AttackAlgorithm({})

    # --- Phase 1: reproduce the screen trial (plain template, index 900000)
    idx = 900000
    builder = attack_mod.TEMPLATES[0][1]
    msgs = attack_mod._messages(builder, idx)
    print("msgs:", msgs)
    for t in range(6):
        env.reset()
        t0 = time.monotonic()
        try:
            for msg in msgs:
                env.interact(msg, max_tool_hops=8)
            raw = attack_mod._trace_raw_score(env.export_trace_dict())
            print(f"trial {t}: raw={raw} elapsed={time.monotonic()-t0:.2f}s OK")
        except Exception as exc:
            print(f"trial {t}: EXC {type(exc).__name__}: {str(exc)[:200]} elapsed={time.monotonic()-t0:.2f}s")


if __name__ == "__main__":
    main()