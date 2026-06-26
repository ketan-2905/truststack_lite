#!/usr/bin/env bash
# Webhook smoke checks against the running, seeded stack (MD 08).
# Deliveries target the in-network webhook-receiver container.
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
ADMIN_EMAIL="${SEED_ADMIN_EMAIL:-admin@truststack.local}"
ADMIN_PASSWORD="${SEED_ADMIN_PASSWORD:-change-me-local}"
RECEIVER_URL="${WEBHOOK_RECEIVER_INTERNAL_URL:-http://webhook-receiver:8080/}"

pass() { echo "  PASS: $1"; }
fail() { echo "  FAIL: $1" >&2; exit 1; }

token="$(curl -s -X POST "${API_URL}/v1/auth/login" -H 'Content-Type: application/json' \
  -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}" | jq -r '.access_token')"
raw="$(curl -s -X POST "${API_URL}/v1/api-keys" -H "Authorization: Bearer ${token}" \
  -H 'Content-Type: application/json' -d '{"name":"wh-smoke"}' | jq -r '.raw_key')"

# Create an endpoint subscribed to case.created (+ test events).
created="$(curl -s -X POST "${API_URL}/v1/webhook-endpoints" -H "Authorization: Bearer ${token}" \
  -H 'Content-Type: application/json' \
  -d "{\"url\":\"${RECEIVER_URL}\",\"event_types\":[\"case.created\",\"webhook.test\"]}")"
endpoint_id="$(echo "${created}" | jq -r '.id')"
secret="$(echo "${created}" | jq -r '.signing_secret')"
[ -n "${secret}" ] && [ "${secret}" != "null" ] && pass "endpoint created with signing secret" \
  || fail "no signing secret: ${created}"

# Test send -> delivered (real signed POST to receiver).
test_status="$(curl -s -X POST "${API_URL}/v1/webhook-endpoints/${endpoint_id}/test" \
  -H "Authorization: Bearer ${token}" | jq -r '.status')"
[ "${test_status}" = "delivered" ] && pass "test event delivered (real signed POST)" \
  || fail "test event status was ${test_status}"

# Create a case -> emits case.created -> async delivery.
aid="$(curl -s -X POST "${API_URL}/v1/applicants" -H "X-API-Key: ${raw}" \
  -H 'Content-Type: application/json' -d '{"full_name":"Webhook Smoke"}' | jq -r '.id')"
curl -s -o /dev/null -X POST "${API_URL}/v1/onboarding-cases" -H "X-API-Key: ${raw}" \
  -H 'Content-Type: application/json' -d "{\"applicant_id\":\"${aid}\"}"

echo "  ... waiting for async case.created delivery"
delivered=""
for _ in $(seq 1 15); do
  delivered="$(curl -s "${API_URL}/v1/webhook-deliveries?delivery_status=delivered" \
    -H "Authorization: Bearer ${token}" | jq -r '[.[] | select(.event_type=="case.created")] | length')"
  [ "${delivered}" -ge 1 ] && break
  sleep 1
done
[ "${delivered:-0}" -ge 1 ] && pass "async case.created webhook delivered" \
  || fail "case.created webhook was not delivered"

# Replay command runs (no failed deliveries expected -> 0).
bash "$(dirname "${BASH_SOURCE[0]}")/replay-webhooks.sh" >/dev/null 2>&1 && pass "replay command runs" \
  || fail "replay command failed"

echo "Webhook smoke passed."
