# TrustStack Lite Implementation Pack

**Project:** TrustStack Lite — risk-adaptive onboarding, consent governance, document verification, fraud/risk scoring, review operations, and webhook integration.

**Non-negotiable rule:** No fake success paths. Do not silently mock external systems. Do not add fallback providers that make tests pass without the configured real service. If a real external provider credential is missing, the relevant test must fail with a clear message saying exactly which environment variable is required.

**Local real infrastructure:** Docker Compose must run real PostgreSQL, Redis, MinIO/S3-compatible storage, backend API, worker, frontend, and observability services. Local MinIO is acceptable as real object storage for development; production must use AWS S3 or another real S3-compatible managed bucket.

**External verification:** Real OCR/redaction must use a configured OCR provider. Real KYC/PAN/Aadhaar/liveness checks must use a legally obtained provider sandbox/live account. Do not scrape government portals. Do not implement unauthorized Aadhaar/PAN verification.



# 04 — Consent and Privacy Ledger

## Objective

Implement versioned consent notices, consent receipts, withdrawal, retention requests, and auditability.

## Why this matters for the IDfy interview

IDfy's Privy theme is privacy governance. Treating consent as a checkbox is immature. Treating it as a versioned ledger with receipts is interview-grade.

## Dependencies

- 01-03 complete.
- Auth/tenant context available.
- Consent tables migrated.

## Before implementation, ask for these if missing

- Confirm target jurisdiction: default `IN-DPDP`.
- Confirm languages: default English + Hindi placeholders. Real legal text must be reviewed by a lawyer before production.

## Implementation instructions

1. Create consent notice management endpoints: create, list, activate, deactivate notices.
2. Create public endpoint to fetch active notice by jurisdiction and language.
3. Implement `POST /v1/onboarding-cases/{id}/consents` to record consent receipt.
4. Store notice version, language, jurisdiction, purpose list, source IP, user agent, timestamp, and immutable receipt hash.
5. Prevent document upload/submission until required consent exists.
6. Implement consent withdrawal endpoint. Withdrawal must not delete old record; it adds a new record with `granted=false`.
7. Implement retention request endpoint with states: `requested`, `approved`, `completed`, `rejected`.
8. Add audit events for notice activation, consent grant, withdrawal, and retention request state changes.
9. Add dashboard read API for consent timeline per case.
10. Add validation that minor workflows require guardian consent when applicant age is below 18.

## Testing instructions

Run:

```bash
docker compose exec api pytest tests/privacy/test_consent_notices.py -q
docker compose exec api pytest tests/privacy/test_consent_receipts.py -q
docker compose exec api pytest tests/privacy/test_minor_guardian_consent.py -q
bash scripts/smoke-test.sh consent
```

Expected:

- uploading document before consent returns `409 Consent Required`;
- after consent, upload can proceed;
- withdrawal creates a new immutable event;
- old consent receipt remains visible in timeline.


## Acceptance criteria

- Consent notices are versioned.
- Consent receipts are immutable.
- Case submission is blocked without required consent.
- Minor flow requires guardian consent.

## What must be true after this MD is complete

- Project now demonstrates privacy governance, not just onboarding.
- Consent timeline can be shown to interviewer.
- No legal claim of DPDP compliance is made without review.

## Do not do this

- Do not hard-code secrets.
- Do not fake success if a required dependency is missing.
- Do not bypass database migrations.
- Do not skip audit events for sensitive actions.
- Do not introduce hidden global state that breaks multi-tenant isolation.


