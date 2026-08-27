"""Insert a GPU-device probe print into notebooks/local_validation/local_validation.py."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "notebooks" / "local_validation" / "local_validation.py"

PROBE = (
    "print('eval harness ready')\n"
    "try:\n"
    "    import torch\n"
    "    print('GPU_DEVICE:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NONE')\n"
    "except Exception as e:\n"
    "    print('gpu probe err', repr(e))\n"
)

src = NB.read_text(encoding="utf-8")
ANCHOR = "print('wrote', golden_path.stat().st_size, cand_path.stat().st_size)"
if "GPU_DEVICE" in src:
    print("probe already present")
elif ANCHOR in src:
    src = src.replace(
        ANCHOR,
        ANCHOR + "\n"
        "try:\n"
        "    import torch\n"
        "    print('GPU_DEVICE:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NONE')\n"
        "except Exception as e:\n"
        "    print('gpu probe err', repr(e))",
        1,
    )
    NB.write_text(src, encoding="utf-8")
    compile(src, str(NB), "exec")
    print("probe inserted + compile OK")
else:
    raise SystemExit("anchor not found: print('wrote', ...)")
