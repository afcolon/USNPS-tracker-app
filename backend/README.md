# Backend

FastAPI app + recommendation engine (later phases). See [../docs/spec.md](../docs/spec.md).

## Setup

```bash
cd backend
uv sync
cp .env.example .env
uv run uvicorn app.main:app --reload
```

Requires Postgres running (see repo root `docker-compose.yml`).

## Commands

```bash
uv run uvicorn app.main:app --reload   # dev server (http://localhost:8000)
uv run pytest                          # tests
uv run ruff check .                    # lint
uv run ruff format .                   # format
```
