"""Check whether Kaggle submission ref 55387090 (E6) has a public score yet."""
import json
import subprocess
import sys

TOKEN = open(r"C:\Users\ASUS\.kaggle\access_token").read().strip()
TARGET_REF = 55387090
URL = "https://api.kaggle.com/v1/competitions/submissions/list/ai-agent-security-multi-step-tool-attacks"

try:
    out = subprocess.run(
        ["curl", "-s", "-m", "40", "-H", f"Authorization: Bearer {TOKEN}", URL],
        capture_output=True,
        text=True,
        timeout=60,
    ).stdout
    subs = json.loads(out)
except Exception as exc:
    print(f"E6 score check error: {exc}")
    sys.exit(0)

hits = [s for s in subs if s.get("ref") == TARGET_REF]
if not hits:
    print("E6 submission (55387090) not found in submission list yet.")
    sys.exit(0)

s = hits[0]
status = s.get("status")
score = s.get("publicScore")
if not score and status not in ("pending", "processing", "queued", "running"):
    score = "(no score yet)"

if status in ("error", "failed") or (score and status == "error"):
    # errored-but-scored submissions still carry a public score in this comp
    print(f"E6 (55387090) status={status} ")
    sys.exit(0)

if score:
    print(f"E6 (55387090) SCORED: public={score} (status={status})")
else:
    # still running — nothing to report yet (stay silent per watchdog pattern)
    pass