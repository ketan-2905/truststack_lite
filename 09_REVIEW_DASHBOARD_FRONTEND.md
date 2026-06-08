# TrustStack Lite Implementation Pack

**Project:** TrustStack Lite — risk-adaptive onboarding, consent governance, document verification, fraud/risk scoring, review operations, and webhook integration.

**Non-negotiable rule:** No fake success paths. Do not silently mock external systems. Do not add fallback providers that make tests pass without the configured real service. If a real external provider credential is missing, the relevant test must fail with a clear message saying exactly which environment variable is required.

**Local real infrastructure:** Docker Compose must run real PostgreSQL, Redis, MinIO/S3-compatible storage, backend API, worker, frontend, and observability services. Local MinIO is acceptable as real object storage for development; production must use AWS S3 or another real S3-compatible managed bucket.

**External verification:** Real OCR/redaction must use a configured OCR provider. Real KYC/PAN/Aadhaar/liveness checks must use a legally obtained provider sandbox/live account. Do not scrape government portals. Do not implement unauthorized Aadhaar/PAN verification.



# 09 — Applicant Flow and Analyst Review Dashboard

## Objective

Build the frontend for applicant onboarding, consent, document upload, case status, analyst queue, risk explanation, and review resolution.

## Why this matters for the IDfy interview

The JD calls out UI, APIs, and product collaboration. A backend-only project can be strong, but a thin dashboard makes your story much easier to understand in an interview.

## Dependencies

- 01-08 complete.
- API OpenAPI available.
- Auth works.

## Before implementation, ask for these if missing

- Confirm branding: default clean blue/white TrustStack Lite. Do not copy IDfy branding/logo.

## Implementation instructions

1. Create web app routes: `/login`, `/applicant/start`, `/applicant/case/[id]`, `/dashboard`, `/dashboard/cases`, `/dashboard/review`, `/dashboard/review/[taskId]`, `/dashboard/audit`, `/dashboard/webhooks`.
2. Use generated API client from OpenAPI or typed fetch wrappers. Do not hand-code inconsistent response shapes.
3. Implement login with JWT storage using secure HTTP-only cookie where possible.
4. Applicant flow: create case, show active consent, record consent, upload document, submit case, show status timeline.
5. Operator dashboard: metrics cards for total cases, pending review, approved, rejected, provider failures, webhook failures.
6. Review queue: filter by status, risk severity, SLA, created date.
7. Review detail page: show applicant data, consent timeline, document redacted preview, risk score, reason codes, audit timeline, resolve action.
8. Webhook settings page: list endpoints, rotate secret, send test event.
9. Audit page: searchable audit events by case/applicant/event type.
10. Add Playwright E2E flows for happy path and risky path.

## Testing instructions

Run:

```bash
docker compose exec web npm run lint
docker compose exec web npm test
docker compose exec web npm run test:e2e
bash scripts/smoke-test.sh frontend
```

Manual demo:

1. Login as analyst.
2. Create applicant case.
3. Accept consent.
4. Upload document.
5. Submit case.
6. Review risk outcome.
7. Resolve manual review task.
8. Confirm audit timeline and webhook event.


## Acceptance criteria

- Frontend covers applicant and analyst journeys.
- Risk explanation is visible.
- Redacted document preview is used.
- Playwright E2E passes.

## What must be true after this MD is complete

- Interview demo becomes visual and understandable.
- Dashboard proves product thinking.
- Frontend does not bypass API security.

## Do not do this

- Do not hard-code secrets.
- Do not fake success if a required dependency is missing.
- Do not bypass database migrations.
- Do not skip audit events for sensitive actions.
- Do not introduce hidden global state that breaks multi-tenant isolation.


