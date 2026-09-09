# Backend

FastAPI app + recommendation engine (later phases). See [../docs/spec.md](../docs/spec.md).

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) — not bundled with Python, install separately:
  - macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh` (or `brew install uv`)
  - Windows: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`

## Setup

```bash
cd backend
uv sync
cp .env.example .env
uv run alembic upgrade head   # creates tables + seeds the single implicit user
uv run uvicorn app.main:app --reload
```

Requires Postgres running (see repo root `docker-compose.yml`). To see all 63 parks in
the passport (rather than an empty list), also run the ingestion script — see
`../ingestion/README.md`.

## Commands

```bash
uv run uvicorn app.main:app --reload   # dev server (http://localhost:8000)
uv run pytest                          # tests
uv run ruff check .                    # lint
uv run ruff format .                   # format
uv run alembic upgrade head            # apply migrations
uv run alembic revision -m "..."       # new migration (hand-write it; autogenerate
                                        # needs a live DB connection to diff against)
```
