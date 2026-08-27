"""Generate notebooks/local_validation/local_validation.py (compact script form).

Embeds gzip+base64 of src/attack.py and src/attack_e22_compact.py, chunked
across short lines so the script survives copy/paste through tool calls.
"""

import base64
import gzip
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
g = (ROOT / "results" / "local_validation" / "attack_v8.gz64").read_text().strip()
c = (ROOT / "results" / "local_validation" / "attack_e22_compact_v8.gz64").read_text().strip()


def chunk(s: str, n: int = 96) -> str:
    return "\n".join('    "%s"' % x for x in textwrap.wrap(s, n))


TEMPLATE = '''import os, sys, json, time, glob, gc, base64, gzip, importlib.util, subprocess
from pathlib import Path

sys.argv = [sys.argv[0]]
WORK = Path('/kaggle/working')
WORK.mkdir(exist_ok=True)

comp_dir = None
for c_ in glob.glob('/kaggle/input/**/aicomp_sdk', recursive=True):
    p = Path(c_).parent
    if (p / 'kaggle_evaluation').exists():
        comp_dir = p
        break
assert comp_dir, 'competition bundle not found'
sys.path.insert(0, str(comp_dir))

ggufs = glob.glob('/kaggle/input/**/*.gguf', recursive=True)
gpt_paths = [p for p in ggufs if 'gpt-oss' in p.lower()]
gemma_paths = [p for p in ggufs if 'gemma' in p.lower()]
print('gpt:', gpt_paths)
print('gemma:', gemma_paths)
assert gpt_paths, 'no gpt-oss gguf'
GEMMA_OK = bool(gemma_paths)
os.environ['GPT_OSS_MODEL_PATH'] = gpt_paths[0]
os.environ['GEMMA_MODEL_PATH'] = gemma_paths[0] if GEMMA_OK else ''
os.environ['PYTHONUTF8'] = '1'

if importlib.util.find_spec('llama_cpp') is None:
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--no-cache-dir',
        'llama-cpp-python',
        '--extra-index-url', 'https://abetlen.github.io/llama-cpp-python/whl/cu124'], check=True)

GOLDEN_GZ64 = (
__GOLDEN__
)
CAND_GZ64 = (
__CAND__
)
golden_path = WORK / 'attack_golden.py'
cand_path = WORK / 'attack_candidate.py'
golden_path.write_bytes(gzip.decompress(base64.b64decode(GOLDEN_GZ64)))
cand_path.write_bytes(gzip.decompress(base64.b64decode(CAND_GZ64)))
print('wrote', golden_path.stat().st_size, cand_path.stat().st_size)

from kaggle_evaluation.jed_attack_134815 import jed_attack_gateway as gw
from kaggle_evaluation.jed_attack_134815.gguf_model_server import GgufModelServer
from kaggle_evaluation.jed_attack_134815 import gpt_oss_model_server, gemma_model_server
from aicomp_sdk.core.env.api import EnvSelection
from aicomp_sdk.evaluation.runner import evaluate_redteam
from aicomp_sdk.evaluation.diagnostics import RunDiagnostics, EvaluatorVerbosity

SEED = int(gw.ATTACK_SEED)
SPECS = {'gpt_oss': gpt_oss_model_server.SPEC, 'gemma': gemma_model_server.SPEC}


def load_attack(path):
    spec = importlib.util.spec_from_file_location('atk_' + path.stem, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.AttackAlgorithm


def run_eval(model_name, attack_path, budget_s):
    server = GgufModelServer(SPECS[model_name])
    print('loading %s ...' % model_name, flush=True)
    t0 = time.time()
    server.load_model()
    print('%s loaded in %.0fs' % (model_name, time.time() - t0), flush=True)
    art = WORK / 'artifacts'
    art.mkdir(exist_ok=True)
    tag = '%s_%s' % (model_name, attack_path.stem)
    t0 = time.time()
    with RunDiagnostics(
        EvaluatorVerbosity.PROGRESS,
        transcript_file=art / (tag + '_transcript.log'),
        event_log_file=art / (tag + '_framework.jsonl'),
        agent_debug_file=art / (tag + '_agent-debug.jsonl'),
    ):
        execution = evaluate_redteam(
            load_attack(attack_path),
            budget_s=budget_s,
            agent_factory=lambda: server._load_agent(),
            agent_label=model_name + '_gguf',
            env_selection=EnvSelection.GYM,
            fixtures_dir=comp_dir / 'aicomp_sdk' / 'fixtures',
            attack_env_seed=SEED,
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


BUDGET_S = int(os.environ.get('LOCAL_BUDGET_S', '1800'))
REPLAY_FRACTION = float(os.environ.get('LOCAL_REPLAY_FRACTION', '0.55'))
os.environ.setdefault('LOCAL_REPLAY_BUDGET_S', str(BUDGET_S * REPLAY_FRACTION))
MODELS = ['gpt_oss'] + (['gemma'] if GEMMA_OK else [])
results = []
errors = []
for cfg_path in (golden_path, cand_path):
    for model in MODELS:
        try:
            results.append(run_eval(model, cfg_path, BUDGET_S))
        except Exception as e:
            msg = 'EVAL_FAIL %s %s: %r' % (cfg_path.stem, model, e)
            print(msg, flush=True)
            errors.append(msg)
print('EVAL_ERRORS:', len(errors), flush=True)

print()
print('=== COMPARISON ===')
by = {(r['config'], r['model']): r for r in results}
for cfg in sorted({r['config'] for r in results}):
    gpt = by.get((cfg, 'gpt_oss'), {})
    gem = by.get((cfg, 'gemma'), {})
    line = '%-24s gpt_oss=%7.2f (find %s, cells %s)' % (
        cfg, gpt.get('score') or 0, gpt.get('findings'), gpt.get('unique_cells'))
    if GEMMA_OK:
        mean = ((gpt.get('score') or 0) + (gem.get('score') or 0)) / 2
        line += '  gemma=%7.2f  mean=%7.2f' % (gem.get('score') or 0, mean)
    print(line)

(WORK / 'validation_summary.json').write_text(json.dumps(results, indent=2))
print('saved validation_summary.json')
'''

script = TEMPLATE.replace("__GOLDEN__", chunk(g)).replace("__CAND__", chunk(c))
out = ROOT / "notebooks" / "local_validation" / "local_validation.py"
out.write_text(script, encoding="utf-8")
compile(script, str(out), "exec")
print("script OK:", out, len(script), "chars,", script.count("\n"), "lines")
