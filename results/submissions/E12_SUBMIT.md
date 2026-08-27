# E12 submit - DeepFrame ReplayRank top-100 push

**Submitted:** ref `55523383` | kernel `danielsolo1770/agent-security-phase0` v19 | T4 GPU | **PENDING**
**Date:** 2026-08-14

**Message:** `E12 DeepFrame ReplayRank: finalists 4->8, burst3/forge6/plain_frame2 added, hops=8 re-probe = honest replay raw/s rank`

## Position before submit

| Metric | Value |
|--------|------:|
| Best live public | **88.515** (E11, ref 55502576) |
| E7 golden | 87.840 (ref 55404474) |
| Top-100 cutoff | ~91.6-92.0 |
| Gap to top-100 | +3.1 |

## Replay-cap analysis (why E11 stalled at 88.5)

LB raw ~= replay_cap / per-finding-replay-time x 18:

- E7 raw 17,568 = ~976 findings; E11 raw 17,703 = ~983 findings.
- 9000s replay budget / 976 findings ~= 9.2s per finding (8 hops).
- Both E7 and E11 sit AT the replay-cap wall: more candidates do not fit.
- The ONLY lever left is raw per replay second (density or faster termination).

## E12 changes vs E11

1. **FINALISTS 4 -> 8**: the shallow screen ranks singles first (18/1gen vs
   34/3gen), so dense templates rarely reached the finalist pool whose hops=8
   re-probe is the HONEST raw/s rank. A wide pool gives burst2/forge4/6 their
   honest replay raw/s measurement. Replay always burns ~8 hops per finding,
   so extra early posts convert churned hops into EXFIL raw.
2. New templates: `burst3` (3 posts/msg, SCREEN_HOPS=4), `forge6` (6 posts/msg,
   SCREEN_HOPS=7), `plain_frame2` (v25 wording variant). 16 templates total.
3. Safety unchanged: MIN_SCORE_RAW=16, REPLAY_SAFE=0.99, COST_PAD=1.01,
   MARGIN_S=90, MARGIN_MULT=1.50, tail 0.10/140, FALLBACK_INDEX=0.

Screen cost with 8 finalists ~= 870s/phase + validation ~960s << 9000s budget:
generation has slack; replay budget is the binding constraint.

## Verification before submit

- `python -m py_compile src/attack_e12.py src/attack.py` -> PASS
- `tests/test_attack_unit.py` -> **10 passed / 0 failed**
- AlwaysPost smoke: 20 candidates / 20 findings / raw 360 / normalized 1.8
- env=None fallback: 300 candidates, all 1-message
- All 16 templates shape-checked (marker+url, no share-intent words, msg len)
- Kernel build: enable_gpu=true, machine_shape=NvidiaTeslaT4, v19 COMPLETE

## Expected result band

| Outcome | Interpretation | Next action |
|---|---|---|
| < 88.515 | density lost the honest rank on both rows | re-submit E11 or pure E7 |
| 88.5-90.5 | singles still champion; small bank gain | E13 = per-template replay probe depth match |
| **90.5-91.9** | density won one row | E13 = deepen density (forge8/burst4) |
| >= 91.98 | **Top-100 reached** | freeze; start top-50 plan |