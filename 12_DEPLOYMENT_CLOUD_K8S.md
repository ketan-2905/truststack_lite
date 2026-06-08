# TrustStack Lite Implementation Pack

**Project:** TrustStack Lite — risk-adaptive onboarding, consent governance, document verification, fraud/risk scoring, review operations, and webhook integration.

**Non-negotiable rule:** No fake success paths. Do not silently mock external systems. Do not add fallback providers that make tests pass without the configured real service. If a real external provider credential is missing, the relevant test must fail with a clear message saying exactly which environment variable is required.

**Local real infrastructure:** Docker Compose must run real PostgreSQL, Redis, MinIO/S3-compatible storage, backend API, worker, frontend, and observability services. Local MinIO is acceptable as real object storage for development; production must use AWS S3 or another real S3-compatible managed bucket.

**External verification:** Real OCR/redaction must use a configured OCR provider. Real KYC/PAN/Aadhaar/liveness checks must use a legally obtained provider sandbox/live account. Do not scrape government portals. Do not implement unauthorized Aadhaar/PAN verification.



# 12 — Deployment and Cloud Architecture

## Objective

Implement production deployment docs and optional manifests for Docker-based cloud deployment and Kubernetes/ECS-style architecture.

## Why this matters for the IDfy interview

IDfy's public technical material mentions independently scalable services and Kubernetes-based deployment for video services. Your project should show cloud-native readiness without pretending a toy laptop demo is production.

## Dependencies

- 01-11 complete.
- Docker images build successfully.
- Env checklist ready.

## Before implementation, ask for these if missing

- Choose deployment target: Railway/Render/Fly for fast demo, or AWS ECS/Fargate for stronger cloud story.
- Provide domain name if deploying publicly.
- Confirm cloud object storage provider and region.

## Implementation instructions

1. Create production Dockerfiles for API, worker, and web.
2. Create deployment compose file or ECS/K8s manifests under `infra/`.
3. Separate environment variables into local, staging, production examples.
4. Document required managed services: Postgres, Redis, object storage, secrets manager, logs, metrics.
5. Add health checks and readiness checks.
6. Add migration job for production deployment.
7. Add worker scaling instructions.
8. Add object storage bucket policy notes.
9. Add backup/restore notes for Postgres.
10. Add zero-downtime deployment notes: migration compatibility, rolling deploy, feature flags for provider changes.
11. Add `docs/deployment.md` with local, staging, and production steps.
12. Add architecture diagram for production.

## Testing instructions

Run local production-like test:

```bash
docker build -t truststack-api:local apps/api
docker build -t truststack-worker:local apps/worker
docker build -t truststack-web:local apps/web
docker compose -f infra/docker-compose.prod-like.yml up -d
bash scripts/smoke-test.sh
```

Cloud smoke test after deployment:

```bash
API_BASE_URL=https://api.your-domain.com WEB_BASE_URL=https://your-domain.com bash scripts/smoke-test.sh deployed
```

Expected:

- deployed API health is OK;
- migrations applied;
- worker consumes queue;
- document upload works;
- webhook delivery works;
- no local-only config remains in production.


## Acceptance criteria

- Production-like Docker images build.
- Deployment docs exist.
- Cloud architecture is explicit.
- Smoke tests validate deployed environment.

## What must be true after this MD is complete

- You can talk about scaling services independently.
- Deployment is reproducible.
- No 'works on my machine' excuse remains.

## Do not do this

- Do not hard-code secrets.
- Do not fake success if a required dependency is missing.
- Do not bypass database migrations.
- Do not skip audit events for sensitive actions.
- Do not introduce hidden global state that breaks multi-tenant isolation.


