# TrustStack Lite Implementation Pack

**Project:** TrustStack Lite — risk-adaptive onboarding, consent governance, document verification, fraud/risk scoring, review operations, and webhook integration.

**Non-negotiable rule:** No fake success paths. Do not silently mock external systems. Do not add fallback providers that make tests pass without the configured real service. If a real external provider credential is missing, the relevant test must fail with a clear message saying exactly which environment variable is required.

**Local real infrastructure:** Docker Compose must run real PostgreSQL, Redis, MinIO/S3-compatible storage, backend API, worker, frontend, and observability services. Local MinIO is acceptable as real object storage for development; production must use AWS S3 or another real S3-compatible managed bucket.

**External verification:** Real OCR/redaction must use a configured OCR provider. Real KYC/PAN/Aadhaar/liveness checks must use a legally obtained provider sandbox/live account. Do not scrape government portals. Do not implement unauthorized Aadhaar/PAN verification.



# 14 — API Keys, Environment Variables, and Credential Checklist

## Objective

List every credential and environment variable required to run TrustStack Lite locally, run real external tests, and deploy to cloud.

## Hard truth

You asked for "real thing, no mock, no fallback." That means external verification cannot be completed unless you provide real credentials for a legally usable OCR/KYC/liveness provider. If you do not have those keys, the project must say **blocked by missing credentials**. Anything else is lying.

## Local infrastructure variables

These are required for one-command Docker local development.

```env
APP_ENV=local
API_BASE_URL=http://localhost:8000
WEB_BASE_URL=http://localhost:3000

POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=truststack
POSTGRES_USER=truststack
POSTGRES_PASSWORD=truststack_local_password

REDIS_URL=redis://redis:6379/0

OBJECT_STORAGE_PROVIDER=s3
S3_ENDPOINT=http://minio:9000
S3_REGION=ap-south-1
S3_BUCKET=truststack-local
S3_ACCESS_KEY_ID=minioadmin
S3_SECRET_ACCESS_KEY=minioadmin
S3_FORCE_PATH_STYLE=true

JWT_SECRET=change_this_local_32_chars_minimum
JWT_ACCESS_TTL_SECONDS=900
JWT_REFRESH_TTL_SECONDS=604800

ARGON2_MEMORY_COST=65536
ARGON2_TIME_COST=3
ARGON2_PARALLELISM=4

WEBHOOK_DEFAULT_SECRET=change_this_local_webhook_secret
```

## OCR provider variables

Choose exactly one provider for real OCR.

### Option A — Google Cloud Vision OCR

```env
OCR_PROVIDER=google_vision
GOOGLE_CLOUD_PROJECT_ID=
GOOGLE_APPLICATION_CREDENTIALS=/run/secrets/google-vision-service-account.json
```

Required credential:

- Google Cloud service-account JSON with Vision API enabled.

### Option B — Google Document AI

```env
OCR_PROVIDER=google_document_ai
GOOGLE_CLOUD_PROJECT_ID=
GOOGLE_DOCUMENT_AI_LOCATION=us
GOOGLE_DOCUMENT_AI_PROCESSOR_ID=
GOOGLE_APPLICATION_CREDENTIALS=/run/secrets/google-document-ai-service-account.json
```

Required credential:

- Google Cloud service-account JSON.
- Document AI processor ID.
- Correct processor location.

### Option C — AWS Textract

```env
OCR_PROVIDER=aws_textract
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_TEXTRACT_ROLE_ARN=
```

Required credential:

- AWS IAM user/role with Textract and S3 permissions.

## Identity/KYC/liveness provider variables

Use only providers you are legally allowed to use. Do not scrape official government portals.

### IDfy sandbox/live if you get access

```env
VERIFY_PROVIDER=idfy
IDFY_BASE_URL=
IDFY_API_KEY=
IDFY_ACCOUNT_ID=
IDFY_WEBHOOK_SECRET=
IDFY_ENV=sandbox
```

### Persona

```env
VERIFY_PROVIDER=persona
PERSONA_API_KEY=
PERSONA_API_VERSION=
PERSONA_WEBHOOK_SECRET=
PERSONA_TEMPLATE_ID=
PERSONA_ENV=sandbox
```

### Veriff

```env
VERIFY_PROVIDER=veriff
VERIFF_BASE_URL=
VERIFF_API_KEY=
VERIFF_SHARED_SECRET=
VERIFF_WEBHOOK_SECRET=
VERIFF_ENV=sandbox
```

### Entrust/Onfido

```env
VERIFY_PROVIDER=onfido
ONFIDO_API_TOKEN=
ONFIDO_REGION=
ONFIDO_WEBHOOK_SECRET=
ONFIDO_WORKFLOW_ID=
```

### Indian KYC aggregator, only with legal sandbox

```env
VERIFY_PROVIDER=signzy
SIGNZY_BASE_URL=
SIGNZY_CLIENT_ID=
SIGNZY_CLIENT_SECRET=
SIGNZY_WEBHOOK_SECRET=
```

or

```env
VERIFY_PROVIDER=surepass
SUREPASS_BASE_URL=
SUREPASS_API_KEY=
SUREPASS_WEBHOOK_SECRET=
```

or

```env
VERIFY_PROVIDER=hyperverge
HYPERVERGE_APP_ID=
HYPERVERGE_APP_KEY=
HYPERVERGE_BASE_URL=
HYPERVERGE_WEBHOOK_SECRET=
```

## Optional face/liveness provider variables

If you cannot get a KYC provider but want a real image/face check:

```env
FACE_PROVIDER=aws_rekognition
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
```

Be precise in README: AWS Rekognition face comparison is not equal to certified KYC/PAD compliance.

## Observability variables

```env
OTEL_SERVICE_NAME=truststack-lite-api
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
PROMETHEUS_ENABLED=true
LOG_LEVEL=info
LOG_PII_REDACTION=true
```

## CI variables

```env
CI=true
RUN_EXTERNAL_TESTS=false
TRIVY_SEVERITY=HIGH,CRITICAL
MIN_BACKEND_COVERAGE=75
```

For real external provider CI:

```env
RUN_EXTERNAL_TESTS=true
OCR_PROVIDER=...
VERIFY_PROVIDER=...
```

## Cloud deployment variables

```env
APP_ENV=production
API_BASE_URL=https://api.yourdomain.com
WEB_BASE_URL=https://yourdomain.com

DATABASE_URL=
REDIS_URL=

S3_REGION=ap-south-1
S3_BUCKET=
S3_ACCESS_KEY_ID=
S3_SECRET_ACCESS_KEY=

JWT_SECRET=
WEBHOOK_DEFAULT_SECRET=

SENTRY_DSN=
```

## Required accounts by feature

| Feature | Account/key required | Can build without it? | Can truthfully demo as real without it? |
|---|---|---:|---:|
| Local DB/queue/storage | None beyond Docker | Yes | Yes, local infra only |
| OCR | Google Vision / Document AI / AWS Textract | Yes, but OCR endpoint blocked | No |
| Redaction | OCR provider + local image processing | Partially | No, unless OCR succeeds |
| PAN/Aadhaar/KYC verification | IDfy/Signzy/Surepass/HyperVerge or equivalent legal sandbox | Adapter yes, live test no | No |
| Liveness/PAD | IDfy/Persona/Veriff/Onfido/HyperVerge or certified provider | Adapter yes, live test no | No |
| Face comparison | AWS Rekognition or equivalent | Adapter yes | Only face comparison, not certified KYC |
| Email/SMS | Not required for MVP | Yes | Not relevant |
| Webhooks | No third-party required | Yes | Yes |
| Observability | Local Prometheus/Grafana | Yes | Yes |
| Cloud deployment | AWS/Render/Fly/Railway/Neon/Upstash/S3 | Local only yes | No public demo without it |

## Final rule for implementation

If an MD needs a credential and it is missing, stop that specific external feature and ask for the exact missing credential. Do not create a fake provider. Do not add a fallback. Do not mark the feature complete.

