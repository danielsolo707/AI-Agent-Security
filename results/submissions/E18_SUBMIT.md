# E18 submit - RowLock (90+ from E14 floor)

**Submitted:** ref `55623497` | kernel `danielsolo1770/agent-security-phase0` v25 | T4 GPU | **COMPLETE 89.820 — NEW BEST (+1.215)**
**Date:** 2026-08-19

**Message:** `E18 RowLock: E14 floor + forge1-vs-plain speed lock, no 12s split no p70 no filled-JSON`

## Position before submit

| Metric | Value |
|--------|------:|
| Best live | **88.605** (E14 — keep selected) |
| E17 | **80.145** (p70 overpack) |
| E16 | **62.275** (latency split / filled forge) |
| E15 | 87.705 |
| Rank | #482 / 3690 |
| Target | **> 90** |
| Top public | 137.130 |

## Why E18

90.0 ≈ 1000 singles × 18 raw. E14 is ~985. The public mean is gated by the slower row.

Failed 90+ bets:
- E15: `gemma_forge` in the **global** screen stole a row (87.705)
- E16: 12s **mean** latency split + `forge1_filled` (62.275)
- E17: unit p70 (80.145)

E18 keeps the E14 engine (p75, REPLAY_SAFE 0.99, dense gate, forge1) and adds **one** lock:

1. After warmup, 3× `plain` vs 3× `forge1` (hops=1).
2. If `forge1` median < 0.80 × `plain` median → **slow** bank (Harmony only).
3. If `forge1` is slower / does not fire → **fast** bank (plain/bare only).
4. Ambiguous → E14 full bank.
5. Assistant-text Harmony / `<|tool_call>` tokens can confirm the lock. User text is ignored (forge1's own tokens must not classify gemma as slow).

No 12s threshold. No filled JSON. No p70.

## Verification

- py_compile PASS
- tests **12 passed / 0 failed**
- AlwaysPost 20/20 raw 360
- env=None 300
- classify unit: speedup → slow, slower/no-fire → fast

## Expected band

| Score | Next |
|------:|------|
| **> 90** | Select E18 |
| 88.6-90 | Keep best of E14/E18 |
| < 88.6 | Stay on E14; do not iterate lock knobs the same day |
