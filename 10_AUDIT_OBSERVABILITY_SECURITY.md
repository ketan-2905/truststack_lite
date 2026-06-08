# TrustStack Lite Implementation Pack

**Project:** TrustStack Lite — risk-adaptive onboarding, consent governance, document verification, fraud/risk scoring, review operations, and webhook integration.

**Non-negotiable rule:** No fake success paths. Do not silently mock external systems. Do not add fallback providers that make tests pass without the configured real service. If a real external provider credential is missing, the relevant test must fail with a clear message saying exactly which environment variable is required.

**Local real infrastructure:** Docker Compose must run real PostgreSQL, Redis, MinIO/S3-compatible storage, backend API, worker, frontend, and observability services. Local MinIO is acceptable as real object storage for development; production must use AWS S3 or another real S3-compatible managed bucket.

**External verification:** Real OCR/redaction must use a configured OCR provider. Real KYC/PAN/Aadhaar/liveness checks must use a legally obtained provider sandbox/live account. Do not scrape government portals. Do not implement unauthorized Aadhaar/PAN verification.



# 10 — Audit, Observability, and Security Hardening

## Objective

Add production-grade audit logging, structured logs, metrics, traces, secret handling, PII minimization, and threat controls.

## Why this matters for the IDfy interview

IDfy's domain is sensitive identity data. Without audit and security controls, the project is not credible. This MD turns a demo into a serious engineering artifact.

## Dependencies

- 01-09 complete.
- Core flows working end to end.

## Before implementation, ask for these if missing

- Confirm logging destination in production: default stdout JSON locally, CloudWatch/GCP Logs in cloud.
- Confirm secret manager for deployment: AWS Secrets Manager, Doppler, Vault, or platform env.

## Implementation instructions

1. Standardize structured JSON logs with request_id, tenant_id, actor_id, event_type, and duration_ms.
2. Redact PII from logs: document numbers, phone, email, OCR text, raw provider payloads.
3. Add OpenTelemetry instrumentation for API and worker.
4. Expose Prometheus metrics: request count/latency, job queue depth, job failures, webhook failures, provider latency, case decision counts.
5. Create Grafana dashboard JSON committed under `infra/grafana/dashboards/`.
6. Define immutable audit event helper. All modules must use one helper.
7. Add security headers in API/frontend reverse proxy.
8. Add file upload protections: MIME validation, size limits, extension allowlist, checksum, malware-scan hook placeholder that fails closed if enabled but unconfigured.
9. Add secret scanning in CI.
10. Add dependency/container scanning in CI.
11. Add threat model document under `docs/security.md`.

## Testing instructions

Run:

```bash
docker compose exec api pytest tests/security/test_pii_log_redaction.py -q
docker compose exec api pytest tests/security/test_audit_coverage.py -q
docker compose exec worker pytest tests/observability/test_metrics.py -q
docker compose exec api pytest tests/security/test_upload_guards.py -q
docker compose exec trivy image truststack-api:local
```

Manual checks:

- open Grafana dashboard;
- trigger a document upload and risk decision;
- verify metrics change;
- inspect logs and confirm no raw OCR/PII appears.


## Acceptance criteria

- PII does not leak in logs.
- Metrics and traces exist.
- Audit coverage exists for sensitive actions.
- Security scans run in CI.

## What must be true after this MD is complete

- The project has production hygiene.
- You can discuss compliance-sensitive engineering honestly.
- Security is not bolted on at the end.

## Do not do this

- Do not hard-code secrets.
- Do not fake success if a required dependency is missing.
- Do not bypass database migrations.
- Do not skip audit events for sensitive actions.
- Do not introduce hidden global state that breaks multi-tenant isolation.


