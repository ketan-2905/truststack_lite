#!/usr/bin/env bash
# Consent ledger smoke checks against the running, seeded stack (MD 04).
# Requires: stack up + `bash scripts/seed.sh` already run.
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
ADMIN_EMAIL="${SEED_ADMIN_EMAIL:-admin@truststack.local}"
ADMIN_PASSWORD="${SEED_ADMIN_PASSWORD:-change-me-local}"
TENANT_SLUG="${SEED_TENANT_SLUG:-acme}"

pass() { echo "  PASS: $1"; }
fail() { echo "  FAIL: $1" >&2; exit 1; }

token="$(curl -s -X POST "${API_URL}/v1/auth/login" -H 'Content-Type: application/json' \
  -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}" | jq -r '.access_token')"
[ -n "${token}" ] && [ "${token}" != "null" ] || fail "login failed"

raw="$(curl -s -X POST "${API_URL}/v1/api-keys" -H "Authorization: Bearer ${token}" \
  -H 'Content-Type: application/json' -d '{"name":"consent-smoke"}' | jq -r '.raw_key')"

# Public fetch of the seeded active notice.
notice_id="$(curl -s "${API_URL}/v1/public/consent-notices/active" \
  --get --data-urlencode "tenant_slug=${TENANT_SLUG}" \
  --data-urlencode "jurisdiction=IN-DPDP" --data-urlencode "language=en" | jq -r '.id')"
[ -n "${notice_id}" ] && [ "${notice_id}" != "null" ] && pass "public active notice fetched" \
  || fail "no active notice for ${TENANT_SLUG}"

# Create applicant + case via API key.
applicant_id="$(curl -s -X POST "${API_URL}/v1/applicants" -H "X-API-Key: ${raw}" \
  -H 'Content-Type: application/json' -d '{"full_name":"Consent Smoke"}' | jq -r '.id')"
case_id="$(curl -s -X POST "${API_URL}/v1/onboarding-cases" -H "X-API-Key: ${raw}" \
  -H 'Content-Type: application/json' -d "{\"applicant_id\":\"${applicant_id}\"}" | jq -r '.id')"

# Submit before consent → 409.
code="$(curl -s -o /dev/null -w '%{http_code}' -X POST \
  "${API_URL}/v1/onboarding-cases/${case_id}/submit" -H "X-API-Key: ${raw}")"
[ "${code}" = "409" ] && pass "submit before consent -> 409" || fail "expected 409, got ${code}"

# Record consent.
code="$(curl -s -o /dev/null -w '%{http_code}' -X POST \
  "${API_URL}/v1/onboarding-cases/${case_id}/consents" -H "X-API-Key: ${raw}" \
  -H 'Content-Type: application/json' -d "{\"notice_id\":\"${notice_id}\",\"granted\":true}")"
[ "${code}" = "201" ] && pass "consent recorded" || fail "consent grant got ${code}"

# Submit after consent → 200.
code="$(curl -s -o /dev/null -w '%{http_code}' -X POST \
  "${API_URL}/v1/onboarding-cases/${case_id}/submit" -H "X-API-Key: ${raw}")"
[ "${code}" = "200" ] && pass "submit after consent -> 200" || fail "expected 200, got ${code}"

# Withdraw → timeline keeps both records.
curl -s -o /dev/null -X POST "${API_URL}/v1/onboarding-cases/${case_id}/consents/withdraw" \
  -H "X-API-Key: ${raw}" -H 'Content-Type: application/json' \
  -d "{\"notice_id\":\"${notice_id}\"}"
count="$(curl -s "${API_URL}/v1/onboarding-cases/${case_id}/consents" -H "X-API-Key: ${raw}" | jq 'length')"
[ "${count}" = "2" ] && pass "timeline preserves grant + withdrawal" || fail "timeline has ${count} records"

# A retention request can be filed and approved.
rid="$(curl -s -X POST "${API_URL}/v1/retention-requests" -H "X-API-Key: ${raw}" \
  -H 'Content-Type: application/json' -d "{\"case_id\":\"${case_id}\",\"reason\":\"smoke\"}" | jq -r '.id')"
code="$(curl -s -o /dev/null -w '%{http_code}' -X POST \
  "${API_URL}/v1/retention-requests/${rid}/state" -H "Authorization: Bearer ${token}" \
  -H 'Content-Type: application/json' -d '{"state":"approved"}')"
[ "${code}" = "200" ] && pass "retention request approved" || fail "retention approve got ${code}"

echo "Consent smoke passed."
