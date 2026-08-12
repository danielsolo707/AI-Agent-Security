# Phase E2 submit

**E1 result:** ref 55194786 → **66.645** (+0.765 vs golden 65.880), clean.

**E2 submitted:** ref **55207374** · kernel v9 · CPU · PENDING  
**Message:** `E2: lean multipost prompt @ K=6 (E1 knobs) posts/sec climb (CPU)`

## One knob
Shorter multipost forge (compact url list, less prefill). K=6 / cap1000 / safe0.95 / adapt / residual unchanged.

## Read when scored
| Score | Next |
|-------|------|
| format / ≪66 | Revert forge to E1 verbose; keep E1 selected |
| 66–67 flat | Lean didn't help; next = cap reclaim 1100–1200 @ E1 forge |
| **≥68** | Lean wins; iterate shorter or gemma-specific |
