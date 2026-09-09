# Frontend

React + Vite + TypeScript app. See [../docs/spec.md](../docs/spec.md).

## Prerequisites

- **Node.js 20.x.** Later Node builds (22+, and definitely 24) require macOS 13.5+ and will crash on
  older macOS with a `dyld: Symbol not found` error. If you use [nvm](https://github.com/nvm-sh/nvm),
  running `nvm use` in this directory picks up the pinned version from `.nvmrc` automatically.

## Setup

```bash
cd frontend
nvm use   # if using nvm — picks up Node 20 from .nvmrc
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
