# Phase E3 submit (dimong4 hybrid)

**Ref:** **55207650** · kernel **v10** · **CPU only** · PENDING  
**Message:** `E3: dimong4 hybrid BURST=2 slow-MULTI=4 frame-split replay_safe0.97 hard2000 (CPU)`

## Intel applied
From `dimong4/ai-agent-security` (+ public 79–86 frame cluster notes):

| Knob | E1 multi-primary | E3 hybrid |
|------|------------------|-----------|
| Fast path | multi K=6 | **BURST_K=2** verbose |
| Slow path | multi K=6 | **Harmony multipost K=4** only |
| Routing | bake-off multi vs single | **latency split** (8 classify) |
| Cap | 1000 | **HARD_N_CAP 2000** (replay stop) |
| Replay safe | 0.95 | **0.97** |
| Multi pad | 1.08 global | **1.10** on multi only |

## Files
- `src/attack.py`
- `results/submits/attack_submit_e3.py`
- prior: `results/submits/attack_submit_e2_pre_e3.py`

## How to read score
| Score | Next |
|-------|------|
| format / ≪66 | Revert E1 66.645 selected |
| 66–72 | Partial hybrid; tune BURST/K or threshold |
| **72–86** | Hybrid works; iterate pad/cap |
| ≥90 | top-50 path open |
