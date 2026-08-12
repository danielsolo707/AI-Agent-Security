# Discussion 712642 — host evaluator update FAQ (takeaways)

Source: https://www.kaggle.com/competitions/ai-agent-security-multi-step-tool-attacks/discussion/712642  
Host post by competition team (Owen Vallis et al.), plus community replies.

## Official pipeline (confirmed)

Per model (`gpt_oss`, `gemma`), sequential:

1. **Live exploration** — `AttackAlgorithm.run()` once vs **Public OptimalGuardrail**, budget **9000s**.  
2. **Static replay** — same returned candidates, fresh envs, vs **public + private** guardrails, **9000s each**.  
3. **Global job ceiling 15h** — not extra attack time.  
4. Phase timeout → **fail without score** (fail-fast), not hang until global timeout.  
5. Private LB does **not** re-run `attack.py` — only replay portfolio.  
6. EXFIL scorer: active replay trace + encodings (URL/base64/hex/reverse/separator).  
7. Max **2000** candidates, **32** msgs/chain, **8** hops, **10k** chars/msg.

## Community ops facts (actionable)

| Observation | Implication for us |
|-------------|-------------------|
| N=100 ~2h score; N=400 ~7.5h; N=800+ often **format error** (timeout fail-fast) | Target **safe N ≈ 300–900**, not 2000 |
| ~900 cands/model → score **~81** (post-guardrail update, SECRET_MARKER) | ~0.09/cand still holds |
| Kaggle replay ~**6× slower** than AAS local | Don’t trust raw local proj_9000 |
| LB includes pre-update frozen scores | Public rank ≠ final private fairness |
| Private = static transfer of public-discovered chains | Need payload **diversity** (encodings) not just volume |

## How we already match the FAQ

- Live-fill validated SECRET_MARKER posts under Optimal  
- Replay-safe sizing to avoid phase timeout zeros  
- Early Harmony **frame** on slow models (gpt-oss)  
- No re-run assumption for private  

## Improvements applied after reading this thread

1. **Encoded payload rotation** (base64 / reverse / separator) for private hedge.  
2. **Warmup + fill prefer frame** when latency already high.  
3. **Diversity OFF** by default so we don’t blow replay budget.  
4. **Smaller fallback N** + latency-sized emit.  
5. Document practical N band (300–900) vs HARD_N_CAP 2000.

## Still useful while waiting

- Calibrate hops=1 probe coef on LM Studio (gen speed vs hops=8 replay cost).  
- After first public score: set hard_n_cap / replay_safe_frac from observed N.  
- Optional multipost only if single-post saturates and latency allows.
