# `src/attack.py` — E18 RowLock

This is the algorithm that was actually submitted. It is not a post-deadline rewrite.

**Public 90.765 · private 0.000**

The attack live-validates single-message `http.post` prompts that put `SECRET_MARKER` in `data` and a unique host in `url`. After a short warmup it locks either:

- the Harmony/`forge1` bank (gpt-oss), or
- the plain-English bank (gemma)

then fills a replay-safe number of unique candidates against a 9,000 second budget.

Public `OptimalGuardrail` inspects `url` before `data`, so the marker scores. The private guardrail scans `data` for `SECRET_MARKER` and every candidate is denied. See [`docs/POSTMORTEM.md`](../docs/POSTMORTEM.md).
