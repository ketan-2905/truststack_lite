#!/usr/bin/env bash
# End-to-end smoke test of the running stack.
#   bash scripts/smoke-test.sh           # core infra checks
#   bash scripts/smoke-test.sh auth      # + auth checks (MD 03)
#   bash scripts/smoke-test.sh consent   # + consent checks (MD 04)
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
SUITE="${1:-core}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bash "${SCRIPT_DIR}/wait-for-services.sh"

pass() { echo "  PASS: $1"; }
fail() { echo "  FAIL: $1" >&2; exit 1; }

echo "== Smoke: core =="

health="$(curl -fsS "${API_URL}/health")"
status="$(echo "${health}" | jq -r '.status')"
[ "${status}" = "ok" ] && pass "/health status ok" || fail "/health status was '${status}'"

db="$(echo "${health}" | jq -r '.checks.database.status')"
[ "${db}" = "ok" ] && pass "database healthy" || fail "database not healthy"

redis="$(echo "${health}" | jq -r '.checks.redis.status')"
[ "${redis}" = "ok" ] && pass "redis healthy" || fail "redis not healthy"

storage="$(echo "${health}" | jq -r '.checks.object_storage.status')"
[ "${storage}" = "ok" ] && pass "object storage healthy" || fail "object storage not healthy"

# External providers must be REPORTED, not hidden.
ocr="$(echo "${health}" | jq -r '.providers.ocr')"
kyc="$(echo "${health}" | jq -r '.providers.kyc')"
[ -n "${ocr}" ] && [ "${ocr}" != "null" ] && pass "ocr provider reported as '${ocr}'" || fail "ocr provider not reported"
[ -n "${kyc}" ] && [ "${kyc}" != "null" ] && pass "kyc provider reported as '${kyc}'" || fail "kyc provider not reported"

# OpenAPI must be served.
curl -fsS "${API_URL}/openapi.json" >/dev/null && pass "openapi.json served" || fail "openapi.json missing"

if [ "${SUITE}" = "auth" ]; then
  echo "== Smoke: auth =="
  bash "${SCRIPT_DIR}/smoke-auth.sh"
fi

if [ "${SUITE}" = "consent" ]; then
  echo "== Smoke: consent =="
  bash "${SCRIPT_DIR}/smoke-consent.sh"
fi

if [ "${SUITE}" = "risk" ]; then
  echo "== Smoke: risk =="
  bash "${SCRIPT_DIR}/smoke-risk.sh"
fi

if [ "${SUITE}" = "webhooks" ]; then
  echo "== Smoke: webhooks =="
  bash "${SCRIPT_DIR}/smoke-webhooks.sh"
fi

echo "Smoke test passed."
