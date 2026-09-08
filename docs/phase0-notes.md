# Phase 0 — Scaffolding Notes

Records decisions and new behaviors introduced while scaffolding, beyond what
`docs/spec.md` §4/§7 already specifies. Spec §7 defines "done" for Phase 0 as:
*"FastAPI app + React app talk to each other; Postgres running in Docker."*
Nothing beyond that minimal wiring was built.

## Decisions made with you (confirmed via prompts)

| Area | Choice | Why |
|---|---|---|
| Python dependency manager | [uv](https://docs.astral.sh/uv/) | Fast, modern, single lockfile, less legacy friction than Poetry |
| Local Docker scope | Postgres only | Backend/frontend run natively (`uvicorn --reload`, `vite dev`) for faster iteration; only the DB is containerized |
| Frontend package manager | npm | Ships with Node, no extra tooling |
| Frontend language | TypeScript | Type safety, pairs with FastAPI's typed OpenAPI schema later |
| Linting/formatting | Set up now, not deferred | — |
| Frontend linter | **oxlint** (not ESLint as originally discussed) | The current `npm create vite@latest -- --template react-ts` scaffold ships with oxlint instead of ESLint by default. Flagged and confirmed with you rather than silently swapping either way. Prettier added alongside it for formatting (oxlint doesn't format). |

## Implementation decisions made without asking (low-stakes, documented here for easy tweaking)

- **Python version:** targeting `>=3.11` (matches the interpreter already on this machine, `3.11.15`). Not pinned to 3.12+ to avoid needing `uv` to download a new interpreter.
- **SQLAlchemy: async, not sync.** Used `sqlalchemy[asyncio]` + `asyncpg` driver, since FastAPI is async-native and this is the common modern pairing. Easy to change later if it becomes friction.
- **Alembic not yet initialized.** The spec's stack (§4.2) calls for SQLAlchemy + Alembic, but Phase 0's "done when" doesn't require any models or migrations. Deferred Alembic init to Phase 1, when the first real model (`Park`) is introduced — avoids an empty, undirected migration setup now.
- **Ruff for both lint and format** on the Python side (`ruff check` + `ruff format`), instead of ruff+black. Ruff's formatter is stable and functionally a black-compatible drop-in, so this avoids a second tool.
- **Health-check surface:** `GET /health` (app liveness only) and `GET /health/db` (executes `SELECT 1` through the async engine) — added specifically to give the frontend something concrete to poll to prove "talk to each other" + "Postgres reachable" per the Phase 0 bar.
- **No automated test for `/health/db`.** Unit tests run without a live Postgres instance; `/health/db` is verified manually (see Verification section below) rather than via a DB-backed test fixture, since setting up test-DB infrastructure is beyond Phase 0's scope.
- **CORS:** backend allows `http://localhost:5173` (Vite's default dev port) via `CORS_ORIGINS` setting.
- Deleted the Vite template's demo assets/markup (hero image, counter button, docs/social links, associated CSS) and replaced `App.tsx` with a minimal page that calls `/health` and `/health/db` and renders their status — this is the "talk to each other" proof for Phase 0.

## In progress — backend dependency install

`uv add` for the backend's runtime deps (fastapi, uvicorn, sqlalchemy, asyncpg,
pydantic-settings) hit repeated network timeouts fetching wheel metadata from
PyPI through this session's proxy. Resolution itself succeeded — `uv.lock` is
complete and consistent (all 35 packages resolved, including every runtime
dep) — but the actual wheel downloads into the local `.venv` were still slow/
in progress as of this commit. `.venv` isn't committed, so this doesn't affect
repo state; it just means `uv sync` may need a retry (or more patience) the
first time it's run in a fresh environment. Verification (ruff, pytest, a
uvicorn smoke test) is still pending and will follow in a subsequent commit.

## Open item — needs your input

**Docker is not available inside this sandboxed session** (`dockerd` exists but can't start — `ulimit: Operation not permitted`, consistent with a container that doesn't allow nested privileged Docker). This means I could not run `docker compose up -d db` here to verify Postgres connectivity end-to-end.

`docker-compose.yml` is written and reviewed for correctness, but **only verified by inspection, not by actually running it.** You'll need to run this yourself (or in an environment where Docker works) to confirm the full loop:

```bash
docker compose up -d db
cd backend && uv sync && cp .env.example .env && uv run uvicorn app.main:app --reload
# in another terminal
cd frontend && npm install && cp .env.example .env && npm run dev
# visit http://localhost:5173 — should show "Backend API: ok" and "Database (via backend): ok"
```

Let me know if that doesn't work as expected and I'll adjust.
