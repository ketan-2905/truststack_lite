# TrustStack Lite Implementation Pack

**Project:** TrustStack Lite — risk-adaptive onboarding, consent governance, document verification, fraud/risk scoring, review operations, and webhook integration.

**Non-negotiable rule:** No fake success paths. Do not silently mock external systems. Do not add fallback providers that make tests pass without the configured real service. If a real external provider credential is missing, the relevant test must fail with a clear message saying exactly which environment variable is required.

**Local real infrastructure:** Docker Compose must run real PostgreSQL, Redis, MinIO/S3-compatible storage, backend API, worker, frontend, and observability services. Local MinIO is acceptable as real object storage for development; production must use AWS S3 or another real S3-compatible managed bucket.

**External verification:** Real OCR/redaction must use a configured OCR provider. Real KYC/PAN/Aadhaar/liveness checks must use a legally obtained provider sandbox/live account. Do not scrape government portals. Do not implement unauthorized Aadhaar/PAN verification.



# 03 — Auth, Multi-Tenancy, API Keys, and RBAC

## Objective

Implement first-party authentication, tenant API keys, key rotation, RBAC, and tenant isolation.

## Why this matters for the IDfy interview

IDfy deals with sensitive identity data and public technical descriptions mention endpoint authentication using API keys and key rotation. This MD proves you understand secure B2B API design.

## Dependencies

- 01 and 02 complete.
- Users, tenants, and API key tables exist.

## Before implementation, ask for these if missing

- Confirm admin email/password for local seed user.
- Confirm whether OTP/email login is required. Default: no; keep scope tight.

## Implementation instructions

1. Implement password hashing with Argon2id.
2. Implement JWT login for dashboard users: `POST /v1/auth/login`, `POST /v1/auth/refresh`, `POST /v1/auth/logout`.
3. Implement RBAC roles: `tenant_admin`, `analyst`, `viewer`, `system`.
4. Implement tenant API key creation. Store only hashed API keys, never raw keys.
5. Implement API key authentication for B2B endpoints using `X-API-Key`.
6. Implement API key rotation: create new active key, optionally expire old key. Never show old keys again.
7. Add middleware that resolves `tenant_id` from API key or JWT.
8. Enforce tenant isolation in repository queries. No query should return data across tenants unless explicitly system-scoped.
9. Add authorization checks per endpoint.
10. Audit login, failed login, API key creation, key rotation, and forbidden access attempts.
11. Add rate limiting for auth and API-key endpoints using Redis.

## Testing instructions

Run:

```bash
docker compose exec api pytest tests/security/test_auth.py -q
docker compose exec api pytest tests/security/test_tenant_isolation.py -q
docker compose exec api pytest tests/security/test_api_key_rotation.py -q
bash scripts/smoke-test.sh auth
```

Manual checks:

```bash
curl -X POST http://localhost:8000/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{{"email":"admin@truststack.local","password":"change-me-local"}}'
```

Expected:

- valid user receives JWT;
- invalid password fails;
- tenant A API key cannot read tenant B case;
- rotated old key fails after expiration.


## Acceptance criteria

- JWT auth works for dashboard users.
- API keys work for tenant clients.
- Keys are hashed and rotatable.
- Cross-tenant reads are impossible through API.

## What must be true after this MD is complete

- A real B2B auth model exists.
- Security story is credible.
- Every sensitive operation is audit-trailed.

## Do not do this

- Do not hard-code secrets.
- Do not fake success if a required dependency is missing.
- Do not bypass database migrations.
- Do not skip audit events for sensitive actions.
- Do not introduce hidden global state that breaks multi-tenant isolation.


