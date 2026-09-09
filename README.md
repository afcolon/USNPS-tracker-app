# National Parks Passport & Trip Planner

A passport-style tracker for U.S. National Parks, paired with a trip planner that recommends hikes for a given park and trip length — using computed hike stats (distance, elevation, difficulty) and travel time between trailheads.

Full spec: [docs/spec.md](docs/spec.md)

## Status

✅ Phase 0 complete — FastAPI + React + Postgres scaffolded and verified end-to-end. See [docs/phase0-notes.md](docs/phase0-notes.md) for scaffolding decisions.

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

```bash
docker compose up -d db

cd backend && uv sync && cp .env.example .env && uv run uvicorn app.main:app --reload
# in another terminal
cd frontend && nvm use && npm install && cp .env.example .env && npm run dev
```

Visit `http://localhost:5173` — should show both health checks as `ok`.
See `backend/README.md` and `frontend/README.md` for prerequisites and full command reference.
