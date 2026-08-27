# E17 submit - E14Clean (90+ from E14 floor)

**Submitted:** ref `55605397` | kernel `danielsolo1770/agent-security-phase0` v24 | T4 GPU | **PENDING**
**Date:** 2026-08-18

**Message:** `E17 E14Clean: E14 singles + forge1 open, density removed, unit p70, no split no filled-JSON`

## Position before submit

| Metric | Value |
|--------|------:|
| Best live | **88.605** (E14 — keep selected) |
| E16 | **62.275** (split / filled forge killed a row) |
| E15 | 87.705 |
| Target | **> 90** |

## What E17 is

E14 engine. Two deltas only:

1. Live bank is **singles** (`plain` / `bare` / `bare_ok` / `call_syntax` / `inj_*` / `plain_frame` / `forge1`). Density gone.
2. Unit quantile **0.75 → 0.70**. Slightly more candidates; Aug-7 partial replay covers an overpack tail.

No latency split. No `forge1_filled`. No `gemma_forge`.

## Verification

- py_compile PASS
- tests **12 passed / 0 failed**
- AlwaysPost 20/20 raw 360
- env=None 300

## Expected band

| Score | Next |
|------:|------|
| **> 90** | Select E17 |
| 88.6-90 | Keep best of E14/E17 |
| < 88.6 | Stay on E14 |
