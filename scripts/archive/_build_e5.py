"""Build results/submits/attack_submit_e5.py from src/attack.py (E4 N32)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src_path = ROOT / "src" / "attack.py"
out_path = ROOT / "results" / "submits" / "attack_submit_e5.py"

raw = src_path.read_text(encoding="utf-8")
# Drop existing module docstring
if raw.startswith('"""'):
    end = raw.find('"""', 3)
    raw = raw[end + 3 :].lstrip("\n")

header = '''"""AI Agent Security — Phase E5 (N32 + per-model template routing → 90+ aim).

Base: yw8837 N32 raw-rate (E4): 7 templates, raw/sec select, P75 size, REPLAY_SAFE=0.99.
Author host: 86.4–88.9. Our E2 multi peaked 68.6; E3 hybrid 61.8.

E5 delta (Cleanor Labs / discussion 731518):
  * Classify model speed with a few plain trials (latency only).
  * Slow row (gpt-oss-like): only Harmony inj_* templates + plain fallback.
  * Fast row (gemma-like): only plain/bare/call_syntax (no Harmony tax).
  * Then same raw/sec finalist + P75 packing as N32.

Target: public ~90+ mean if both rows pick high raw/sec templates.
"""

'''

raw = raw.replace(
    'VARIANT_NAME = "n32_rawrate_r1"',
    'VARIANT_NAME = "e5_n32_latency_split"',
)

knobs = """
# E5: route template bank by measured latency (no model name available).
USE_LATENCY_SPLIT = True
CLASSIFY_REPS = 3
SPLIT_THRESHOLD_S = 12.0  # host-ish: gpt_oss slow ~20s, gemma ~8s in old notes
# Indices into TEMPLATES for each bank (must include FALLBACK_INDEX=0 for safety).
FAST_TEMPLATE_IDX = (0, 1, 2, 3)       # plain, bare, bare_ok, call_syntax
SLOW_TEMPLATE_IDX = (0, 4, 5, 6)       # plain + inj_close/done/commentary
"""
if "USE_LATENCY_SPLIT" not in raw:
    raw = raw.replace("SLOWEST0 = 24.0\n", "SLOWEST0 = 24.0\n" + knobs)

old_screen = """        # Pay and discard one cold-start interaction.
        if has_time():
            trial(FALLBACK_INDEX, probe_index)
            probe_index += 1
            latencies[FALLBACK_INDEX].clear()
            fires[FALLBACK_INDEX] = 0
            raw_scores[FALLBACK_INDEX] = 0

        # Broad full-hop screen.
        for _ in range(SCREEN_REPS):
            for template_index in range(len(TEMPLATES)):
                if not has_time():
                    break
                trial(template_index, probe_index)
                probe_index += 1

        ranked_screen = sorted(
            range(len(TEMPLATES)),
            key=lambda index: (-_raw_per_second(latencies[index], raw_scores[index]), index),
        )
"""

new_screen = """        # Pay and discard one cold-start interaction.
        if has_time():
            trial(FALLBACK_INDEX, probe_index)
            probe_index += 1
            latencies[FALLBACK_INDEX].clear()
            fires[FALLBACK_INDEX] = 0
            raw_scores[FALLBACK_INDEX] = 0

        # E5: classify slow vs fast with plain template only.
        stored = getattr(self, "config", {}) if isinstance(getattr(self, "config", {}), Mapping) else {}
        use_split = bool(stored.get("use_latency_split", USE_LATENCY_SPLIT))
        split_thr = float(stored.get("split_threshold_s", SPLIT_THRESHOLD_S))
        classify_reps = max(1, int(stored.get("classify_reps", CLASSIFY_REPS)))
        active_indices = list(range(len(TEMPLATES)))
        row_label = "all"
        if use_split and has_time():
            classify_lats: list[float] = []
            for _ in range(classify_reps):
                if not has_time():
                    break
                trial(FALLBACK_INDEX, probe_index)
                probe_index += 1
                if latencies[FALLBACK_INDEX]:
                    classify_lats.append(latencies[FALLBACK_INDEX][-1])
            # Clear plain stats after classify so screen is unbiased
            latencies[FALLBACK_INDEX].clear()
            fires[FALLBACK_INDEX] = 0
            raw_scores[FALLBACK_INDEX] = 0
            if classify_lats:
                mean_lat = sum(classify_lats) / len(classify_lats)
                if mean_lat >= split_thr:
                    active_indices = list(stored.get("slow_template_idx", SLOW_TEMPLATE_IDX))
                    row_label = "slow"
                else:
                    active_indices = list(stored.get("fast_template_idx", FAST_TEMPLATE_IDX))
                    row_label = "fast"
                active_indices = [int(i) for i in active_indices if 0 <= int(i) < len(TEMPLATES)]
                if not active_indices:
                    active_indices = list(range(len(TEMPLATES)))
                    row_label = "all"

        # Screen only active bank (or all if split off).
        for _ in range(SCREEN_REPS):
            for template_index in active_indices:
                if not has_time():
                    break
                trial(template_index, probe_index)
                probe_index += 1

        ranked_screen = sorted(
            active_indices,
            key=lambda index: (-_raw_per_second(latencies[index], raw_scores[index]), index),
        )
"""

if old_screen not in raw:
    raise SystemExit("screen block not found — E4 source changed?")
raw = raw.replace(old_screen, new_screen)

raw = raw.replace(
    "TEMPLATES[selected][0],\n                candidate_count,",
    '("%s/%s" % (row_label, TEMPLATES[selected][0])),\n                candidate_count,',
)

final = header + raw
compile(final, str(out_path), "exec")
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(final, encoding="utf-8")
print("wrote", out_path, "bytes", len(final))
print("split OK", "USE_LATENCY_SPLIT" in final, "row_label" in final)
