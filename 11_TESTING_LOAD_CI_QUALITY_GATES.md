# TrustStack Lite Implementation Pack

**Project:** TrustStack Lite — risk-adaptive onboarding, consent governance, document verification, fraud/risk scoring, review operations, and webhook integration.

**Non-negotiable rule:** No fake success paths. Do not silently mock external systems. Do not add fallback providers that make tests pass without the configured real service. If a real external provider credential is missing, the relevant test must fail with a clear message saying exactly which environment variable is required.

**Local real infrastructure:** Docker Compose must run real PostgreSQL, Redis, MinIO/S3-compatible storage, backend API, worker, frontend, and observability services. Local MinIO is acceptable as real object storage for development; production must use AWS S3 or another real S3-compatible managed bucket.

**External verification:** Real OCR/redaction must use a configured OCR provider. Real KYC/PAN/Aadhaar/liveness checks must use a legally obtained provider sandbox/live account. Do not scrape government portals. Do not implement unauthorized Aadhaar/PAN verification.



# 11 — Testing, Load Testing, CI, and Quality Gates

## Objective

Build the complete test strategy: unit, integration, E2E, external-gated tests, load testing, static analysis, coverage, and CI gates.

## Why this matters for the IDfy interview

The JD explicitly mentions writing test cases alongside implementation, static analysis, and performance/load testing. If you do not have this, you are ignoring the job description.

## Dependencies

- 01-10 complete.
- Core app flows complete.

## Before implementation, ask for these if missing

- Confirm CI provider: default GitHub Actions.
- Confirm minimum coverage threshold: default 75% lines for backend core modules.

## Implementation instructions

1. Organize tests by layer: unit, integration, external, e2e, security, load.
2. Add backend unit tests for risk policies, consent validation, auth utilities, webhook signing.
3. Add integration tests using real Postgres/Redis/MinIO services in Docker.
4. Add external provider tests gated by `RUN_EXTERNAL_TESTS=true`.
5. Add Playwright E2E tests for applicant happy path and analyst review path.
6. Add k6 load tests for case creation, case status polling, webhook fan-out, and review listing.
7. Add migration test: fresh DB -> latest migration -> seed -> smoke flow.
8. Add OpenAPI diff/check in CI.
9. Add lint/type/static analysis gates.
10. Add CI matrix: backend, frontend, worker, docker-build, security-scan, load-smoke.
11. Generate `docs/testing.md` with test matrix and command list.
12. Make CI fail on missing env vars when external tests are explicitly enabled.

## Testing instructions

Run:

```bash
docker compose exec api pytest -q
docker compose exec worker pytest -q
docker compose exec web npm test
docker compose exec web npm run test:e2e
bash scripts/load-test.sh
act -j ci  # optional local GitHub Actions runner
```

Load test minimum targets for interview demo:

- 100 concurrent case-status reads for 60 seconds;
- 20 concurrent case submissions for 60 seconds;
- p95 API latency under 500 ms locally for read endpoints;
- zero duplicate decisions under repeated callback retries.


## Acceptance criteria

- CI runs automatically.
- Unit/integration/E2E tests pass.
- External tests fail clearly if credentials missing and enabled.
- Load test report exists.

## What must be true after this MD is complete

- The repo has proof, not claims.
- You can show test evidence in the interview.
- Quality gates prevent silent regressions.

## Do not do this

- Do not hard-code secrets.
- Do not fake success if a required dependency is missing.
- Do not bypass database migrations.
- Do not skip audit events for sensitive actions.
- Do not introduce hidden global state that breaks multi-tenant isolation.


