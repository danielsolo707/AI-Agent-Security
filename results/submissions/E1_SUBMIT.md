# Phase E1 — top-50 climb submit

**Submitted:** 2026-08-02 · ref **55194786** · kernel v8 · CPU  
**Message:** `E1: K=6 multipost golden + adaptive up/down + residual singles + cap1000 safe0.95 (CPU)`

## Position vs plan

| Metric | Value |
|--------|--------|
| Best before E1 | **65.880** (K=6 multipost, ref 55138995) |
| Rank (stale LB ~Jul 28) | ~843 / ~2480 |
| Top-50 cutoff (then) | ~**92.6** |
| Gap to top 50 | ~**+27** public points |
| Medal math (posts) | need ~mean 0.09×N_eff ≈ 1030 single-eq EXFIL or denser multipost |

## Host A/B evidence (do not re-learn)

| Build | Score | Lesson |
|-------|-------|--------|
| singles N≤750 | 59.805 | baseline |
| multipost **K=6** cap1200 safe0.94 | **65.880** | **best** |
| multipost K=8 cap1200 | 63.045 | K=8 over-hops |
| multipost K=4 cap700 | 55.980 | under-packed |
| singles N=900 | format error | N climb dead |

## E1 recipe (this submit)

| Knob | Golden 65.88 | E1 |
|------|--------------|-----|
| PRIMARY_MULTIPOST_N | 6 | **6** |
| MAX_CANDIDATES | 1200 | **1000** |
| REPLAY_SAFE_FRAC | 0.94 | **0.95** |
| Adaptive-K | down only | **down + up** |
| Multi miss streak | — | → residual **singles** |
| MULTI_REPLAY_PAD | 1.0 | **1.08** |
| Density margin | 1.0 | **0.95** (prefer multi) |

Files: `src/attack.py`, `results/submits/attack_submit_e1.py`, golden backup `results/submits/attack_golden_k6_65.88.py`

## How to read E1 when scored

| E1 score | Next move |
|----------|-----------|
| format / ~0 | Revert to pure golden K=6 65.88 knobs; drop pad/safe changes |
| 63–66 (flat) | Density not the issue; next = gemma post-rate / leaner multi prompt |
| **67–75** | E1 deltas help; next E2 = K=6 + lean frame or better adapt |
| **≥75** | Path open; push posts/sec (still need ~90 for top50) |

## Path to top 50 (after E1)

1. **Public lever only:** successful `http.post`/sec on slower model (gemma).  
2. Do **not** chase K=8 or N=1200 singles.  
3. Ladder: E1 → (if clean) lean multipost prompt / gemma-specific K → private floor last.  
4. Target bands: 75 → 85 → 92+.
