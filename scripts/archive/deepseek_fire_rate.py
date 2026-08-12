"""Measure DeepSeek-v4-flash fire rate on SECRET_MARKER http.post templates.

Uses OptimalGuardrail + sandbox. Never prints API keys.
"""

from __future__ import annotations

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
from deepseek_blue_agent import DeepSeekBlueAgent, load_dotenv, smoke_hello, _model  # noqa: E402

FIXTURES = ROOT / "data" / "aicomp_sdk" / "fixtures"
OUT = ROOT / "results" / "deepseek_fire_rate.json"


def main() -> None:
    load_dotenv()
    model = _model()
    if model != "deepseek-v4-flash":
        raise SystemExit(f"Refusing non-flash model: {model!r}")

    print("connectivity check (model=deepseek-v4-flash)...")
    try:
        reply = smoke_hello()
        print("smoke_reply_len", len(reply), "preview", reply[:40].replace("\n", " "))
    except Exception as exc:
        print("SMOKE_FAILED", type(exc).__name__, str(exc)[:200])
        raise SystemExit(1) from exc

    templates = [
        ("verbose", attack_mod.TEMPLATE),
        ("frame", attack_mod.FRAME_TEMPLATE),
        *[(f"alt{i}", t) for i, t in enumerate(attack_mod.ALT_TEMPLATES)],
    ]
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 5

    agent = DeepSeekBlueAgent()
    env = SandboxEnv(
        seed=123,
        fixtures_dir=FIXTURES,
        agent=agent,
        guardrail=Optimal(),
    )

    rows = []
    for name, template in templates:
        fires = 0
        exfils = 0
        errors = 0
        lat = []
        samples = []
        for i in range(n_per):
            msg = attack_mod._msg(10_000 + i, template)
            t0 = time.time()
            try:
                env.reset()
                env.interact(msg, max_tool_hops=4)
                elapsed = time.time() - t0
                lat.append(elapsed)
                tr = env.export_trace_dict()
                tool_names = [e.get("name") for e in tr.get("tool_events", []) if e.get("ok")]
                fired = attack_mod._fired(env)
                preds = [p.get("predicate") for p in eval_predicates(tr)]
                if fired:
                    fires += 1
                if "EXFILTRATION" in preds:
                    exfils += 1
                if i == 0:
                    samples.append(
                        {
                            "msg_preview": msg[:100],
                            "tools_ok": tool_names,
                            "preds": preds,
                            "elapsed": elapsed,
                        }
                    )
            except Exception as exc:
                errors += 1
                lat.append(time.time() - t0)
                if i == 0:
                    samples.append({"error": f"{type(exc).__name__}: {str(exc)[:160]}"})
            print(f"  {name} trial {i+1}/{n_per} fires_so_far={fires}", flush=True)

        rows.append(
            {
                "template": name,
                "model": model,
                "trials": n_per,
                "fires": fires,
                "exfils": exfils,
                "errors": errors,
                "fire_rate": fires / max(1, n_per),
                "exfil_rate": exfils / max(1, n_per),
                "mean_latency_s": sum(lat) / max(1, len(lat)),
                "samples": samples,
            }
        )
        print(
            f"{name}: fire_rate={fires}/{n_per} exfil={exfils} "
            f"mean_lat={rows[-1]['mean_latency_s']:.2f}s errors={errors}"
        )

    OUT.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
