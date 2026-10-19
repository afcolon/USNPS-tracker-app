#!/usr/bin/env bash
# One-off data loading: all 63 National Parks, then pilot hike data for Zion.
# Requires Postgres running and migrated (scripts/dev.sh, or at least
# `docker compose up -d --wait db` + `cd backend && uv run alembic upgrade head`),
# and ingestion/.env set up with a real NPS_API_KEY (see ingestion/README.md).

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../ingestion"

echo "==> Loading all 63 National Parks from the NPS API..."
uv run python load_parks.py

echo ""
echo "==> Loading pilot hike data (Zion)..."
uv run python load_hikes.py data/zion_hikes.json
