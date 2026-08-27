import sys, io, traceback
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
try:
    from kaggle.api.kaggle_api_extended import KaggleApi
    from kagglesdk.competitions.types.competition_api_service import ApiGetLeaderboardRequest

    COMP = "ai-agent-security-multi-step-tool-attacks"
    api = KaggleApi()
    api.authenticate()

    rows = []
    token = None
    for _ in range(60):
        with api.build_kaggle_client() as client:
            req = ApiGetLeaderboardRequest()
            req.competition_name = COMP
            api._set_paging(req, 200, token)
            resp = client.competitions.competition_api_client.get_leaderboard(req)
        rows.extend(resp.submissions or [])
        token = resp.next_page_token
        if not token:
            break

    seen = {}
    for r in rows:
        seen[r.team_id] = r
    rows = list(seen.values())
    rows.sort(key=lambda r: -float(r.score or 0))
    n = len(rows)
    print("total teams:", n)
    for rank in (1, 10, 25, 40, 45, 50, 55, 60, 75, 100, 125, 150, 200, 250, 300, 350, 400, 450, 500):
        if rank <= n:
            r = rows[rank - 1]
            print(f"rank {rank:4d} -> {str(r.team_name)[:32]:32s} {r.score}")
    print("TOP50 cutoff:", rows[49].score if n >= 50 else None)
    print("TOP100 cutoff:", rows[99].score if n >= 100 else None)
    for i, r in enumerate(rows):
        name = (r.team_name or "").lower()
        if "daniel" in name or "solo" in name or "1770" in name:
            print("OUR ROW: rank", i + 1, r.team_name, r.score)
except Exception:
    traceback.print_exc()
