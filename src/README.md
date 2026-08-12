# Attack sources

| File | Role |
|------|------|
| `attack.py` | **Active** — copied into the Kaggle kernel |
| `attack_e9.py` | E9 DensifySafe (fire-gate + REPLAY_SAFE 1.005) |
| `attack_e7.py` | **Best scored** golden (87.840 public) |
| `archive/` | Older experiments (E5–E8 backups, early submits) |

Promote a golden to active:

```powershell
Copy-Item src\attack_e7.py src\attack.py -Force
python scripts\build_kaggle_kernel.py
```
