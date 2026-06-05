# TrustStack Lite Implementation Pack

**Project:** TrustStack Lite — risk-adaptive onboarding, consent governance, document verification, fraud/risk scoring, review operations, and webhook integration.

**Non-negotiable rule:** No fake success paths. Do not silently mock external systems. Do not add fallback providers that make tests pass without the configured real service. If a real external provider credential is missing, the relevant test must fail with a clear message saying exactly which environment variable is required.

**Local real infrastructure:** Docker Compose must run real PostgreSQL, Redis, MinIO/S3-compatible storage, backend API, worker, frontend, and observability services. Local MinIO is acceptable as real object storage for development; production must use AWS S3 or another real S3-compatible managed bucket.

**External verification:** Real OCR/redaction must use a configured OCR provider. Real KYC/PAN/Aadhaar/liveness checks must use a legally obtained provider sandbox/live account. Do not scrape government portals. Do not implement unauthorized Aadhaar/PAN verification.



# 01 — Repo Infrastructure and One-Command Docker

## Objective

Create the repository skeleton, Docker Compose stack, environment convention, CI entrypoint, and first health checks.

## Why this matters for the IDfy interview

The JD expects scalable cloud-native applications, static analysis, load testing, and engineering discipline. If the project cannot start cleanly with one command, it already fails the ownership signal.

## Dependencies

- No previous MD required.

## Before implementation, ask for these if missing

- Preferred backend language: FastAPI/Python or NestJS/TypeScript.
- Confirm local ports 3000, 3001, 8000, 5432, 6379, 9000, 9001 are free.

## Implementation instructions

1. Create monorepo structure exactly as defined in `00_MASTER_IMPLEMENTATION.md`.
2. Add `infra/docker-compose.yml` with services: `api`, `worker`, `web`, `postgres`, `redis`, `minio`, `prometheus`, `grafana`.
3. Add root `docker-compose.yml` that includes or points to `infra/docker-compose.yml` so `docker compose up --build` works from repo root.
4. Create `.env.example` with all required variables. Use safe placeholder values only.
5. Create `scripts/wait-for-services.sh`, `scripts/seed.sh`, `scripts/smoke-test.sh`, and `scripts/load-test.sh`.
6. Create `/health` endpoint in API returning service status for API, DB, Redis, and object storage.
7. Add Docker health checks for API, Postgres, Redis, and MinIO.
8. Add GitHub Actions workflow skeleton that runs lint, tests, Docker build, and Trivy image scan.
9. Add `README.md` with local setup commands and service URLs.
10. Commit with message: `chore: scaffold truststack lite infrastructure`.

## Testing instructions

Run:

```bash
cp .env.example .env
docker compose up -d --build
docker compose ps
curl -f http://localhost:8000/health
bash scripts/smoke-test.sh
```

Expected:

- all containers healthy;
- `/health` returns `status: ok`;
- smoke test exits `0`;
- missing external OCR/KYC credentials are reported as `not_configured`, not hidden.


## Acceptance criteria

- `docker compose up --build` starts the full local stack.
- `/health` validates DB, Redis, object storage.
- CI workflow exists and runs at least lint/test placeholders.
- No provider-mocking code exists.

## What must be true after this MD is complete

- Repository can be cloned and started by an interviewer.
- All ports and service URLs are documented.
- The rest of the MDs can build on this structure.

## Do not do this

- Do not hard-code secrets.
- Do not fake success if a required dependency is missing.
- Do not bypass database migrations.
- Do not skip audit events for sensitive actions.
- Do not introduce hidden global state that breaks multi-tenant isolation.


