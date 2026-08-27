# Attack sources

| File | Role |
|------|------|
| `attack.py` | **Active** — embedded in the Kaggle kernel (currently E17) |
| `attack_e14.py` | **Selected golden** — 88.605 public |
| `attack_e11.py` | Previous best — 88.515 public |
| `attack_e15.py` | Frozen E15 snapshot (same family as `attack.py`) |
| `archive/` | Older phases (E5–E13) |

Promote a golden to active:

```powershell
Copy-Item src\attack_e14.py src\attack.py -Force
$env:KAGGLE_ENABLE_GPU = "1"
python scripts\build_kaggle_kernel.py
```
