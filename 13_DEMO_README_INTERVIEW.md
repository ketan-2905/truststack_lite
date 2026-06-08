# TrustStack Lite Implementation Pack

**Project:** TrustStack Lite — risk-adaptive onboarding, consent governance, document verification, fraud/risk scoring, review operations, and webhook integration.

**Non-negotiable rule:** No fake success paths. Do not silently mock external systems. Do not add fallback providers that make tests pass without the configured real service. If a real external provider credential is missing, the relevant test must fail with a clear message saying exactly which environment variable is required.

**Local real infrastructure:** Docker Compose must run real PostgreSQL, Redis, MinIO/S3-compatible storage, backend API, worker, frontend, and observability services. Local MinIO is acceptable as real object storage for development; production must use AWS S3 or another real S3-compatible managed bucket.

**External verification:** Real OCR/redaction must use a configured OCR provider. Real KYC/PAN/Aadhaar/liveness checks must use a legally obtained provider sandbox/live account. Do not scrape government portals. Do not implement unauthorized Aadhaar/PAN verification.



# 13 — README, Demo Script, and Interview Talking Points

## Objective

Create the GitHub presentation layer: README, architecture docs, demo data, screenshots, video script, and interview talking points.

## Why this matters for the IDfy interview

Good code badly presented is wasted. IDfy wants engineers who think like product builders. The repo must explain what problem was solved and how it was engineered.

## Dependencies

- 01-12 complete.
- Working demo flow exists.
- Screenshots can be captured.

## Before implementation, ask for these if missing

- Confirm whether you want a 2-minute, 5-minute, or 8-minute demo video. Default 5 minutes.

## Implementation instructions

1. Rewrite README so the first screen explains the problem, solution, architecture, and how to run.
2. Add screenshots/GIFs: dashboard, applicant flow, risk explanation, audit timeline, webhook delivery.
3. Add `docs/architecture.md` with diagrams and module explanations.
4. Add `docs/security.md` summary of privacy, PII, audit, and threat controls.
5. Add `docs/testing.md` with exact commands and latest test result screenshots/log snippets.
6. Add `docs/tradeoffs.md` explaining what is intentionally not built.
7. Add demo seed script that creates one approved case and one manual review case.
8. Add demo script with exact speaking lines.
9. Add interview Q&A: why rules-first risk engine, why async workers, why consent ledger, why provider adapters, why no fake KYC.
10. Add `PROJECT_STATUS.md` listing complete, partial, blocked-by-credentials items.

## Testing instructions

Run:

```bash
bash scripts/seed-demo.sh
bash scripts/smoke-test.sh demo
```

Manual checklist:

- README setup works from clean clone;
- screenshots match current UI;
- demo script can be completed in under 5 minutes;
- `PROJECT_STATUS.md` does not overclaim anything.


## Acceptance criteria

- README is interviewer-ready.
- Demo can be completed without improvisation.
- Claims are honest about external provider access.
- Trade-offs are documented.

## What must be true after this MD is complete

- Project becomes presentable.
- Interview narrative is crisp.
- You avoid the common mistake of overclaiming AI/KYC capability.

## Do not do this

- Do not hard-code secrets.
- Do not fake success if a required dependency is missing.
- Do not bypass database migrations.
- Do not skip audit events for sensitive actions.
- Do not introduce hidden global state that breaks multi-tenant isolation.


