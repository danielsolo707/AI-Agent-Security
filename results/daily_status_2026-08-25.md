# Daily Status — 2026-08-25 (ox-alpha session)

## Actions taken today
1. **Validator v7/v8 root-caused → v9 pushed (RUNNING)**
   - v7 died: TimeoutError in replay. Root cause: engine packs for its own
     REPLAY_BUDGET_S=9000 regardless of validator's budget_s=1800.
   - v8 fix (env-aware REPLAY_BUDGET_S, default unchanged 9000) STILL died:
     replay began ~t1365s, died exactly +1800s later. Packing shrank as designed,
     but T4/GGUF real replay cost per candidate runs hotter than engine's
     projected unit cost (COST_PAD only 1.01, UNIT_QUANTILE p75).
   - v9 fix: LOCAL_REPLAY_BUDGET_S = BUDGET_S * LOCAL_REPLAY_FRACTION (default 0.55)
     => packing targets ~982s unit-cost; survives ~1.8x real overrun. LB kernel untouched.
2. **E18o golden re-roll submitted** ref 55771784 (T4). Score pending at last check;
     network drops (user ISP) interrupted monitors repeatedly — rebuilt with retry logic.

## Live state
Best 90.765 (E18h) · rank #311/4014 · cutoff100 = 97.155 (gap +6.39) · deadline Sep 1 23:59 UTC.

## Monitors
proc_146c3a8bee2f → validator v9 (7-min poll, 12x net-retry)
proc_1593e13fc171 → E18o score (10-min poll)

## v9 result (19:45)
- **FIRST VALID NUMBER EVER: golden E18 on gpt_oss local = 86.94** (966 findings,
  966 unique cells, raw 17388, 1875.7s wall). Replay budget fix WORKED.
- gemma load crashed (GGUF "Failed to load model") → killed whole run (no isolation).
- v10 pushed: per-eval try/except isolation; gemma failure no longer kills golden/cand evals.
- Note: local 86.94 vs LB GPU mean ~88.9 → replica reads slightly low but same ballpark;
  comparison E18-vs-E22 on SAME host is still apples-to-apples.

## v10 RESULT — VALIDATOR COMPLETE (20:55) 🎯
| config | gpt_oss score | findings | cells | eval_time |
|---|---:|---:|---:|---:|
| attack_golden (E18)  | **84.33** | 937 | 937 | 1898s |
| attack_candidate (E22)| **83.70** | 930 | 930 | 1892s |
(gemma failed to load both times — GGUF file issue, isolated per-eval as designed)

## VERDICT: KILL E22
E22 Compact loses to golden by -0.63 (930 vs 937 findings) on identical host/seed.
Weatherhead-style compact prompts did NOT beat the frozen E18 engine locally.
Golden stays; no real submission slot spent. Consistent with geometry-freeze discipline.
Note: local scores drift run-to-run (86.94 in v9 vs 84.33 in v10 for same config)
→ variance ~±1.3; margin -0.63 is within noise BUT there is no positive signal,
and promoting would cost a real slot + regression risk. Kill stands.

## E18o FINAL (07:00 Aug 26) ⚠️
**E18o = 73.935 — worst GPU roll ever recorded** (previous band 86.9–90.8, n=10).
17h queue + catastrophic score. Two hypotheses:
1. Genuine lottery tail-luck (would be ~4-sigma outlier vs N(88.9,1) — very unlikely)
2. Degraded/contended T4 worker or host-side slowdown during that window
   (long queue is circumstantial evidence) → engine hit its internal margins and packed far fewer findings.
Action: treat 73.9 as an outlier data point; do NOT panic-adjust the engine.
Today's fresh slot: submit a new re-roll EARLY in the day. If it also lands <87,
then suspect environment shift and investigate before burning more slots.

## Aug 26 morning action
- **E18p submitted** ref 55785086 (04:03 UTC, T4, fresh day slot) — the diagnostic
  re-roll: if it lands <87 too, environment shift is confirmed and slots pause
  pending investigation. Monitor proc_621dc494496a.
