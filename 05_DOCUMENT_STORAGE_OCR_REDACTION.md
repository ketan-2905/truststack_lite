# TrustStack Lite Implementation Pack

**Project:** TrustStack Lite — risk-adaptive onboarding, consent governance, document verification, fraud/risk scoring, review operations, and webhook integration.

**Non-negotiable rule:** No fake success paths. Do not silently mock external systems. Do not add fallback providers that make tests pass without the configured real service. If a real external provider credential is missing, the relevant test must fail with a clear message saying exactly which environment variable is required.

**Local real infrastructure:** Docker Compose must run real PostgreSQL, Redis, MinIO/S3-compatible storage, backend API, worker, frontend, and observability services. Local MinIO is acceptable as real object storage for development; production must use AWS S3 or another real S3-compatible managed bucket.

**External verification:** Real OCR/redaction must use a configured OCR provider. Real KYC/PAN/Aadhaar/liveness checks must use a legally obtained provider sandbox/live account. Do not scrape government portals. Do not implement unauthorized Aadhaar/PAN verification.



# 05 — Document Storage, Real OCR, and Redaction

## Objective

Implement document upload, checksuming, S3/MinIO storage, real OCR provider integration, and redacted document preview.

## Why this matters for the IDfy interview

IDfy's technical public material discusses document detection, information extraction, Aadhaar redaction, and tamper detection. This module is where the project becomes domain-relevant.

## Dependencies

- 01-04 complete.
- Object storage running.
- OCR provider selected.

## Before implementation, ask for these if missing

- Choose OCR provider: `google_vision`, `google_document_ai`, or `aws_textract`.
- Provide required OCR credentials if running external tests.
- Confirm allowed document types: default `pan_card`, `aadhaar_card`, `passport`, `driving_license`.

## Implementation instructions

1. Create document upload endpoint that returns a pre-signed upload URL or accepts multipart upload, depending on chosen implementation.
2. Store document metadata: case_id, doc_type, mime_type, storage_key, checksum_sha256, size_bytes, upload status.
3. Reject unsupported file types and oversized files.
4. Implement checksum calculation server-side after upload finalization.
5. Implement OCR worker job triggered after document finalization.
6. Implement OCR provider interface with exactly one configured live provider. No fake provider that returns success.
7. Store raw OCR text and bounding boxes in `documents.extracted_json` or a separate `document_extractions` table.
8. Implement redaction processor: detect Aadhaar-like numbers, PAN-like numbers, phone numbers, and OCR bounding boxes; create redacted image/PDF derivative.
9. Store redacted artifact under `redacted_storage_key`.
10. Expose safe preview endpoint that only serves redacted artifact to dashboard users.
11. Add risk signal if same checksum appears across two different applicants.
12. Add audit events for upload, OCR started, OCR completed, redaction completed, OCR failed.

## Testing instructions

Run local infrastructure test:

```bash
docker compose exec api pytest tests/documents/test_upload_storage.py -q
docker compose exec worker pytest tests/documents/test_redaction_rules.py -q
```

Run real OCR test:

```bash
RUN_EXTERNAL_TESTS=true docker compose exec worker pytest tests/external/test_real_ocr_provider.py -q
```

Expected:

- local storage uploads work against MinIO;
- checksum is persisted;
- redacted derivative is created from OCR output;
- if `RUN_EXTERNAL_TESTS=true` and OCR credentials are missing, the test fails clearly;
- dashboard/API never exposes unredacted artifact unless role explicitly permits it.


## Acceptance criteria

- Documents are stored in object storage, not DB blobs.
- OCR uses a real configured provider when external tests are enabled.
- Redacted preview exists.
- Duplicate checksum risk signal is created.

## What must be true after this MD is complete

- The project can show real document-processing pipeline.
- Sensitive data handling is visibly safer.
- No fake OCR success exists.

## Do not do this

- Do not hard-code secrets.
- Do not fake success if a required dependency is missing.
- Do not bypass database migrations.
- Do not skip audit events for sensitive actions.
- Do not introduce hidden global state that breaks multi-tenant isolation.


