# AI Agent Security — Multi-Step Tool Attacks

Private working repo for the Kaggle Featured competition  
**[AI Agent Security – Multi-Step Tool Attacks](https://www.kaggle.com/competitions/ai-agent-security-multi-step-tool-attacks)**  
($50k · deadline 2026-09-01).

Team: **Daniel solo** (`danielsolo1770`)

---

## Status (2026-08-27)

| | |
|--|--|
| **Best live public** | **🏆 90.765 (E18h GPU re-roll)** |
| **Rank** | #346 / 4132 · top-50 cutoff 107.570 (gap +16.8) · top-100 cutoff 98.910 (gap +8.15) |
| **Active code** | `src/attack.py` (= E18 golden, geometry FROZEN) |
| **E23 StackHop** | `src/attack_e23_stackturn.py` — additive multi-hop family (burst3/forge2/forge3), validator v13 A/B in flight |
| **In flight** | E18q re-roll ref 55821012 · validator v13 (T4) golden vs E23 |
| **🚨 KEY RULES** | **Always push T4 (`machine_shape: NvidiaTeslaT4`)** · kernels push needs `KAGGLE_API_TOKEN` from `~/.kaggle/access_token` |

Deadline Sep 1. 5 subs/day. Dashboard: `python scripts/daily_status.py --log` ·
Today: `results/daily_status_2026-08-27.md` · Strategy: `docs/STRATEGY_TOP50.md`.
SDK ground truth (2026-08-27 audit): EXFIL fires per post event (no dedup); UTA
stacking is DEAD on public Optimal (guardrail 5-event window ⊃ predicate 2-event
window); `_host()` aliases at i + 26³.

Full narrative: [`docs/SUBMISSION_JOURNEY_LOG.md`](docs/SUBMISSION_JOURNEY_LOG.md)

---

## Layout

```
AI-Agent-Security/
├── src/
│   ├── attack.py            # ACTIVE kernel algorithm (E18 golden, frozen)
│   ├── attack_e18.py        # frozen E18 golden (89.820)
│   ├── attack_e14.py        # selected golden (88.605)
│   ├── attack_e11.py        # previous best (88.515)
│   ├── attack_e15.py        # frozen E15 snapshot
│   └── archive/             # E5–E13 and older
├── scripts/
│   ├── build_kaggle_kernel.py
│   ├── kaggle_submit.py
│   ├── local_eval.py
│   ├── package_submission.py
│   └── archive/             # one-off benches
├── notebooks/submit_kernel/ # Kaggle notebook (embeds attack.py)
├── results/
│   ├── submissions/         # E1–E15 submit notes
│   ├── intel/               # forum / notebooks / repo research
│   ├── local/               # local eval dumps
│   └── archive/submits/     # frozen attack.py copies
├── docs/
│   ├── SUBMISSION_JOURNEY_LOG.md
│   └── archive/             # stale plans and benches
├── data/                    # aicomp_sdk + kaggle_evaluation
├── configs/
└── tests/
```

---

## Score ladder (post Aug-7 evaluator refresh)

| Phase | Public | Strategy |
|-------|-------:|----------|
| E6 | 85.275 | N32 + validation-fill |
| E7 | 87.840 | multi-turn bank + singles |
| E8 | 82.530 | MsgStack regression (false-fire) |
| E9 | 85.410 | DensifySafe regression vs E7 |
| E10 | 87.795 | GoldenTail ≈ E7 |
| **E11** | **88.515** | FastFill FrameForge — **best live** |
| E12 | 78.750 | density lost on host |
| E13 | 83.250 | SoloReturn regression |
| **E14** | **88.605** | Forge1 — **best live**, still the singles wall |
| E15 | 87.705 | GemmaForge — screen poison |
| E16 | 62.275 | StopFast — split/filled-forge collapsed |
| E17 | 80.145 | E14Clean p70 overpack |
| E18 | 89.820 | RowLock +1.215  |
| E19 | 82.440 | RowLock+ REPLAY_SAFE 0.992 tail 0.11 — regression, reverted |
| E18b | 88.155 | golden re-roll CPU — variance band 88.2–89.8 confirmed |
| E20 | 81.045 | LeanProbe probe trim — regression, geometry now FROZEN |
| E18c/d/e | 87.3/87.1/85.8 | CPU re-rolls — CPU path retired |
| **E18f/g/h/i** | 89.2/**90.765**/89.7/89.1 | **T4 GPU era — E18h = new best, first 90+** |

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
