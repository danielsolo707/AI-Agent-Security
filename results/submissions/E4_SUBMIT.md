# Phase E4 — N32 open-source port (yw8837)

**Verdict on notebook:** YES — best public baseline we have. Author host scores **88.875 / 86.400**.

**Submitted:** ref **55221895** · kernel **v11** · **T4 GPU accepted** · PENDING  
**Message:** `E4: N32 raw-rate open source port (yw8837 88.875 baseline) 7-template P75 safe0.99 (T4)`

## Method
- Single-post SECRET_MARKER only (not multipost-primary)
- 7 templates + live raw/sec selection
- P75 latency sizing, REPLAY_SAFE=0.99, cap 2000
- Source: discussion 731518 / `results/intel_yw8837/N32_attack.py`

## Files
- `src/attack.py`, `results/submits/attack_submit_e4_n32.py`
- Prior best to protect until E4 scores: E2 **68.625**
