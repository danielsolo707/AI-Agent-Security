# E9 submit — DensifySafe (post Aug-7 rules + E8 autopsy)

**Submitted: ref 55443010 · kernel v16 · T4 GPU · PENDING (2026-08-12)**

**Message:** `E9 DensifySafe v16: MIN_SCORE_RAW fire-gate (E8 autopsy), REPLAY_SAFE 1.005 partial-timeout pack, inj_done fallback, multi-turn bank kept`

## Position at submit time

| Metric | Value |
|--------|------:|
| Best live (selected) | **E7 = 87.840** (ref 55404474) |
| E8 (regressed) | 82.530 (ref 55428527) |
| Rank / teams | **#358 / 1170** |
| Top-100 cutoff | **91.595** (gap **+3.76**) |
| Top-50 cutoff | 95.795 |
| Top-25 cutoff | 102.115 |
| #1 | 137.130 |
| Deadline | 2026-09-01 |
| Daily cap | 5 |

## Why E9 (vs re-shipping E7 / iterating E8)

### Rule / scoring changes (Aug 7, disc 733058)
1. **LB invalidated** — all pre-refresh scores (incl. old E4=87.75) are ERROR; only post-refresh runs count.
2. **Gemma parser v3.1.2** — double-brace fix claimed; multi-query gemma still risky in community reports.
3. **Replay timeout preserves partial score** (gen timeout still zeros) → we can pack closer to true 9000s replay budget.
4. **Deterministic re-scoring** on same kernel version.

### E8 autopsy (82.530)
Local bench showed gpt-oss duo/stack returning **raw≈2** (no EXFIL) but still counting as fire under `raw > 0`. Fast dead templates won raw/s screen → poisoned champion → host collapse. **E9 requires `raw >= MIN_SCORE_RAW (16)`.**

### E9 knobs vs E7 (87.840)
| Knob | E7 | E9 |
|------|----|----|
| Fire gate | raw > 0 | **raw ≥ 16** |
| Single-msg multipost | no | **no** (E8 killed) |
| Multi-TURN bank | yes | **kept** (host screen) |
| REPLAY_SAFE | 0.99 | **1.005** |
| COST_PAD | 1.01 | **1.005** |
| fill accel | pad×1.02 | **max(pad, 1.01)** |
| MARGIN_S | 90 | **70** |
| FALLBACK | plain (0) | **inj_done (5)** |

## Projected score band
- Floor: ~E7 (87–88) if densify is neutral and screen still picks singles.
- Target: **91.5–93** if ~4% more findings replay under partial-timeout packing.
- Stretch: multi-turn selected on gemma with real 34–50 raw → 95+.

## Files
- `src/attack_e9.py` / `src/attack.py` (active)
- `results/submits/attack_submit_e9.py`
- Prior best to **keep selected** until E9 scores: **E7 87.840**

## Read when scored
| Score | Next |
|-------|------|
| format / ≪85 | Revert to pure E7 code; check gen timeout / format |
| 85–88 flat | Densify neutral; next = faster unit (shorter prompts) or private hedge |
| **≥91.6** | **Top-100 lock**; densify further or multi-turn wording polish toward 95 |
| ≥95 | Top-50 path; freeze Slot A |
| ≪E7 | Bug in fire gate / sizing; re-ship E7 golden |
