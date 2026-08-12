# E6 submit — N32 global screen + champion validation-fill + K=2 multipost option

**Submitted: ref 55387090 · kernel v13 · T4 GPU · scriptVersionId 341292616 · PENDING (2026-08-09)**

**Context:**
- E4 (N32 raw-rate, 7 templates, T4 GPU) = **87.750** ← prior best (ref 55221895)
- E5 (N32 + dual-probe latency-split, CPU) = **78.570** ← regression (ref 55233913)
- Live LB (2026-08-09): #1 = 134.410, rank-50 = 92.67, rank-23 ≈ 100.8 → >100 needs top ~25

## E6 changes vs E4 (the 87.75 engine)
1. **Global screen kept** — all templates screened, ranked by raw/sec (no E5-style forced bank routing −9 pts regression).
2. **+Live validation-fill of the champion** (dimong4 ~90.09 pattern): after raw/sec selection, spend remaining live budget validating candidates of the winning template; keep ONLY those that demonstrably fire at the same max_tool_hops the replay will use. Every returned candidate is a proven fire → its 0.09 is earned in replay.
3. **dimong4-style replay-safe sizing**: charge each kept candidate its MEASURED latency (fill latency == true replay cost); accumulate and stop at the cap — no more P75-estimate blind sizing.
4. **Top-up safety**: if fill under-collects, pad with blind champion emit up to the REMAINING replay budget — never worse than E4, never above cap.
5. **+m2_inj (multipost K=2, Harmony frame)** in the bank: ties singles on gpt-oss (raw/s 4.55 vs 4.53) — host screen decides single vs multi empirically.
6. **Replay-safe constant kept**: REPLAY_SAFE 0.99, COST_PAD 1.01, cap 2000, T4 GPU like E4.

## Local gate (LM Studio real models, 2026-08-09, budget 240s)
| Model | Returned | Replay fire (sample 15) | Implied unit |
|-------|----------|------------------------|--------------|
| gpt-oss-20b | **1995** (~2000 cap) | 14/15 | ~4.4s (inj_done picked) |
| gemma-4-26b | **1517** | 15/15 | ~5.8s (call_syntax picked) |

Local projection: gpt-oss ~179, gemma ~136 → mean ~158 (host replay is much slower; expect lower, but 100+ is the aim).

## Files
- `src/attack_e6.py` — source (copied to `src/attack.py` for kernel embed)
- `src/attack_e5_backup.py` — E5 backup (78.570)
- `results/submits/attack_submit_e6.py` — packaged copy
- `scripts/e6_final_gate.py`, `scripts/e6_multipost_bench.py` — test rigs
- `results/e6_final_gate.json`, `results/e6_multipost_bench.json` — gate data