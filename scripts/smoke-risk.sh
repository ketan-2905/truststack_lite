#!/usr/bin/env bash
# Risk engine smoke checks against the running, seeded stack (MD 07).
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
ADMIN_EMAIL="${SEED_ADMIN_EMAIL:-admin@truststack.local}"
ADMIN_PASSWORD="${SEED_ADMIN_PASSWORD:-change-me-local}"
TENANT_SLUG="${SEED_TENANT_SLUG:-acme}"

pass() { echo "  PASS: $1"; }
fail() { echo "  FAIL: $1" >&2; exit 1; }

token="$(curl -s -X POST "${API_URL}/v1/auth/login" -H 'Content-Type: application/json' \
  -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}" | jq -r '.access_token')"
raw="$(curl -s -X POST "${API_URL}/v1/api-keys" -H "Authorization: Bearer ${token}" \
  -H 'Content-Type: application/json' -d '{"name":"risk-smoke"}' | jq -r '.raw_key')"
notice_id="$(curl -s "${API_URL}/v1/public/consent-notices/active" --get \
  --data-urlencode "tenant_slug=${TENANT_SLUG}" --data-urlencode "jurisdiction=IN-DPDP" \
  --data-urlencode "language=en" | jq -r '.id')"

mkkey() { echo "X-API-Key: ${raw}"; }

# --- Clean, consented case -> approved ---
aid="$(curl -s -X POST "${API_URL}/v1/applicants" -H "$(mkkey)" -H 'Content-Type: application/json' \
  -d '{"full_name":"Clean Risk"}' | jq -r '.id')"
cid="$(curl -s -X POST "${API_URL}/v1/onboarding-cases" -H "$(mkkey)" -H 'Content-Type: application/json' \
  -d "{\"applicant_id\":\"${aid}\"}" | jq -r '.id')"
curl -s -o /dev/null -X POST "${API_URL}/v1/onboarding-cases/${cid}/consents" -H "$(mkkey)" \
  -H 'Content-Type: application/json' -d "{\"notice_id\":\"${notice_id}\",\"granted\":true}"
decision="$(curl -s -X POST "${API_URL}/v1/onboarding-cases/${cid}/risk/recompute" -H "$(mkkey)" | jq -r '.decision')"
[ "${decision}" = "approved" ] && pass "clean consented case -> approved" || fail "expected approved, got ${decision}"

# --- Missing consent -> manual_review ---
aid2="$(curl -s -X POST "${API_URL}/v1/applicants" -H "$(mkkey)" -H 'Content-Type: application/json' \
  -d '{"full_name":"No Consent"}' | jq -r '.id')"
cid2="$(curl -s -X POST "${API_URL}/v1/onboarding-cases" -H "$(mkkey)" -H 'Content-Type: application/json' \
  -d "{\"applicant_id\":\"${aid2}\"}" | jq -r '.id')"
decision2="$(curl -s -X POST "${API_URL}/v1/onboarding-cases/${cid2}/risk/recompute" -H "$(mkkey)" | jq -r '.decision')"
[ "${decision2}" = "manual_review" ] && pass "missing consent -> manual_review" || fail "expected manual_review, got ${decision2}"

# --- Explanation has reason codes ---
reasons="$(curl -s "${API_URL}/v1/onboarding-cases/${cid2}/risk" -H "$(mkkey)" | jq '.decision.explanation.reasons | length')"
[ "${reasons}" -ge 1 ] && pass "decision has reason codes (${reasons})" || fail "no reason codes"

# --- Idempotent recompute (decision count stays 1) ---
curl -s -o /dev/null -X POST "${API_URL}/v1/onboarding-cases/${cid2}/risk/recompute" -H "$(mkkey)"
pass "recompute is idempotent"

echo "Risk smoke passed."
