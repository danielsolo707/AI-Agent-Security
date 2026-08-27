# E13 submit - SoloReturn (back to E11-proof geometry)

**Submitted:** ref `55538989` | kernel `danielsolo1770/agent-security-phase0` v20 | T4 GPU | **PENDING**
**Date:** 2026-08-16

**Message:** `E13 SoloReturn: E11-proof geometry (finalists=4), FINAL_REPS 7 for top-2 (stabler unit), +plain_frame2/+inj_dual_close single-post variants`

## Position before submit

| Metric | Value |
|--------|------:|
| Best live public | **88.515** (E11, ref 55502576) |
| E12 | 78.750 (regression, ref 55523383) |
| Top-100 cutoff | ~91.6-92.0 |
| Gap to top-100 | +3.1 |

## E12 autopsy (why 78.750)

- Wide finalist pool (4->8) let a dense template (forge6/burst3) win the honest
  hops=8 raw/s rank on at least one row, but replay amortization is a myth on
  this host: gpt-oss false-fires multi-posts, gemma parser caps ~1 post per
  candidate (E8 = 82.53, E12 = 78.75, E7 chains dead — all consistent).
- Replay budget is the binding constraint (9000s shared, ~9.06s per finding,
  ~983 findings max); per-finding raw is ~18 for anything that actually fires.

## E13 changes vs E11 (the 88.515 champion)

1. **Byte-identical E11 engine** (finalists=4, SCREEN_HOPS 1/3/5, hops-1
   validation charged at projected_unit, tail 0.10/140, REPLAY_SAFE 0.99,
   COST_PAD 1.01, MIN_SCORE_RAW 16).
2. **FINAL_REPS 5 -> 7 for the top-2 finalists**: stabler p75 unit -> the
   candidate_count lands closer to the true replay cap without overshoot
   (generation has slack; ~36s/phase extra is free).
3. Two new SINGLE-post frame variants: `plain_frame2` (v25 wording variant),
   `inj_dual_close` (closes BOTH analysis + commentary channels).

## Verification before submit

- `python -m py_compile src/attack_e13.py src/attack.py` -> PASS
- `tests/test_attack_unit.py` -> **10 passed / 0 failed**
- AlwaysPost smoke: 20 candidates / 20 findings / raw 360 / normalized 1.8
- env=None fallback: 300 candidates, all 1-message
- All 15 templates shape-checked
- Kernel build: enable_gpu=true, machine_shape=NvidiaTeslaT4, v20 COMPLETE

## Expected result band

| Outcome | Interpretation | Next action |
|---|---|---|
| < 87.84 | E11 gain was luck; sizing change hurt | re-submit E11 byte-identical |
| 87.8-88.5 | ≈ E11; stabler unit neutral | accept; variance rolls |
| 88.5-90.5 | stabler unit tightened packing | E14 = REPLAY_SAFE 0.995 with top-2 x7 |
| >= 91.98 | **Top-100 reached** | freeze; start top-50 plan |
