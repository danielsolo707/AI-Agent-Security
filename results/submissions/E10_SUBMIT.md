# E10 submit — GoldenTail top-100 push

**Submitted:** ref `55467616` · kernel `danielsolo1770/agent-security-phase0` v17 · T4 GPU · **PENDING**  
**Date:** 2026-08-12 21:45:16 Kaggle time / 2026-08-13 local session

**Message:** `E10 GoldenTail: E7 golden + raw>=16 gate + 10pct post-safe tail for Aug7 partial-replay top100 push`

## Position before submit

| Metric | Value |
|--------|------:|
| Best live public | **87.840** (E7, ref 55404474) |
| Current rank | **#394 / 1275** |
| Top-100 cutoff | **91.980** |
| Gap to top-100 | **+4.140** |
| Top-50 cutoff | **96.680** |
| Top-20 cutoff | **105.165** |
| Daily submissions remaining after submit | **4** |

## Research summary before submit

Checked top-20 leaderboard usernames and public notebooks/discussions. Most top-20 teams did not expose direct current code. Public evidence that influenced E10:

- `yw8837/88-875-lb-open-source-jed-attack-full-code`: N32 raw/s single-post baseline around 88.875.
- `tetsutani/ai-agent-sec-adaptive-uniform-two-probe-recovery`: reported 88.515–89.055 using validated single-post template racing.
- `pilkwang/*` and Cleanor discussions: scoring frontier is mostly EXFIL throughput; gpt_oss latency is the bottleneck; static blind spam and multi-post jumps often regress.
- Aug-7 official update: replay timeouts preserve partial score, while attack.py generation timeout still zeros. This makes a **post-safe-prefix tail** the cleanest +4.140 lever.

## E10 changes vs E7 golden

Base: `src/attack_e7.py`

1. Keep E7 geometry and safety constants:
   - `REPLAY_SAFE = 0.99`
   - `COST_PAD = 1.01`
   - `MARGIN_S = 90.0`
   - `MARGIN_MULT = 1.50`
   - same single-post + multi-turn bank.
2. Add E8/E9 lesson:
   - `MIN_SCORE_RAW = 16` to ignore cell-only false fires.
3. Add GoldenTail:
   - append selected-template blind tail **after** the E7-safe prefix.
   - `TAIL_EXTRA_FRAC = 0.10`
   - `TAIL_EXTRA_MAX = 140`
4. Active hash at test time:
   - `src/attack.py` sha256 `6454e28afd88fc831135ebdf0bd1f41f4b59ddfb27fd41c7d02b6910531dbc61`

## Verification before submit

- `python -m py_compile src/attack.py src/attack_e10.py` → PASS
- Manual run of `tests/test_attack_unit.py` functions → **10 passed / 0 failed**
- AlwaysPost smoke override:
  - 20 candidates
  - 20 findings
  - raw 360
  - normalized 1.8
- Kernel build:
  - `enable_gpu=true`
  - `machine_shape=NvidiaTeslaT4`
  - kernel v17 completed before code submission.

## Expected result band

| Outcome | Interpretation | Next action |
|---|---|---|
| < 87.840 | E10 tail/selection regressed | re-submit pure E7 or E7 with smaller tail |
| 88–91.9 | Tail partly helped but not enough | E11 = larger tail / best-of retry |
| **≥91.980** | **Top-100 reached** | freeze as selected; start top-50 plan |
| ≥96.680 | Top-50 reached | defend selected; explore top-20 mechanisms |

