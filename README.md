# National Parks Passport & Trip Planner

A passport-style tracker for U.S. National Parks, paired with a trip planner that recommends hikes for a given park and trip length — using computed hike stats (distance, elevation, difficulty) and travel time between trailheads.

Full spec: [docs/spec.md](docs/spec.md)

## Status

✅ Phase 0 complete — FastAPI + React + Postgres scaffolded and verified end-to-end. See [docs/phase0-notes.md](docs/phase0-notes.md) for scaffolding decisions.

✅ Phase 1 complete — all 63 National Parks load from the NPS API, mark visited, see stamps. Verified end-to-end against real Postgres + a real NPS API key. See [docs/phase1-notes.md](docs/phase1-notes.md).

✅ Phase 2 complete — hike data (stats, difficulty, highlights) for Zion, the pilot park, sourced via the AllTrails MCP connector. Verified end-to-end against real Postgres. See [docs/phase2-notes.md](docs/phase2-notes.md).

## Stack

- **Backend:** Python + FastAPI
- **Database:** PostgreSQL
- **Frontend:** React (Vite)
- **Data:** OpenStreetMap (Overpass API), USGS elevation data, NPS API/GIS data
- **Travel time:** OSRM

See [docs/spec.md](docs/spec.md) §4 for the full architecture rationale.

## Repo layout

```
backend/     FastAPI app (API + recommendation engine)
frontend/    React app
ingestion/   Data pipeline scripts (NPS, OSM, USGS) — run separately from the API
docs/        Spec and design docs
```

## Build phases

| Phase | Goal |
|---|---|
| 0 | Project scaffolding |
| 1 | Park data + passport |
| 2 | Hike data (pilot park) |
| 3 | Trip planner v1 (greedy) |
| 4 | Travel time integration |
| 5 | Expand hike data coverage |
| 6 | Optimization engine (stretch) |

See [docs/spec.md](docs/spec.md) §7 for details on each phase.

## Getting started

**One-time setup:**
```bash
docker compose up -d --wait db   # --wait: block until Postgres passes its healthcheck,
                                 # not just until the container starts (alembic below
                                 # connects immediately and won't retry)

cd backend && uv sync && cp .env.example .env && uv run alembic upgrade head && cd ..
cd frontend && nvm use && npm install && cp .env.example .env && cd ..
cd ingestion && uv sync && cp .env.example .env && cd ..   # add your NPS_API_KEY
```

**Every time — one command** starts Postgres, the backend, and the frontend together
(Ctrl-C stops all three):
```bash
./scripts/dev.sh
```

**Load data** (one-off, after Postgres is up — `./scripts/dev.sh` in another terminal,
or just `docker compose up -d --wait db`): loads all 63 National Parks + pilot hike data for Zion.
```bash
./scripts/load-data.sh
```

Visit `http://localhost:5173` — the passport grid should show all 63 parks once
`load-data.sh` has run.
See `backend/README.md`, `frontend/README.md`, and `ingestion/README.md` for prerequisites
and full command reference (running each component by hand, tests, lint, etc.).
