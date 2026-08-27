# E11 submit - FastFill FrameForge top-100 push

**Submitted:** ref `55502576` | kernel `danielsolo1770/agent-security-phase0` v18 | T4 GPU | **PENDING**
**Date:** 2026-08-14

**Message:** `E11 FastFill FrameForge: 13-template bank, hops-1 screen/validation, plain_frame+forge4 for gpt-oss`

## Position before submit

| Metric | Value |
|--------|------:|
| Best live public | **87.840** (E7, ref 55404474) |
| E10 GoldenTail | **87.795** (ref 55467616) |
| Top-100 cutoff | **~91.6-92.0** |
| Gap to top-100 | **+4.1** |

## Research summary before submit

Intel from top notebooks / forum / repo:

- **hops=1 probes fire identically to hops=8** (12/12 both models) - screen/validation can run at hop 1.
- nctuan jed-v25 (135 votes): Harmony-frame VERBOSE wording kills gpt-oss CoT; slow-row only.
- nctuan jed-slow-multipost (65 votes): token-forged multi-post ~4.0 posts/candidate at N=4 vs 0.33 natural; ~1.1x net gain but ~3.6x replay cost; harness executes only first tool call per generation.
- Replay is time-bound: E7 raw 17,568 = ~976 findings x 18 at ~9.2s per finding; 9000s per model per phase.
- coolin666 jed-attack-v12: BURST_K=2 (34 raw/cand), REPLAY_SAFE_FRAC 0.90, cap 2500.
- E9 (REPLAY_SAFE 1.005) = 85.410 regressed; E10 tail ~0. Golden = E7 87.840.

## E11 changes vs E10

Base: `src/attack_e10.py`

1. Template bank grows 10 -> **13** templates:
   - `plain_frame` (nctuan v25 VERBOSE wording, 1 msg)
   - `burst2` (two posts one hop, 1 msg, SCREEN_HOPS=3)
   - `forge4` (nctuan slow-multipost N=4 wording, 1 msg, SCREEN_HOPS=5)
2. **SCREEN_HOPS per template**: 1 for singles/multi-msg, 3 for burst2, 5 for forge4.
3. **FastFill validation**: validation-fill probes run at shallow hops but each candidate is charged the honest projected unit (p75 x COST_PAD) - replay accounting stays honest; screen time freed up.
4. Top-4 finalists re-probed at **hops=8** for honest sizing.
5. Safety constants unchanged: `MIN_SCORE_RAW=16`, `REPLAY_SAFE=0.99`, `COST_PAD=1.01`, `MARGIN_S=90.0`, `MARGIN_MULT=1.50`, tail 0.10/140, `FALLBACK_INDEX=0`.
6. Active hash at submit:
   - `src/attack.py` sha256 `09e4ec8898afc843c0c21b7539f48a13f4c52bbca09cbb6b485edd5092f4c9b7`
   - embedded-in-kernel sha256 MATCH (21640 bytes)

## Verification before submit

- `python -m py_compile src/attack_e11.py src/attack.py` -> PASS
- `tests/test_attack_unit.py` -> **10 passed / 0 failed**
- AlwaysPost smoke override: 20 candidates / 20 findings / raw 360 / normalized 1.8
- env=None fallback: 300 candidates, all 1-message
- All 13 templates shape-checked (marker+url present, no share-intent words, msg len ok)
- Kernel build: `enable_gpu=true`, `machine_shape=NvidiaTeslaT4`, v18 COMPLETE before code submit

## Expected result band

| Outcome | Interpretation | Next action |
|---|---|---|
| < 87.840 | hops-1 probes mis-scaled or new templates lost screen | re-submit pure E7 golden |
| 88-91.9 | FrameForge helped partly, not enough | E12 = more finalists / deeper forge |
| **>= 91.98** | **Top-100 reached** | freeze as selected; start top-50 plan |
| >= 96.68 | Top-50 reached | defend selected; explore top-20 mechanisms |
