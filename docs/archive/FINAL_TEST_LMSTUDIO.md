# Final test protocol — LM Studio (gpt-oss + Gemma only)

**Policy:** Do **not** use these models during intermediate development.  
Use **DeepSeek-v4-flash** (`.env`) for day-to-day fire-rate / fill tests.  
Use **LM Studio local models only for the final validation gate** before a high-stakes Kaggle push.

## Models on disk

Path: `C:\Users\ASUS\.lmstudio\models\lmstudio-community`

| Folder | Competition relevance |
|--------|------------------------|
| `gpt-oss-20b-GGUF` | Matches Kaggle target **gpt_oss** family |
| `gemma-4-26B` | Matches Kaggle target **Gemma 4** family |
| Other (Qwen, ZAYA, …) | **Out of scope** for final test |

## Before final test

1. Open **LM Studio**
2. Load **one** model at a time (GPU memory):
   - First: `gpt-oss-20b` GGUF
   - Then: `gemma-4-26B`
3. Start **Local Server** (OpenAI-compatible), default `http://127.0.0.1:1234/v1`
4. Confirm: `GET http://127.0.0.1:1234/v1/models` lists the loaded model

## Final test commands (when we reach that gate)

```powershell
$env:PYTHONPATH = "$((Resolve-Path data).Path);$((Resolve-Path src).Path);$((Resolve-Path scripts).Path)"
$env:LMSTUDIO_BASE_URL = "http://127.0.0.1:1234/v1"
# Optional: pin model id from /v1/models
# $env:LMSTUDIO_MODEL = "..."

# Fire-rate on current templates (script to be added in Part A/B)
python scripts/lmstudio_fire_rate.py 8

# Short live-fill throughput (e.g. 120s)
python scripts/lmstudio_live_fill.py --budget-s 120
```

**Pass criteria (suggested):**

| Check | Pass |
|-------|------|
| EXFIL fire-rate verbose template | ≥ 70% on **both** models |
| Mean latency | Recorded (drives margin / N) |
| Live-fill produces validated candidates | > 0 under Optimal |
| No tool-name / API errors | Clean logs |
| Replay-safe fill does not return empty fallback only | Real validates, not blind FALLBACK_N |

## What final test is **not**

- Not a substitute for Kaggle private guardrail  
- Not a full 9000s gen + 9000s replay (optional long run later)  
- Not using DeepSeek in the same process as LM Studio (one blue agent at a time)

## Implementation note

Intermediate work continues with DeepSeek only.  
LM Studio client scripts are added when Part A/B scaffolding is ready, but **invoked only at final gate** unless you explicitly ask earlier.
