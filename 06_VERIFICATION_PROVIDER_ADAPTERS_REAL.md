# TrustStack Lite Implementation Pack

**Project:** TrustStack Lite — risk-adaptive onboarding, consent governance, document verification, fraud/risk scoring, review operations, and webhook integration.

**Non-negotiable rule:** No fake success paths. Do not silently mock external systems. Do not add fallback providers that make tests pass without the configured real service. If a real external provider credential is missing, the relevant test must fail with a clear message saying exactly which environment variable is required.

**Local real infrastructure:** Docker Compose must run real PostgreSQL, Redis, MinIO/S3-compatible storage, backend API, worker, frontend, and observability services. Local MinIO is acceptable as real object storage for development; production must use AWS S3 or another real S3-compatible managed bucket.

**External verification:** Real OCR/redaction must use a configured OCR provider. Real KYC/PAN/Aadhaar/liveness checks must use a legally obtained provider sandbox/live account. Do not scrape government portals. Do not implement unauthorized Aadhaar/PAN verification.



# 06 — Real Verification Provider Adapters

## Objective

Implement provider adapter boundaries for KYC/liveness/document verification using real, legally obtained provider credentials.

## Why this matters for the IDfy interview

This is where you must not fool yourself. Without live/sandbox provider access, you cannot claim real KYC verification. You can implement the adapter contract and block execution until credentials exist.

## Dependencies

- 01-05 complete.
- OCR pipeline complete.
- Legal sandbox/live access to at least one verification provider if doing live KYC.

## Before implementation, ask for these if missing

- Which provider are you legally allowed to use? Options: IDfy sandbox, Persona, Veriff, Entrust/Onfido, Signzy, Surepass, HyperVerge, AWS Rekognition for face/document checks.
- Provide API base URL, API key/client ID, secret, webhook secret, and sandbox/live mode.
- Confirm which document/country is allowed for test. Do not test Aadhaar/PAN without authorized provider access.

## Implementation instructions

1. Create `VerificationProvider` interface with methods: `create_session`, `submit_document`, `submit_selfie`, `get_status`, `parse_callback`, `cancel_session`.
2. Create provider config table or env-driven provider config. Store secrets only in env/secret manager, not DB.
3. Implement exactly one provider adapter initially based on available credentials.
4. If no provider is configured, verification endpoints must return `424 Failed Dependency` with `missing_provider_config`.
5. Map provider-specific responses into normalized verification step states: `pending`, `processing`, `passed`, `failed`, `needs_review`, `provider_error`.
6. Persist provider request IDs and response hashes for traceability.
7. Implement webhook/callback endpoint for provider status updates.
8. Validate provider callback signature if provider supports signing.
9. Create risk signals from provider failures: document mismatch, liveness failed, duplicate identity, tamper suspected, provider risk score high.
10. Add clear README section: what provider was used, what was real, what was not available.

## Testing instructions

Run adapter contract tests:

```bash
docker compose exec worker pytest tests/providers/test_provider_contract.py -q
```

Run real provider tests:

```bash
RUN_EXTERNAL_TESTS=true VERIFY_PROVIDER=persona docker compose exec worker pytest tests/external/test_persona_provider.py -q
# or
RUN_EXTERNAL_TESTS=true VERIFY_PROVIDER=veriff docker compose exec worker pytest tests/external/test_veriff_provider.py -q
# or your selected provider
```

Expected:

- if credentials exist, provider session is created against real sandbox/live API;
- callback parser handles real provider payload;
- if credentials are missing, test fails with exact missing env var names;
- no fake provider marks a verification as passed.


## Acceptance criteria

- Provider boundary exists.
- At least one real provider can be integrated when credentials exist.
- Missing provider config fails loudly.
- Provider outputs become normalized verification steps and risk signals.

## What must be true after this MD is complete

- You can discuss vendor-agnostic architecture honestly.
- You are not falsely claiming real KYC without credentials.
- System is ready for real provider integration.

## Do not do this

- Do not hard-code secrets.
- Do not fake success if a required dependency is missing.
- Do not bypass database migrations.
- Do not skip audit events for sensitive actions.
- Do not introduce hidden global state that breaks multi-tenant isolation.


