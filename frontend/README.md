# Frontend

React + Vite + TypeScript app. See [../docs/spec.md](../docs/spec.md).

## Setup

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Requires the backend running (see `../backend/README.md`) for the health checks on the home page to succeed.

## Commands

```bash
npm run dev            # dev server (http://localhost:5173)
npm run build           # production build
npm run lint             # oxlint
npm run format            # prettier --write
npm run format:check       # prettier --check
```
