"""Daily competition status dashboard for Daniel solo."""

from __future__ import annotations

import argparse
import csv
import io
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMP = "ai-agent-security-multi-step-tool-attacks"
TEAM = "Daniel solo"
DEADLINE = datetime(2026, 9, 1, 23, 59, tzinfo=timezone.utc)
MERGER = datetime(2026, 8, 25, 23, 59, tzinfo=timezone.utc)


def _f(value: object) -> float | None:
    try:
        return float(str(value))
    except Exception:
        return None


def get_submissions_api(api: object) -> list[dict]:
    rows = []
    for attr in ("competition_submissions", "competitions_submissions_list"):
        fn = getattr(api, attr, None)
        if fn is None:
            continue
        try:
            raw = fn(competition=COMP)
        except TypeError:
            try:
                raw = fn(id=COMP)
            except Exception:
                continue
        except Exception:
            continue
        for s in raw or []:
            rows.append(
                {
                    "ref": getattr(s, "ref", None),
                    "date": getattr(s, "date", None),
                    "status": str(getattr(s, "status", "")),
                    "score": _f(getattr(s, "public_score", None)),
                    "desc": getattr(s, "description", "") or "",
                }
            )
        if rows:
            return rows
    return []


def get_submissions_cli() -> list[dict]:
    out = subprocess.run(
        ["kaggle", "competitions", "submissions", "-c", COMP, "--csv"],
        capture_output=True,
        text=True,
    ).stdout
    rows = []
    for item in csv.DictReader(io.StringIO(out)):
        rows.append(
            {
                "ref": int(item["ref"]) if item.get("ref") else None,
                "date": item.get("date"),
                "status": item.get("status", ""),
                "score": _f(item.get("publicScore")),
                "desc": item.get("desc", ""),
            }
        )
    return rows


def get_leaderboard_scores() -> list[float]:
    api = None
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi

        api = KaggleApi()
        api.authenticate()
    except Exception:
        pass
    if api is not None:
        for kwargs in ({"page_size": 100}, {}):
            try:
                entries = api.competition_leaderboard_view(COMP, **kwargs)
                scores = [_f(getattr(e, "score", None)) for e in entries]
                found = [s for s in scores if s is not None]
                if len(found) >= 50:
                    return sorted(found, reverse=True)
            except Exception:
                pass
    out = subprocess.run(
        ["kaggle", "competitions", "leaderboard", "-c", COMP, "--show"],
        capture_output=True,
        text=True,
    ).stdout
    scores = []
    for line in out.splitlines():
        parts = line.split()
        if parts and parts[-1].replace(".", "", 1).isdigit():
            v = _f(parts[-1])
            if v is not None:
                scores.append(v)
    return sorted(scores, reverse=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", action="store_true")
    args = parser.parse_args()

    try:
        from kaggle.api.kaggle_api_extended import KaggleApi

        api = KaggleApi()
        api.authenticate()
        subs = get_submissions_api(api)
    except Exception:
        subs = []
    if not subs:
        subs = get_submissions_cli()
    if not subs:
        raise SystemExit("could not fetch submissions")

    now = datetime.now(timezone.utc)
    days_left = (DEADLINE - now).total_seconds() / 86400.0
    merger_left = (MERGER - now).total_seconds() / 86400.0

    complete = [s for s in subs if s["score"] is not None]
    best = max(complete, key=lambda s: s["score"]) if complete else None
    today = now.strftime("%Y-%m-%d")
    today_count = sum(
        1 for s in subs if isinstance(s["date"], datetime) and s["date"].strftime("%Y-%m-%d") == today
    )
    pending = [
        s for s in subs if "PENDING" in s["status"].upper() or "QUEUED" in s["status"].upper()
    ]

    lb = get_leaderboard_scores()
    cutoff50 = lb[49] if len(lb) >= 50 else None
    my_rank = (1 + sum(1 for s in lb if best and s > best["score"])) if best else None

    print("=" * 46)
    print("DANIEL SOLO — DAILY STATUS")
    print("=" * 46)
    if best:
        print(f"best public : {best['score']:.3f}  (ref {best['ref']})")
        print(f"est. rank   : ~{my_rank}")
    else:
        print("best public : n/a")
    print(f"subs today  : {today_count}/5 (UTC)")
    print(f"in flight   : {len(pending)} pending")
    if cutoff50 is not None and best:
        gap = cutoff50 - best["score"]
        print(f"top-50 cut  : {cutoff50:.3f}   gap: {gap:+.3f}")
    else:
        print(f"top-50 cut  : {cutoff50}")
    print(f"days left   : {days_left:.1f}   merger: {max(0.0, merger_left):.1f}d")
    print("-" * 46)
    for s in subs[:6]:
        score = f"{s['score']:.3f}" if s["score"] is not None else "pending"
        desc = (s["desc"] or "")[:44]
        print(f"  {s['ref']}  {score:>8}  {s['status'][:12]:<12} {desc}")

    if args.log:
        log_path = ROOT / "results" / "daily_log.csv"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        new_file = not log_path.exists()
        with log_path.open("a", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            if new_file:
                writer.writerow(["ts", "best", "cutoff50", "gap", "rank_est", "subs_today"])
            writer.writerow(
                [
                    now.isoformat(timespec="seconds"),
                    f"{best['score']:.3f}" if best else "",
                    f"{cutoff50:.3f}" if cutoff50 else "",
                    f"{cutoff50 - best['score']:.3f}" if cutoff50 and best else "",
                    my_rank if my_rank else "",
                    today_count,
                ]
            )
        print("logged ->", log_path)


if __name__ == "__main__":
    sys.exit(main())
