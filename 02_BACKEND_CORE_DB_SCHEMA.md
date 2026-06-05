# TrustStack Lite Implementation Pack

**Project:** TrustStack Lite — risk-adaptive onboarding, consent governance, document verification, fraud/risk scoring, review operations, and webhook integration.

**Non-negotiable rule:** No fake success paths. Do not silently mock external systems. Do not add fallback providers that make tests pass without the configured real service. If a real external provider credential is missing, the relevant test must fail with a clear message saying exactly which environment variable is required.

**Local real infrastructure:** Docker Compose must run real PostgreSQL, Redis, MinIO/S3-compatible storage, backend API, worker, frontend, and observability services. Local MinIO is acceptable as real object storage for development; production must use AWS S3 or another real S3-compatible managed bucket.

**External verification:** Real OCR/redaction must use a configured OCR provider. Real KYC/PAN/Aadhaar/liveness checks must use a legally obtained provider sandbox/live account. Do not scrape government portals. Do not implement unauthorized Aadhaar/PAN verification.



# 02 — Backend Core and Database Schema

## Objective

Implement the core backend API, migrations, domain schema, seed data, and OpenAPI generation.

## Why this matters for the IDfy interview

IDfy's domain is workflow-heavy: onboarding cases, verification steps, fraud/risk artifacts, privacy records, audit events, and webhooks. A weak schema will expose weak engineering thinking immediately.

## Dependencies

- 01 must be complete.
- Postgres service must be running.
- Backend framework chosen.

## Before implementation, ask for these if missing

- Confirm whether backend is FastAPI/Python or NestJS/TypeScript. Do not switch halfway.

## Implementation instructions

1. Create database migration system: Alembic for FastAPI, Prisma/TypeORM migrations for NestJS.
2. Define UUID primary keys, timestamp columns, soft-delete where required, and strict foreign keys.
3. Create tables: tenants, users, roles, tenant_api_keys, applicants, onboarding_cases, consent_notices, consent_records, documents, verification_steps, risk_signals, risk_decisions, review_tasks, audit_events, webhook_endpoints, webhook_deliveries, retention_requests.
4. Add indexes for every foreign key, `tenant_id`, `case_id`, `status`, `created_at`, and review queue filters.
5. Add enums or constrained values for case state, verification step type, decision, risk severity, review status, and webhook status.
6. Implement repositories/services for tenants, applicants, cases, documents, and audit events.
7. Create seed data: one tenant, one tenant admin, one analyst, one applicant, one consent notice. Seed data must be deterministic and documented.
8. Expose endpoints: `POST /v1/applicants`, `POST /v1/onboarding-cases`, `GET /v1/onboarding-cases/{id}`, `GET /v1/audit-events`.
9. Generate OpenAPI schema into `packages/openapi/openapi.json`.
10. Add correlation/request ID middleware.

## Testing instructions

Run:

```bash
docker compose exec api alembic upgrade head
docker compose exec api pytest tests/integration/test_schema.py -q
docker compose exec api pytest tests/integration/test_cases_api.py -q
curl -s http://localhost:8000/openapi.json | jq '.paths | keys'
```

Expected:

- migrations apply from empty DB;
- seeded tenant/applicant/case are created;
- OpenAPI includes all implemented endpoints;
- audit event is created when applicant/case is created.


## Acceptance criteria

- All core tables exist through migrations.
- Case creation is persisted and tenant-scoped.
- Audit log records create/read-sensitive operations.
- OpenAPI schema is generated.

## What must be true after this MD is complete

- Backend has real persistence, not in-memory storage.
- Every future MD can attach to case IDs and tenant IDs.
- Schema design can be explained in interview.

## Do not do this

- Do not hard-code secrets.
- Do not fake success if a required dependency is missing.
- Do not bypass database migrations.
- Do not skip audit events for sensitive actions.
- Do not introduce hidden global state that breaks multi-tenant isolation.


