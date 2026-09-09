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

## Backend verification (done)

The dependency install that was in progress at the last commit finished
successfully (19 packages, ~5 min over this session's proxy — just slow, not
actually broken). Verified:

- `uv run ruff check .` — clean (one real finding fixed: switched `/health/db`
  from `Depends()` as a default argument to the `Annotated[AsyncSession,
  Depends(get_db)]` style, which is FastAPI's current recommended pattern and
  avoids ruff's B008 false-positive on the old style)
- `uv run ruff format --check .` — clean
- `uv run pytest` — 1 passed (`/health`)
- `uv run uvicorn app.main:app` smoke test — boots fine; `GET /health` →
  `200 {"status": "ok"}`; `GET /health/db` → `500 ConnectionRefusedError`
  (expected and correct, since no Postgres is reachable in this sandbox —
  see the Docker note below)

## Full-stack verification (done — on your machine)

Docker was not available inside the sandboxed session used to build this
(`dockerd` exists but can't start there — `ulimit: Operation not permitted`,
consistent with a container that doesn't allow nested privileged Docker), so
`docker compose up -d db` could only be verified by inspection at that point.

You then ran the full loop locally and confirmed it end-to-end:
`docker compose up -d db` → backend (`uv run uvicorn`) → frontend
(`npm run dev`) → `http://localhost:5173` shows **"Backend API: ok"** and
**"Database (via backend): ok"**. Phase 0's "done when" bar (§7 of the spec)
is met.

Two environment issues surfaced along the way, both now fixed in the repo
rather than just worked around once:
- A flaky/IPv6-broken path to `files.pythonhosted.org` blocked `uv sync` —
  environment-specific, not a repo issue; see git history for the
  troubleshooting if it recurs.
- Node 24 crashes with a `dyld` symbol error on macOS below 13.5. Pinned the
  frontend to Node 20 via `.nvmrc` + `package.json` `engines` — see
  `frontend/README.md` Prerequisites.
