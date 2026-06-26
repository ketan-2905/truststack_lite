#!/usr/bin/env bash
# Wait until the core services report healthy. Used by smoke/load tests and CI.
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
MAX_WAIT="${MAX_WAIT:-120}"

echo "Waiting for API at ${API_URL}/health/live (timeout ${MAX_WAIT}s)..."
elapsed=0
until curl -fsS "${API_URL}/health/live" >/dev/null 2>&1; do
  sleep 2
  elapsed=$((elapsed + 2))
  if [ "${elapsed}" -ge "${MAX_WAIT}" ]; then
    echo "ERROR: API did not become live within ${MAX_WAIT}s" >&2
    exit 1
  fi
done
echo "API is live."

echo "Waiting for core dependencies (database, redis, object storage) to be ok..."
elapsed=0
until [ "$(curl -fsS "${API_URL}/health" 2>/dev/null | jq -r '.status' 2>/dev/null)" = "ok" ]; do
  sleep 2
  elapsed=$((elapsed + 2))
  if [ "${elapsed}" -ge "${MAX_WAIT}" ]; then
    echo "ERROR: core dependencies not healthy within ${MAX_WAIT}s" >&2
    curl -fsS "${API_URL}/health" || true
    exit 1
  fi
done
echo "Core dependencies healthy."
