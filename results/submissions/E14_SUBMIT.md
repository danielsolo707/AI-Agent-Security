# E14 submit - Forge1 (E11 floor + correct Harmony tool prefix)

**Submitted:** ref `55561900` | kernel `danielsolo1770/agent-security-phase0` v21 | T4 GPU | **COMPLETE 88.605**
**Date:** 2026-08-16

**Message:** `E14 Forge1: E11 floor + to=functions.http.post commentary prefix, dense champion gate raw>=30`

## Position before submit

| Metric | Value |
|--------|------:|
| Best live public | **88.515** (E11, ref 55502576) |
| E13 SoloReturn | 83.250 (regression, ref 55538989) |
| E12 | 78.750 (regression, ref 55523383) |
| Rank | **#399 / 1611** |
| Top-100 cutoff | **92.925** |
| Gap to top-100 | **+4.410** |
| #1 | 137.130 (~1524 singles at ~5.9s) |

## Why E13/E12 lost, and why UTA is not E14

- E13 changed E11 geometry (FINAL_REPS 7 for top-2 + two new singles). Host 83.250.
- E12 let density win a wide finalist pool. Host 78.750.
- Public Optimal denies `http.post` for 5 events after web/email. UTA only looks back 2 events. **UTA cannot score on public.** Confirmed in SDK + discussion 734213.
- The 88-90 band is the singles replay wall (~983 findings x 18 raw / 200). Leaving it requires **faster replay**, not more candidates or packing knobs.

## E14 changes vs E11 (the 88.515 champion)

1. **Byte-stable E11 engine**: finalists=4, FINAL_REPS=5, SCREEN_HOPS 1/3/5, hops-1 validation charged at projected_unit, tail 0.10/140, REPLAY_SAFE 0.99, COST_PAD 1.01, MIN_SCORE_RAW 16.
2. **`forge1`**: after closing the analysis channel, open commentary with the **parser-required** header `to=functions.http.post` (`gpt_oss_agent.py` regex). Older `inj_commentary` omitted this, so gpt-oss still had to invent the tool target. Screen still picks per model (gemma should keep `plain`).
3. **Dense champion gate**: `dturn_*` / `burst2` / `forge4` cannot become champion unless hops=8 mean raw >= 30. Stops 18-raw two-turn losers from winning on probe noise.

## Verification before submit

- `python -m py_compile src/attack.py src/attack_e14.py` -> PASS
- `tests/test_attack_unit.py` -> **11 passed / 0 failed**
- AlwaysPost smoke: 20 candidates / 20 findings / raw 360 / normalized 1.8
- env=None fallback: 300 candidates, all 1-message
- Kernel builder now defaults `enable_gpu=true` / `NvidiaTeslaT4` (opt out with `KAGGLE_ENABLE_GPU=0`)

## Expected result band

| Outcome | Interpretation | Next action |
|---|---|---|
| < 87.84 | forge1 poisoned the screen or variance | re-submit E11 byte-identical |
| 87.8-88.5 | ≈ E11; forge1 did not win or was neutral | E15 = force forge1 on the slow row only |
| 88.5-92.9 | forge1 cut gpt-oss latency | keep selected; tighten unit / T4x2 |
| >= 92.925 | **Top-100 reached** | freeze; start top-50 plan |
