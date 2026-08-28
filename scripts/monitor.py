"""Continuous monitor: validator kernel + competition submissions.

Polls until --minutes elapse or the validator completes; prints new scores
and the validation comparison table as they appear.
"""

from __future__ import annotations

import argparse
import csv as _csv_mod  # noqa: F401
import io
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMP = "ai-agent-security-multi-step-tool-attacks"
VALIDATOR = "danielsolo1770/aas-local-validator"
SUBMIT_KERNEL = "danielsolo1770/agent-security-phase0"
STATE = ROOT / "results" / "monitor_state.json"


def log(msg: str) -> None:
    now = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{now}Z] {msg}", flush=True)


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"seen_refs": [], "validator_done": False}


def save_state(st: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st), encoding="utf-8")


def get_submissions() -> list[dict]:
    import csv as _csv

    out = subprocess.run(
        ["kaggle", "competitions", "submissions", "-c", COMP, "--csv"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    )
    rows = []
    for item in _csv.DictReader(io.StringIO(out.stdout)):
        raw_score = (item.get("publicScore") or "").strip()
        try:
            score = float(raw_score) if raw_score else None
        except ValueError:
            score = None
        status = str(item.get("status") or "")
        rows.append(
            {
                "ref": int(item["ref"]) if item.get("ref", "").isdigit() else 0,
                "date": str(item.get("date") or "")[:10],
                "score": score,
                "status": status,
                "desc": str(item.get("desc") or "")[:60],
            }
        )
    return rows


def check_submissions(st: dict) -> None:
    try:
        rows = get_submissions()
    except Exception as exc:
        log(f"submissions fetch error: {exc}")
        return
    seen = set(st.get("seen_refs", []))
    fresh_best = None
    for r in rows:
        if r["ref"] not in seen:
            seen.add(r["ref"])
            tag = f"{r['score']:.3f}" if r["score"] is not None else "pending"
            log(f"sub {r['ref']}: {tag:>8}  {r['desc']}")
            if r["score"] is not None and (fresh_best is None or r["score"] > fresh_best):
                fresh_best = r["score"]
    st["seen_refs"] = sorted(seen)[-80:]
    scores = [r["score"] for r in rows if r["score"] is not None]
    if scores:
        st["best"] = max(scores)
        log(f"best public now: {max(scores):.3f}")


def check_validator(st: dict) -> bool:
    if st.get("validator_done"):
        return True
    out = subprocess.run(
        ["kaggle", "kernels", "status", VALIDATOR],
        capture_output=True,
        text=True,
        timeout=120,
    ).stdout
    log("validator: " + out.strip().splitlines()[-1] if out.strip() else "no status")
    if "COMPLETE" in out:
        st["validator_done"] = True
        return True
    if "ERROR" in out or "CANCEL" in out:
        st["validator_done"] = True
        st["validator_error"] = True
        log("VALIDATOR FAILED")
        return True
    return False


def fetch_validator_results() -> bool:
    dest = ROOT / "results" / "local_validation"
    dest.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    tok_file = Path.home() / ".kaggle" / "access_token"
    if tok_file.exists():
        env["KAGGLE_API_TOKEN"] = tok_file.read_text(encoding="utf-8").strip()
    try:
        p = subprocess.run(
            ["kaggle", "kernels", "output", VALIDATOR, "-p", str(dest), "-o"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=600,
        )
    except Exception as exc:
        log(f"kernels_output failed: {exc}")
        return False
    out = ((p.stdout or "") + (p.stderr or "")).strip()
    if out:
        log("kernels_output: " + out.splitlines()[-1])
    summary = dest / "validation_summary.json"
    if not summary.exists():
        log("no validation_summary.json in output")
        return False
    data = json.loads(summary.read_text(encoding="utf-8"))
    log("=== VALIDATION RESULTS ===")
    for r in data:
        log(json.dumps(r))
    nb = next(dest.glob("local_validation.ipynb"), None)
    if nb is not None:
        text = nb.read_text(encoding="utf-8")
        marker = "=== COMPARISON ==="
        if marker in text:
            tail = text.split(marker, 1)[1][:2000]
            log("comparison block found in notebook output:")
            for line in tail.split("\\n")[:12]:
                if line.strip():
                    log(line.strip()[:160])
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--minutes", type=float, default=22.0)
    parser.add_argument("--interval-s", type=int, default=90)
    args = parser.parse_args()

    deadline = time.monotonic() + args.minutes * 60
    st = load_state()
    log(f"monitor start (for {args.minutes:.0f} min)")
    while time.monotonic() < deadline:
        done = check_validator(st)
        if done and not st.get("results_fetched"):
            time.sleep(30)
            if fetch_validator_results():
                st["results_fetched"] = True
            else:
                time.sleep(60)
                if fetch_validator_results():
                    st["results_fetched"] = True
                else:
                    log("fetch failed — will retry next cycle")
                    st["validator_done"] = False
        check_submissions(st)
        save_state(st)
        if st.get("validator_done") and args.minutes <= 0:
            break
        remaining = deadline - time.monotonic()
        time.sleep(min(args.interval_s, max(15.0, remaining)))
    log("monitor window ended")


if __name__ == "__main__":
    sys.exit(main())
