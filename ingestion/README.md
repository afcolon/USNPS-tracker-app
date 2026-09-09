# Ingestion

One-off data-loading scripts, run manually and separately from the API (see
[../docs/spec.md](../docs/spec.md) §4.3 — ingestion stays out of the live request path).

This is its own small `uv` project (own `pyproject.toml`/venv), deliberately not sharing
code with `backend/` — see [../docs/phase1-notes.md](../docs/phase1-notes.md) for why.

## Setup

```bash
cd ingestion
uv sync
cp .env.example .env
# edit .env: set NPS_API_KEY (free key: https://www.nps.gov/subjects/developer/api-documentation.htm)
```

Requires Postgres running and migrated (see `../backend/README.md` for `alembic upgrade head`).

## Scripts

```bash
uv run python load_parks.py   # loads the 63 National Parks from the NPS API
```
