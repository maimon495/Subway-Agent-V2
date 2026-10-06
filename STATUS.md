# Status — Subway-Agent-V2

_Updated 2026-10-06._

**Active — revived 2026-10-06.** Earlier handoff (2026-10-01) called this superseded by
`maimon495/subway-agent`; that was wrong — the project continues here.

## Where it stands
- Last feature work 2026-02-01 (added Brooklyn, Queens, Bronx stations).
- Branch `personality/Intro`: one unmerged commit (prompt changes). `expanded-stations`
  is fully merged.
- Not known to be deployed anywhere.

## Known issues
- Model `llama-3.3-70b-versatile` is hardcoded in `src/agent/agent.py`; Groq has
  withdrawn it (see `subway-agent` STATUS), so the agent likely fails until changed.
- `app.py` falls back to a hardcoded default `API_KEY`; it is in git history, so treat
  it as exposed and require the env var.
- Conversation history is one module-level list — all web users share it.
- API key is passed as a `?key=` query param (leaks into logs/history).
- No tests, no README. `fastapi`/`uvicorn`/`jinja2` missing from `requirements.txt`;
  stray empty `package-lock.json`.

## Secrets
- `GROQ_API_KEY` — `.env` locally (see `.env.example`); never committed.
- `API_KEY` — web app access key; env var only.
