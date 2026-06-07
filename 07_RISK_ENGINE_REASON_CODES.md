# TrustStack Lite Implementation Pack

**Project:** TrustStack Lite — risk-adaptive onboarding, consent governance, document verification, fraud/risk scoring, review operations, and webhook integration.

**Non-negotiable rule:** No fake success paths. Do not silently mock external systems. Do not add fallback providers that make tests pass without the configured real service. If a real external provider credential is missing, the relevant test must fail with a clear message saying exactly which environment variable is required.

**Local real infrastructure:** Docker Compose must run real PostgreSQL, Redis, MinIO/S3-compatible storage, backend API, worker, frontend, and observability services. Local MinIO is acceptable as real object storage for development; production must use AWS S3 or another real S3-compatible managed bucket.

**External verification:** Real OCR/redaction must use a configured OCR provider. Real KYC/PAN/Aadhaar/liveness checks must use a legally obtained provider sandbox/live account. Do not scrape government portals. Do not implement unauthorized Aadhaar/PAN verification.



# 07 — Explainable Risk Engine and Reason Codes

## Objective

Build the deterministic, explainable risk scoring engine that converts facts and verification outcomes into decisions.

## Why this matters for the IDfy interview

Fraud systems need explainability. A black-box fake AI model is not impressive here. A deterministic signal ledger with reason codes is more credible, testable, auditable, and interview-safe.

## Dependencies

- 01-06 complete.
- Risk signal and decision tables exist.
- At least document/OCR signals available.

## Before implementation, ask for these if missing

- Confirm scoring thresholds: default approve < 40, review 40-69, reject >= 70 or hard-block rule.
- Confirm whether business wants manual override available: default yes.

## Implementation instructions

1. Create `risk_policies` config as code with versioned policy files under `apps/api/app/risk/policies/`.
2. Define signal categories: identity_mismatch, duplicate_artifact, missing_consent, provider_failure, tamper_suspected, unsupported_document, velocity_anomaly, minor_guardian_missing.
3. Implement signal calculator functions. Each function must be pure and unit-testable.
4. Persist every signal as a row with severity, score_delta, evidence_json, and policy_version.
5. Implement decision recomputation endpoint and worker task.
6. Decision logic: sum score deltas, apply hard-block rules, assign decision: `approved`, `manual_review`, `rejected`, `blocked_dependency`.
7. Generate human-readable explanation JSON for dashboard and API.
8. Make risk recomputation idempotent by policy_version and case_id.
9. Create review task automatically when decision is `manual_review`.
10. Audit every decision change.

## Testing instructions

Run:

```bash
docker compose exec api pytest tests/risk/test_signal_calculators.py -q
docker compose exec api pytest tests/risk/test_policy_decisions.py -q
docker compose exec api pytest tests/risk/test_idempotent_recompute.py -q
bash scripts/smoke-test.sh risk
```

Expected scenarios:

- low-risk complete case -> `approved`;
- missing consent -> blocked or review based on policy;
- duplicate checksum -> `manual_review`;
- provider tamper failure -> `rejected` or `manual_review` depending threshold;
- recomputing twice does not duplicate signals incorrectly.


## Acceptance criteria

- Risk policies are versioned.
- Every decision has reason codes.
- Risk scoring is repeatable and testable.
- Manual review tasks are created from risk decisions.

## What must be true after this MD is complete

- The anti-fraud core is real and explainable.
- You can demo why a case was flagged.
- You can discuss trade-offs between friction and fraud prevention.

## Do not do this

- Do not hard-code secrets.
- Do not fake success if a required dependency is missing.
- Do not bypass database migrations.
- Do not skip audit events for sensitive actions.
- Do not introduce hidden global state that breaks multi-tenant isolation.


