# Spy Report — Competitive Intelligence Sweep (2026-08-24)

Sources: discussion topics 736246 / 736602, notebooks by llkh0a (425 votes),
mccocoful, dimong4, lopure; leaderboard rank cross-references.

---

## 1. WHO'S WHO near the top (from comment badges)

| Player | Rank | What they said/do |
|---|---:|---|
| Mohammad Shadab Alam (outliar) | **#2** | Local replica: attack ~35x faster on local GPU than Kaggle; env-loading per candidate ~2x slower (WSL). Hedges with "safe second submission". |
| Joseph Adamski | **#30** | Keeps **6 optimized paths tuned to different private-guardrail hypotheses**, picks 2 at end. |
| James Weatherhead | **#47** | Testing **compact prompts / other languages** (Chinese: fewer tokens) to raise replay throughput. Reports scores improving with more compact wording. |
| Yiheng Wang (GM) | #404 | Same notebook resubmitted → totally different scores; local/2xT4 validation ≫ submitted. |
| hengck23 (GM) | #516 | **Only first ~200–250 of his 1000 candidates got scored** (slow multi-message candidates hit replay timeout); ordering matters. |
| mccocoful (Master) | — | Maintains CPU-replica timing theory; built jed-offline wheelhouse. |

## 2. CONFIRMED MECHANICS

1. **Local validation ≈ LB** (llkh0a table): starter scored 0.255 locally
   vs 0.24 on LB. A faithful local evaluator exists:
   - `evaluate_redteam()` from SDK + `GgufModelServer` loading the SAME
     unsloth GGUF quants, budget 9000 s/model, hops 8, seed 123.
   - Runs on a **Kaggle T4** notebook (models attached as datasets).
   - This is higher-fidelity than LM Studio chat-completion benches.
2. **Agent models are loaded in-process at eval time** (`GgufModelServer`).
   Consistent with our A/B finding that the submission worker's accelerator
   affects score (GPU mean ~89.7 vs CPU ~87.1).
3. **Replay truncation is real**: candidates beyond the effective replay
   window never score ⇒ keep validated candidates FIRST (we already do).
4. **Variance is industry-wide** (GMs complaining publicly): our ±1–2 pts
   swings are normal, not a bug in our pipeline.

## 3. WHAT TOP-50 ARE DOING THAT WE ARE NOT

- **Prompt token-compaction experiments** (rank #47): shorter prompt =
  faster replay = more findings inside 9000 s. Live research area.
- **Multi-path private-guardrail hedging** (rank #30): several final
  candidates tuned to different private-guardrail guesses; pick 2 diverse.
- Community suspicion: private guardrail may be **LLM-based maliciousness
  detection** rather than static rules ⇒ SECRET_MARKER-in-data may die on
  private LB; diversity of final picks is the hedge.

## 4. ACTIONABLE FOR US

| # | Action | Cost | Expected |
|---|---|---|---|
| A | Port llkh0a-style **local validator** into our repo (Kaggle T4 interactive, attach llkh0a model datasets + our attack.py) — validates any future knob OFFLINE without burning slots | ~1–2 T4 hours per config | De-risks every future experiment |
| B | Draft **compact-template variants** (incl. minimal-wording + CJK one-liner) and screen them in the local validator; only promote if they beat forge1 raw/s by >5% | validator hours | Possible +5–10% throughput ⇒ +4–9 pts |
| C | Keep GPU re-roll lottery running (proven machine) | slots | best-of-N compounds |
| D | Final selection = two DISTINCT configs (throughput champion + hedge) | free | private-LB insurance |

## 5. NOT WORTH CHASING
- Random-character prompts (GM asked; no evidence of success).
- Copying public multipost/relay notebooks (E3 lesson: ports lose).
- Multi-turn chains (broken Gemma syntax confirmed again by Renee/hengck23).
