"""Build a Kaggle competition notebook that embeds src/attack.py and serves JED."""

from __future__ import annotations

import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATTACK = ROOT / "src" / "attack.py"
OUT_DIR = ROOT / "notebooks" / "submit_kernel"
NB_NAME = "agent-security-phase0.ipynb"
KERNEL_ID = "danielsolo1770/agent-security-phase0"


def main() -> None:
    attack_text = ATTACK.read_text(encoding="utf-8")
    b64 = base64.b64encode(attack_text.encode("utf-8")).decode("ascii")

    setup_cell = """import sys, os, glob, base64
from pathlib import Path

sys.argv = [sys.argv[0]]

for candidate in glob.glob('/kaggle/input/**/kaggle_evaluation', recursive=True):
    dataset_root = str(Path(candidate).parent)
    if dataset_root not in sys.path:
        sys.path.insert(0, dataset_root)
    print(f'Dataset root: {dataset_root}')
    break

print('Setup complete')
"""

    write_cell = f"""import base64
from pathlib import Path

ATTACK_PY_B64 = \"\"\"{b64}\"\"\"

attack_path = Path('/kaggle/working/attack.py')
attack_path.write_bytes(base64.b64decode(ATTACK_PY_B64))
print(f'Wrote {{attack_path}} ({{attack_path.stat().st_size}} bytes)')

src = attack_path.read_text(encoding='utf-8')
assert 'class AttackAlgorithm' in src
print('AttackAlgorithm present: OK')
"""

    serve_cell = """from pathlib import Path

placeholder = (
    'Id,Score\\n'
    'gpt_oss_public,0.0\\n'
    'gpt_oss_private,0.0\\n'
    'gemma_public,0.0\\n'
    'gemma_private,0.0\\n'
)
(Path('/kaggle/working') / 'submission.csv').write_text(placeholder)
print('submission.csv placeholder written')

from kaggle_evaluation.jed_attack_134815.jed_attack_inference_server import JEDAttackInferenceServer
print('Starting JEDAttackInferenceServer...')
JEDAttackInferenceServer().serve()
"""

    nb = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.10.0"},
        },
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# AI Agent Security — DanielEmpire Phase-0 Attack\n",
                    "\n",
                    "Portfolio + Go-Explore multi-step tool attack.\n",
                    "Writes `attack.py` then serves the JED inference endpoint.\n",
                ],
            },
            {
                "cell_type": "code",
                "metadata": {},
                "execution_count": None,
                "outputs": [],
                "source": setup_cell.splitlines(keepends=True),
            },
            {
                "cell_type": "code",
                "metadata": {},
                "execution_count": None,
                "outputs": [],
                "source": write_cell.splitlines(keepends=True),
            },
            {
                "cell_type": "code",
                "metadata": {},
                "execution_count": None,
                "outputs": [],
                "source": serve_cell.splitlines(keepends=True),
            },
        ],
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    nb_path = OUT_DIR / NB_NAME
    nb_path.write_text(json.dumps(nb, indent=1), encoding="utf-8")

    # GPU: P100 often rejected; T4 used by many public high-score notebooks.
    # KAGGLE_ENABLE_GPU=1 and optional KAGGLE_GPU_SHAPE=NvidiaTeslaT4
    import os

    use_gpu = os.environ.get("KAGGLE_ENABLE_GPU", "").strip() in ("1", "true", "True", "yes")
    gpu_shape = os.environ.get("KAGGLE_GPU_SHAPE", "NvidiaTeslaT4").strip() or "NvidiaTeslaT4"
    meta = {
        "id": KERNEL_ID,
        "title": "agent-security-phase0",
        "code_file": NB_NAME,
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": use_gpu,
        "enable_tpu": False,
        "enable_internet": False,
        "keywords": ["agent-security", "red-team"],
        "dataset_sources": [],
        "kernel_sources": [],
        "competition_sources": ["ai-agent-security-multi-step-tool-attacks"],
        "model_sources": [],
    }
    if use_gpu:
        meta["machine_shape"] = gpu_shape
    (OUT_DIR / "kernel-metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"Wrote {nb_path} ({nb_path.stat().st_size} bytes)")
    print(f"Kernel id: {KERNEL_ID}")
    print(f"Embedded attack.py: {len(attack_text)} bytes")


if __name__ == "__main__":
    main()
