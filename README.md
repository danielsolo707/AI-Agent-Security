# AI Agent Security — Multi-Step Tool Attacks

Private working repo for the Kaggle Featured competition  
**[AI Agent Security – Multi-Step Tool Attacks](https://www.kaggle.com/competitions/ai-agent-security-multi-step-tool-attacks)**  
($50k · deadline 2026-09-01).

Team: **Daniel solo** (`danielsolo1770`)

---

## Status (2026-08-12)

| | |
|--|--|
| **Best live public** | **87.840 (E7)** |
| **Rank** | ~#358 / 1170 |
| **Top-100 cutoff** | ~91.6 |
| **Active code** | `src/attack.py` (= **E9 DensifySafe**, pending host score) |
| **Golden to defend** | `src/attack_e7.py` |

Full narrative: [`docs/SUBMISSION_JOURNEY_LOG.md`](docs/SUBMISSION_JOURNEY_LOG.md) · snapshot: [`docs/STATUS_2026-08-12.md`](docs/STATUS_2026-08-12.md)

---

## Layout

```
AI-Agent-Security/
├── src/
│   ├── attack.py          # ACTIVE submission algorithm (E9)
│   ├── attack_e7.py       # Best scored golden (87.840)
│   ├── attack_e9.py       # DensifySafe source
│   └── archive/           # older variants
├── scripts/
│   ├── build_kaggle_kernel.py
│   ├── kaggle_submit.py
│   ├── local_eval.py
│   ├── package_submission.py
│   ├── final_lmstudio_gate.py
│   └── archive/           # one-off benches / overnight jobs
├── notebooks/submit_kernel/   # Kaggle notebook shell (embeds attack.py)
├── results/
│   ├── submissions/       # E1–E9 submit notes
│   └── submits/           # frozen attack.py copies per phase
├── docs/                  # journey, research, status
├── data/                  # competition aicomp_sdk + kaggle_evaluation
├── configs/
└── tests/
```

---

## Score ladder (post Aug-7 evaluator refresh)

| Phase | Public | Strategy |
|-------|-------:|----------|
| E6 | 85.275 | N32 + validation-fill |
| **E7** | **87.840** | multi-turn bank + singles, host raw/s |
| E8 | 82.530 | MsgStack regression (false-fire) |
| E9 | pending | fire-gate + denser replay packing |

Pre-refresh scores (E4 87.75 etc.) are **ERROR** after the host reset.

---

## Local setup

```powershell
# Python 3.11+ recommended
cd AI-Agent-Security

# Competition package (if data/ missing)
kaggle competitions download -c ai-agent-security-multi-step-tool-attacks -p data
# extract aicomp_sdk + kaggle_evaluation into data/

$env:PYTHONPATH = "$((Resolve-Path data).Path);$((Resolve-Path src).Path)"

# Smoke unit tests
python -c "import tests.test_attack_unit as t; [getattr(t,n)() for n in dir(t) if n.startswith('test_')]"

# Optional local eval (deterministic / rules)
python scripts/local_eval.py --budget-s 40 --guardrail rules
```

Kaggle CLI auth: put `kaggle.json` in `%USERPROFILE%\.kaggle\` (gitignored).

---

## Submit to Kaggle

```powershell
# Embed src/attack.py into the notebook and push (T4 GPU recommended)
$env:KAGGLE_ENABLE_GPU = "1"
$env:KAGGLE_GPU_SHAPE = "NvidiaTeslaT4"
python scripts/build_kaggle_kernel.py
kaggle kernels push -p notebooks/submit_kernel

# After kernel COMPLETE, submit (Python 3.12 + kaggle package)
python scripts/kaggle_submit.py "E9: short message"
```

Or use `kaggle.api.competition_submit_code(...)` against kernel `danielsolo1770/agent-security-phase0`.

---

## Strategy notes (public Optimal)

1. High-throughput **SECRET_MARKER** `http.post` to unique hosts beats clever multi-hop under Optimal.
2. Live **raw/s template screen** + **validation-fill** + replay-safe sizing.
3. Only count **real EXFIL** (`raw >= 16`) as fire — avoids false-champion templates (E8 lesson).
4. After Aug-7, replay timeout keeps **partial score** → can pack slightly past old 0.99 cushion.
5. Generation timeout still zeros the run — keep a gen margin.

---

## Private repo

This repo is intended **private**. Do not publish attack sources or competition-derived intel publicly if that conflicts with Kaggle rules or your strategy.

```bash
git init
git add .
git commit -m "Initial private competition workspace (E7 golden, E9 active)"
gh repo create AI-Agent-Security --private --source=. --remote=origin --push
# or: create empty private repo on GitHub, then
# git remote add origin git@github.com:<you>/AI-Agent-Security.git
# git push -u origin main
```
