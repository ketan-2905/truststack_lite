#!/usr/bin/env bash
# Apply migrations and load deterministic seed data into the running stack.
set -euo pipefail

COMPOSE="${COMPOSE:-docker compose}"

echo "Applying database migrations..."
${COMPOSE} exec -T api alembic upgrade head

echo "Loading seed data..."
${COMPOSE} exec -T api python -m app.seed

echo "Seed complete."
