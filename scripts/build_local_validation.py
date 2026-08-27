"""Build the offline local-validation notebook (Kaggle T4, GGUF models).

Embeds two attack variants (golden E18 from src/attack.py and candidate E22),
runs SDK evaluate_redteam per (model, config), and prints a comparison table.
Push with: kaggle kernels push -p notebooks/local_validation
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "notebooks" / "local_validation"
NB_NAME = "local_validation.ipynb"
KERNEL_ID = "danielsolo1770/aas-local-validator"

GOLDEN = ROOT / "src" / "attack.py"
CANDIDATE = ROOT / "src" / "attack_e22_compact.py"


def b64(path: Path) -> str:
    return base64.b64encode(path.read_text(encoding="utf-8").encode("utf-8")).decode("ascii")


SETUP_CELL = """import os, sys, json, time, glob, gc, base64, importlib.util
from pathlib import Path

sys.argv = [sys.argv[0]]

comp_dir = None
for c in glob.glob('/kaggle/input/**/aicomp_sdk', recursive=True):
    p = Path(c).parent
    if (p / 'kaggle_evaluation').exists():
        comp_dir = p
        break
assert comp_dir, 'competition bundle not found'
sys.path.insert(0, str(comp_dir))

ggufs = glob.glob('/kaggle/input/**/*.gguf', recursive=True)
gpt_paths = [p for p in ggufs if 'gpt-oss' in p.lower()]
gemma_paths = [p for p in ggufs if 'gemma' in p.lower()]
if not gpt_paths or not gemma_paths:
    print('!! mounted inputs:')
    for p in glob.glob('/kaggle/input/*/*', recursive=False):
        print('   ', p)
print('gpt_oss ggufs:', gpt_paths)
print('gemma ggufs:', gemma_paths)
assert gpt_paths, 'no gpt-oss gguf mounted'
GEMMA_OK = bool(gemma_paths)
os.environ['GPT_OSS_MODEL_PATH'] = gpt_paths[0]
os.environ['GEMMA_MODEL_PATH'] = gemma_paths[0] if GEMMA_OK else ''
os.environ['PYTHONUTF8'] = '1'
print('comp:', comp_dir)

from kaggle_evaluation.jed_attack_134815 import jed_attack_gateway as gw
CFG = {
    'budget_full_s': float(gw.DEFAULT_BUDGET_S),
    'max_tool_hops': int(gw.DEFAULT_MAX_TOOL_HOPS),
    'seed': int(gw.ATTACK_SEED),
}
print(json.dumps(CFG))
"""

INSTALL_CELL = """import importlib.util, subprocess, sys

if importlib.util.find_spec('llama_cpp') is None:
    subprocess.run([
        sys.executable, '-m', 'pip', 'install', '-q', '--no-cache-dir',
        'llama-cpp-python',
        '--extra-index-url', 'https://abetlen.github.io/llama-cpp-python/whl/cu124',
    ], check=True)
print('llama-cpp-python ready')
"""

WRITE_CELL = """import base64
from pathlib import Path

WORK = Path('/kaggle/working')
WORK.mkdir(exist_ok=True)

GOLDEN_B64 = "__GOLDEN__"
CAND_B64 = "__CAND__"

golden_path = WORK / 'attack_golden.py'
cand_path = WORK / 'attack_candidate.py'
golden_path.write_bytes(base64.b64decode(GOLDEN_B64))
cand_path.write_bytes(base64.b64decode(CAND_B64))
print('wrote', golden_path.stat().st_size, cand_path.stat().st_size)
"""


def write_cell() -> str:
    return WRITE_CELL.replace("__GOLDEN__", b64(GOLDEN)).replace("__CAND__", b64(CANDIDATE))


EVALDEF_CELL = """import importlib.util
from kaggle_evaluation.jed_attack_134815.gguf_model_server import GgufModelServer
from kaggle_evaluation.jed_attack_134815 import gpt_oss_model_server, gemma_model_server
from aicomp_sdk.core.env.api import EnvSelection
from aicomp_sdk.evaluation.runner import evaluate_redteam
from aicomp_sdk.evaluation.diagnostics import RunDiagnostics, EvaluatorVerbosity

SPECS = {'gpt_oss': gpt_oss_model_server.SPEC, 'gemma': gemma_model_server.SPEC}


def load_attack(path):
    spec = importlib.util.spec_from_file_location('atk_' + path.stem, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.AttackAlgorithm


def run_eval(model_name, attack_path, budget_s):
    server = GgufModelServer(SPECS[model_name])
    print(f'loading {model_name} ...', flush=True)
    t0 = time.time()
    server.load_model()
    print(f'{model_name} loaded in {time.time()-t0:.0f}s', flush=True)
    agent_factory = lambda: server._load_agent()
    art = WORK / 'artifacts'
    art.mkdir(exist_ok=True)
    tag = f"{model_name}_{attack_path.stem}"
    t0 = time.time()
    with RunDiagnostics(
        EvaluatorVerbosity.PROGRESS,
        transcript_file=art / f'{tag}_transcript.log',
        event_log_file=art / f'{tag}_framework.jsonl',
        agent_debug_file=art / f'{tag}_agent-debug.jsonl',
    ):
        execution = evaluate_redteam(
            load_attack(attack_path),
            budget_s=budget_s,
            agent_factory=agent_factory,
            agent_label=f'{model_name}_gguf',
            env_selection=EnvSelection.GYM,
            fixtures_dir=comp_dir / 'aicomp_sdk' / 'fixtures',
            attack_env_seed=CFG['seed'],
        )
    a = execution.attack
    summary = {
        'config': attack_path.stem,
        'model': model_name,
        'score': float(a.score),
        'score_raw': float(a.score_raw),
        'findings': int(a.findings_count),
        'unique_cells': int(a.unique_cells),
        'eval_time_s': round(float(a.time_taken), 1),
        'wall_s': round(time.time() - t0, 1),
    }
    print(json.dumps(summary), flush=True)
    try:
        server.unload()
    except Exception as e:
        print('unload err', repr(e))
    gc.collect()
    try:
        import torch
        torch.cuda.empty_cache()
    except Exception:
        pass
    return summary

print('eval harness ready')
"""

RUN_CELL = """BUDGET_S = int(os.environ.get('LOCAL_BUDGET_S', '1800'))
MODELS = ['gpt_oss'] + (['gemma'] if GEMMA_OK else [])
if not GEMMA_OK:
    print('!! gemma model not mounted (terms not accepted?) — running gpt_oss only')
results = []
for cfg_path in (golden_path, cand_path):
    for model in MODELS:
        results.append(run_eval(model, cfg_path, BUDGET_S))

print('\\n=== COMPARISON ===')
by = {(r['config'], r['model']): r for r in results}
for cfg in sorted({r['config'] for r in results}):
    g = by.get((cfg, 'gpt_oss'), {})
    m = by.get((cfg, 'gemma'), {})
    parts = [f"{cfg:<24} gpt_oss={g.get('score'):7.2f} (find {g.get('findings')}, cells {g.get('unique_cells')})"]
    if GEMMA_OK:
        mean = ((g.get('score') or 0) + (m.get('score') or 0)) / 2
        parts.append(f"gemma={m.get('score'):7.2f} (find {m.get('findings')}, cells {m.get('unique_cells')}) mean={mean:7.2f}")
    print(' '.join(parts))

(WORK / 'validation_summary.json').write_text(json.dumps(results, indent=2))
print('saved validation_summary.json')
"""


def cell(source: str, code: bool = True) -> dict:
    out = {
        "cell_type": "code" if code else "markdown",
        "metadata": {},
        "source": source.splitlines(keepends=True),
    }
    if code:
        out["outputs"] = []
        out["execution_count"] = None
    return out


def main() -> None:
    nb = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        },
        "cells": [
            cell("# AAS local validator — golden vs candidate on both target models", False),
            cell(SETUP_CELL),
            cell(INSTALL_CELL),
            cell(write_cell()),
            cell(EVALDEF_CELL),
            cell(RUN_CELL),
        ],
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / NB_NAME).write_text(json.dumps(nb, indent=1), encoding="utf-8")

    meta = {
        "id": KERNEL_ID,
        "title": "aas-local-validator",
        "code_file": NB_NAME,
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": True,
        "enable_tpu": False,
        "enable_internet": True,
        "dataset_sources": [],
        "kernel_sources": [],
        "competition_sources": ["ai-agent-security-multi-step-tool-attacks"],
        "model_sources": [
            "llkh0a/gpt-oss-20b-gguf/PyTorch/default/1",
            "llkh0a/gemma-4-26b-a4b-it-ud-q4-k-m-gguf/PyTorch/default/1",
        ],
        "model_data_sources": [
            "llkh0a/gpt-oss-20b-gguf/PyTorch/default/1",
            "llkh0a/gemma-4-26b-a4b-it-ud-q4-k-m-gguf/PyTorch/default/1",
        ],
    }
    (OUT_DIR / "kernel-metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"wrote {OUT_DIR / NB_NAME}")
    print(f"kernel: {KERNEL_ID}")


if __name__ == "__main__":
    main()
