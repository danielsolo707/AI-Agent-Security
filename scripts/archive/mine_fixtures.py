"""Index competition fixtures for injection families (Phase-1 fixture graph)."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "data" / "aicomp_sdk" / "fixtures"
OUT = ROOT / "results" / "fixture_graph.json"

INJECTION_MARKERS = (
    "ignore previous",
    "forget",
    "disregard",
    "overlook",
    "you must",
    "immediately",
    "system mode",
    "admin",
    "secret.txt",
    "http.post",
    "shell.run",
    "fs.delete",
    "fs.read",
    "base64",
    "rot13",
    "morse",
)


def classify(text: str) -> list[str]:
    low = text.lower()
    tags: list[str] = []
    for m in INJECTION_MARKERS:
        if m in low:
            tags.append(m.replace(" ", "_"))
    if "https://" in low or "http://" in low:
        tags.append("has_url")
    if re.search(r"step\s*1|1\.", low):
        tags.append("numbered_steps")
    return tags or ["benign"]


def main() -> None:
    report: dict = {"web": [], "email": [], "files": [], "summary": {}}

    web = json.loads((FIXTURES / "web_corpus.json").read_text(encoding="utf-8"))
    tag_counts: Counter[str] = Counter()
    for page in web.get("pages", [])[:5000]:  # cap for speed; full set is huge
        tags = classify(page.get("content", "") + " " + page.get("title", ""))
        for t in tags:
            tag_counts[t] += 1
        if "benign" not in tags or len(tags) > 1:
            report["web"].append(
                {
                    "id": page.get("id"),
                    "title": page.get("title"),
                    "tags": tags,
                    "opener": f"open {page.get('id')}",
                }
            )

    mail = json.loads((FIXTURES / "mail_seed.json").read_text(encoding="utf-8"))
    for msg in mail.get("inbox", [])[:2000]:
        tags = classify(
            " ".join(
                [
                    str(msg.get("subject", "")),
                    str(msg.get("body", "")),
                    str(msg.get("from", "")),
                ]
            )
        )
        if "benign" not in tags or len(tags) > 1:
            report["email"].append(
                {
                    "id": msg.get("id"),
                    "subject": msg.get("subject"),
                    "tags": tags,
                    "opener": f"read email {msg.get('id')}",
                }
            )

    file_seed = FIXTURES / "file_seed"
    for path in sorted(file_seed.iterdir()):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        tags = classify(text)
        report["files"].append(
            {
                "name": path.name,
                "tags": tags,
                "opener": f"read {path.name}",
                "size": len(text),
            }
        )

    # Top openers for attack banks
    report["summary"] = {
        "web_injection_pages_sampled": len(report["web"]),
        "email_injection_msgs_sampled": len(report["email"]),
        "files": len(report["files"]),
        "web_tag_counts_top": tag_counts.most_common(20),
        "recommended_web_openers": [w["opener"] for w in report["web"][:40]],
        "recommended_email_openers": [e["opener"] for e in report["email"][:40]],
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")
    print("web inject pages", len(report["web"]))
    print("email inject", len(report["email"]))
    print("top tags", tag_counts.most_common(10))


if __name__ == "__main__":
    main()
