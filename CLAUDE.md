# Subway-Agent-V2 — Project Context

MTAGPT: NYC subway chat agent (LangGraph + Groq, FastAPI web chat, CLI, Dockerfile).
**Active** — revived 2026-10-06. A sibling repo, `maimon495/subway-agent` (LIRR,
iOS backend), also exists; this one is maintained separately, not superseded.

## Layout
- `src/agent/` — `agent.py` (ReAct agent), `tools.py` (arrivals, route, alerts), `prompts.py`
- `src/gtfs/client.py` — MTA GTFS-RT fetch + 30s cache
- `src/services/` — arrivals, routing, transfers, alerts, direction parsing
- `src/data/` — hand-coded stations, lines, transfer points
- `app.py` (FastAPI, `/`, `/chat`, `/clear`, `/health`), `main.py` (CLI)

## Run
`pip install -r requirements.txt fastapi uvicorn jinja2`, set `GROQ_API_KEY` (and
`API_KEY` for the web app) in `.env`, then `python main.py` or `uvicorn app:app`.

## Working with Brian
- Work on a feature branch and open a PR; never commit to `main`. Brian merges.
- Do the work end to end. Only hand back secrets, spending, irreversible
  outward-facing actions, and product decisions such as naming.
- Never commit secrets. Where each one lives is listed in STATUS.md.
- Other projects: see `docs/ALL-PROJECTS.md` in `maimon495/DailyGratitudeJournal`.

@STATUS.md
