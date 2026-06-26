#!/usr/bin/env bash
# Auth smoke checks against the running, seeded stack (MD 03).
# Requires: stack up + `bash scripts/seed.sh` already run.
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
ADMIN_EMAIL="${SEED_ADMIN_EMAIL:-admin@truststack.local}"
ADMIN_PASSWORD="${SEED_ADMIN_PASSWORD:-change-me-local}"

pass() { echo "  PASS: $1"; }
fail() { echo "  FAIL: $1" >&2; exit 1; }

# 1. Invalid password is rejected.
code="$(curl -s -o /dev/null -w '%{http_code}' -X POST "${API_URL}/v1/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"definitely-wrong\"}")"
[ "${code}" = "401" ] && pass "invalid password -> 401" || fail "invalid password got ${code}"

# 2. Valid login returns a JWT.
login="$(curl -s -X POST "${API_URL}/v1/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}")"
token="$(echo "${login}" | jq -r '.access_token')"
[ -n "${token}" ] && [ "${token}" != "null" ] && pass "valid login -> JWT" || fail "no access_token: ${login}"

# 3. Admin can create a tenant API key.
created="$(curl -s -X POST "${API_URL}/v1/api-keys" \
  -H "Authorization: Bearer ${token}" -H 'Content-Type: application/json' \
  -d '{"name":"smoke-key"}')"
raw="$(echo "${created}" | jq -r '.raw_key')"
key_id="$(echo "${created}" | jq -r '.id')"
[ -n "${raw}" ] && [ "${raw}" != "null" ] && pass "api key created (raw shown once)" || fail "no raw_key: ${created}"

# 4. API key authenticates a B2B call.
code="$(curl -s -o /dev/null -w '%{http_code}' -X POST "${API_URL}/v1/applicants" \
  -H "X-API-Key: ${raw}" -H 'Content-Type: application/json' \
  -d '{"full_name":"Smoke Applicant"}')"
[ "${code}" = "201" ] && pass "api key authorizes applicant create" || fail "api key call got ${code}"

# 5. Unauthenticated B2B call is rejected.
code="$(curl -s -o /dev/null -w '%{http_code}' -X POST "${API_URL}/v1/applicants" \
  -H 'Content-Type: application/json' -d '{"full_name":"No Auth"}')"
[ "${code}" = "401" ] && pass "unauthenticated -> 401" || fail "unauthenticated got ${code}"

# 6. Rotation invalidates the old key.
rotated="$(curl -s -X POST "${API_URL}/v1/api-keys/${key_id}/rotate" \
  -H "Authorization: Bearer ${token}" -H 'Content-Type: application/json' \
  -d '{"expire_old":true}')"
new_raw="$(echo "${rotated}" | jq -r '.raw_key')"
code="$(curl -s -o /dev/null -w '%{http_code}' -X POST "${API_URL}/v1/applicants" \
  -H "X-API-Key: ${raw}" -H 'Content-Type: application/json' -d '{"full_name":"Old Key"}')"
[ "${code}" = "401" ] && pass "rotated old key -> 401" || fail "old key still works (${code})"
code="$(curl -s -o /dev/null -w '%{http_code}' -X POST "${API_URL}/v1/applicants" \
  -H "X-API-Key: ${new_raw}" -H 'Content-Type: application/json' -d '{"full_name":"New Key"}')"
[ "${code}" = "201" ] && pass "rotated new key works" || fail "new key failed (${code})"

echo "Auth smoke passed."
