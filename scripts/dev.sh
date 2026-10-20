#!/usr/bin/env bash
# Starts Postgres, the backend API, and the frontend dev server together.
# Ctrl-C stops all three. One-time setup (uv sync, npm install, .env files --
# see README.md "Getting started") must already be done; this script only
# starts things, it doesn't install anything.

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

# Load nvm non-interactively so the frontend picks up the Node version pinned
# in frontend/.nvmrc, even though this script isn't an interactive shell (nvm
# is normally only available because a shell's rc file sources it).
#
# nvm.sh is not written for `set -e`/`set -u`: it relies on functions that
# return non-zero as normal control flow (not real errors) and references
# variables that are legitimately unset on first load. Sourcing it with our
# strict mode still active aborts this entire script instantly and silently
# (before even the first echo below), so strict mode is relaxed just for the
# sourcing call and restored right after.
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
if [ -s "$NVM_DIR/nvm.sh" ]; then
  set +euo pipefail
  # shellcheck disable=SC1091
  \. "$NVM_DIR/nvm.sh"
  set -euo pipefail
fi

# kill 0 signals every process in this script's process group (itself plus
# every background job below), so Ctrl-C actually stops backend + frontend
# instead of leaving them running after the script exits. Disarming the trap
# first thing is essential -- kill 0 also signals this script itself, which
# would otherwise re-enter this same handler (it's armed for EXIT too) and
# recurse until the shell crashes.
cleanup() {
  trap - INT TERM EXIT
  echo
  echo "==> Stopping..."
  kill 0 2>/dev/null || true
}
trap cleanup INT TERM EXIT

echo "==> Starting Postgres (docker compose)..."
docker compose up -d --wait db

echo "==> Starting backend (http://localhost:8000)..."
(cd backend && uv run uvicorn app.main:app --reload) 2>&1 | sed -u 's/^/[backend]  /' &

echo "==> Starting frontend (http://localhost:5173)..."
(
  cd frontend
  if command -v nvm >/dev/null 2>&1; then
    set +euo pipefail
    nvm use >/dev/null
    set -euo pipefail
  fi
  npm run dev
) 2>&1 | sed -u 's/^/[frontend] /' &

wait
