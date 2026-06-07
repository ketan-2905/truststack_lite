# TrustStack Lite Implementation Pack

**Project:** TrustStack Lite — risk-adaptive onboarding, consent governance, document verification, fraud/risk scoring, review operations, and webhook integration.

**Non-negotiable rule:** No fake success paths. Do not silently mock external systems. Do not add fallback providers that make tests pass without the configured real service. If a real external provider credential is missing, the relevant test must fail with a clear message saying exactly which environment variable is required.

**Local real infrastructure:** Docker Compose must run real PostgreSQL, Redis, MinIO/S3-compatible storage, backend API, worker, frontend, and observability services. Local MinIO is acceptable as real object storage for development; production must use AWS S3 or another real S3-compatible managed bucket.

**External verification:** Real OCR/redaction must use a configured OCR provider. Real KYC/PAN/Aadhaar/liveness checks must use a legally obtained provider sandbox/live account. Do not scrape government portals. Do not implement unauthorized Aadhaar/PAN verification.



# 08 — Async Workers, Domain Events, and Signed Webhooks

## Objective

Implement event-driven processing, reliable worker jobs, idempotency, and signed webhooks.

## Why this matters for the IDfy interview

Real verification/onboarding systems are asynchronous. If you make everything synchronous, you will look like you have not built production workflows.

## Dependencies

- 01-07 complete.
- Redis running.
- Risk and document jobs exist.

## Before implementation, ask for these if missing

- Provide webhook receiver URL for real manual testing if available. Local default can use webhook.site or a local receiver container.

## Implementation instructions

1. Create domain event table or queue event model: `case.created`, `consent.granted`, `document.uploaded`, `ocr.completed`, `risk.decided`, `review.resolved`, `case.completed`.
2. Create worker jobs for OCR, redaction, provider status polling, risk recomputation, and webhook delivery.
3. Implement idempotency keys for external client case creation and provider callbacks.
4. Implement webhook endpoints table with URL, secret, active status, event filters.
5. Sign outbound webhooks with HMAC-SHA256 using tenant webhook secret.
6. Implement retry policy: exponential backoff, max attempts, dead-letter state.
7. Persist every delivery attempt with status code, response body hash, duration, and error.
8. Create webhook test endpoint that sends a real signed test event.
9. Add CLI/script to replay failed webhook deliveries.
10. Add audit events for webhook endpoint creation, secret rotation, and delivery failure.

## Testing instructions

Run:

```bash
docker compose exec worker pytest tests/events/test_worker_jobs.py -q
docker compose exec api pytest tests/webhooks/test_signature.py -q
docker compose exec worker pytest tests/webhooks/test_retries.py -q
bash scripts/smoke-test.sh webhooks
```

Manual real webhook test:

```bash
WEBHOOK_TEST_URL=https://webhook.site/<your-url> bash scripts/smoke-test.sh webhook-real
```

Expected:

- events create jobs;
- jobs update DB state;
- webhook signatures verify;
- failed webhooks retry and eventually enter `failed`;
- replay command resends failed event.


## Acceptance criteria

- Async worker processes real Redis jobs.
- Webhooks are signed.
- Delivery attempts are persisted.
- Idempotency prevents duplicates.

## What must be true after this MD is complete

- System now behaves like integration infrastructure.
- You can discuss reliability under provider/client failure.
- No silent success path exists.

## Do not do this

- Do not hard-code secrets.
- Do not fake success if a required dependency is missing.
- Do not bypass database migrations.
- Do not skip audit events for sensitive actions.
- Do not introduce hidden global state that breaks multi-tenant isolation.


