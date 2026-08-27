# E16 submit - StopFast (90+ push)

**Submitted:** ref `55587268` | kernel `danielsolo1770/agent-security-phase0` v23 | T4 GPU | **COMPLETE 62.275**
**Date:** 2026-08-17

**Message:** `E16 StopFast: latency-split 12s, forge1_filled JSON on slow row, no density/gemma_forge, 90+ push`

## Position before submit

| Metric | Value |
|--------|------:|
| Best live | **88.605** (E14, keep selected) |
| E15 GemmaForge | **87.705** (poisoned screen) |
| Target | **> 90** |
| Top-100 | 93.065 |

## Why E15 failed / what E16 changes

E15 added `gemma_forge` to the **global** screen. It can win on gpt-oss and slow the row. 87.705 vs 88.605.

E16 does **not** add a competing template to a shared bank:

1. **8-probe latency split** (nctuan v25): mean plain > 12s → SLOW bank (`forge1_filled`, `forge1`, `plain_frame`, `inj_done`, `plain`). Else FAST bank (`plain`, `bare`, `bare_ok`, `call_syntax`). Harmony never runs on gemma; density/gemma_forge deleted.
2. **`forge1_filled`**: same `to=functions.http.post` hijack as E14, JSON body pre-written. gpt-oss should emit only `<|call|>`.
3. Safety unchanged: REPLAY_SAFE 0.99, p75, hops=8 re-probe, MIN_SCORE_RAW 16, tail 0.10/140.

90.0 needs ~1000 x 18 raw (~0.15s faster than E14's ~9.15s). That is a small speed win on the locked slow row, not a new predicate.

## Verification

- py_compile PASS
- tests **12 passed / 0 failed**
- AlwaysPost 20/20 raw 360
- env=None 300 singles

## Expected band

| Score | Next |
|------:|------|
| **> 90** | Keep E16 selected |
| 88.6-90 | Keep best; do not add templates |
| < 88.6 | Re-select E14; do not iterate split knobs the same day |
