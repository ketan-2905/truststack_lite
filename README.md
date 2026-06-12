# TrustStack Lite

**Risk-adaptive onboarding platform** with document verification, consent governance, fraud detection, and analyst review workflows.

Built for the IDfy Software Engineer interview to demonstrate end-to-end ownership of identity, security, and scalability.

## Problem

Identity onboarding requires coordinating multiple systems: document storage, OCR, KYC verification, risk scoring, audit compliance, and human review. Manual integration is error-prone and slow. TrustStack Lite proves a unified, credible approach.

## Solution

1. **Applicant submits identity document** → OCR extracts fields + redacts PII
2. **Risk engine scores document** → rules-based decision (auto-approve / manual review)
3. **Analyst reviews risky cases** → approves, rejects, or escalates
4. **Signed webhook notifies client** → immutable audit trail
5. **System supports multi-tenancy, consent lifecycle, real provider adapters** → production-ready

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Next.js Applicant & Analyst UI              │
└───────────────────────────┬─────────────────────────────────────┘
                            │ (HTTP/JSON)
┌─────────────────────────┬─────────────────────────────────────┐
│     FastAPI Backend     │                                     │
│  (Auth, Cases, Risk,    │  PostgreSQL │ Redis │ MinIO/S3      │
│   Webhooks, Audit)      │                                     │
└─────────────────────────┬─────────────────────────────────────┘
                            │ (Job Queue)
┌─────────────────────────┬─────────────────────────────────────┐
│    ARQ Background       │                                     │
│    Worker               │ Real OCR Provider │ Real KYC Provider
│  (Document, Risk,       │ (Google / AWS)    │ (Persona / IDfy)
│   Webhooks)             │                                     │
└─────────────────────────┴─────────────────────────────────────┘

Observability: Prometheus, Grafana, structured JSON logs
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Git

### Local Development

```bash
# Clone and enter directory
cd truststack-lite

# Setup environment
cp .env.example .env

# Start all services (API, web, database, etc.)
docker compose up -d --build

# Wait for services to be healthy
bash scripts/wait-for-services.sh

# Verify stack is running
curl http://localhost:8000/health | jq .
```

Services will be available at:

| Service | URL | Login |
|---|---|---|
| **Web Dashboard** | http://localhost:3000 | See below |
| **API Docs** | http://localhost:8000/docs | — |
| **MinIO Console** | http://localhost:9001 | truststack / truststack-secret |
| **Prometheus** | http://localhost:9090 | — |
| **Grafana** | http://localhost:3001 | admin / admin |

### Demo Credentials

```
Tenant Slug: acme
Admin Email: admin@truststack.local
Admin Password: change-me-local

Analyst Email: analyst@truststack.local
Analyst Password: change-me-local
```

## Features

### Applicant Flow

- [x] Login with email/password
- [x] Create applicant + start onboarding case
- [x] Accept versioned consent notice + receipt
- [x] Upload identity document (image/PDF)
- [x] View case status with risk score
- [x] Audit timeline

### Analyst Dashboard

- [x] Metrics overview (total cases, pending review, approved, rejected)
- [x] Case list with status filter
- [x] Review queue (manual review tasks)
- [x] Review detail page with:
  - Risk score + severity
  - Reason codes (e.g., duplicate_artifact, missing_consent)
  - Redacted document preview
  - Audit timeline
  - Resolution form (approve/reject/escalate + notes)
- [x] Searchable audit log
- [x] Webhook endpoint management

### Backend

- [x] Multi-tenant isolation (API key + JWT auth)
- [x] RBAC (tenant_admin, analyst, viewer)
- [x] Consent ledger (immutable, versioned notices)
- [x] Document storage (MinIO S3-compatible)
- [x] OCR pipeline (Google Vision / Document AI / AWS Textract)
- [x] Redaction (server-side image masking)
- [x] Verification adapters (Persona, IDfy, Veriff, Onfido, etc.)
- [x] Risk engine (rules-based policy, explainable reason codes)
- [x] Async workers (ARQ + Redis)
- [x] Signed webhooks (HMAC-SHA256, retries, idempotency)
- [x] Audit logging (immutable, tenant-scoped)
- [x] PII redaction in logs
- [x] Prometheus metrics + Grafana dashboards

## Testing

### Run All Tests

```bash
# Backend unit + integration tests
docker compose exec -T api pytest -q

# Frontend tests
docker compose exec -T web npm test

# Smoke test (basic health checks)
bash scripts/smoke-test.sh

# Load test (p95 latency, error rate)
bash scripts/load-test.sh

# With coverage
docker compose exec -T api pytest --cov=app --cov-report=html -q
```

### Linting & Type Checking

```bash
# Backend
docker compose exec -T api ruff check app/

# Frontend
docker compose exec -T web npm run lint
```

### External Provider Tests (requires credentials)

```bash
# Only runs if OCR/KYC credentials are configured
RUN_EXTERNAL_TESTS=true docker compose exec -T api pytest tests/external -q
```

## API Documentation

OpenAPI schema available at **http://localhost:8000/docs**

Key endpoints:

- `POST /v1/auth/login` — JWT login
- `POST /v1/applicants` — Create applicant
- `POST /v1/onboarding-cases` — Start case
- `POST /v1/consent` — Record consent
- `POST /v1/documents` — Upload document
- `GET /v1/onboarding-cases/{id}` — Get case status
- `GET /v1/risk/decisions` — Get risk decision
- `POST /v1/review/tasks/{id}/resolve` — Resolve review
- `GET /v1/audit-events` — Audit log

All require `Authorization: Bearer <token>` header (except `/login`).

## Configuration

### OCR Provider

Choose one (or none for demo):

```env
# Google Cloud Vision (requires service account JSON)
OCR_PROVIDER=google_vision
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GOOGLE_CLOUD_PROJECT_ID=my-project

# Google Document AI
OCR_PROVIDER=google_document_ai
GOOGLE_CLOUD_PROJECT_ID=my-project
GOOGLE_DOCUMENT_AI_PROCESSOR_ID=processor-id
GOOGLE_DOCUMENT_AI_LOCATION=us

# AWS Textract
OCR_PROVIDER=aws_textract
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

Missing OCR → endpoints return `424 Failed Dependency` (no fallbacks).

### KYC/Verification Provider

Choose one (or none for demo):

```env
# Persona
VERIFY_PROVIDER=persona
PERSONA_API_KEY=...
PERSONA_TEMPLATE_ID=...

# IDfy (requires legal access)
VERIFY_PROVIDER=idfy
IDFY_API_KEY=...
IDFY_ACCOUNT_ID=...
```

Missing KYC → endpoints return `424 Failed Dependency`.

## Deployment

### Docker Compose (Production-like)

```bash
docker compose -f infra/docker-compose.prod-like.yml up -d --build
```

### Kubernetes

```bash
# Create namespace
kubectl apply -f infra/k8s/namespace.yaml

# Create secrets
kubectl create secret generic db-secret \
  --from-literal=url='postgresql://...' -n truststack-lite

# Deploy
kubectl apply -f infra/k8s/api-deployment.yaml
kubectl apply -f infra/k8s/worker-deployment.yaml
kubectl apply -f infra/k8s/web-deployment.yaml
kubectl apply -f infra/k8s/ingress.yaml
```

See [docs/deployment.md](docs/deployment.md) for detailed cloud instructions.

## Interview Talking Points

### Why This Project?

**Problem solved:** Identity onboarding is complex (OCR, KYC, risk, compliance, review). No single solution handles end-to-end credibly.

**Signals demonstrated:**
1. **End-to-end ownership** — all layers (frontend, API, async workers, DB)
2. **Scalability** — multi-tenant, async processing, Kubernetes-ready
3. **Cloud-native** — containers, managed services support, observability
4. **Fraud/risk tech** — rules-based scoring, reason codes, review queue
5. **Security & compliance** — audit trail, consent ledger, PII handling
6. **Strong testing** — unit, integration, load tests in CI
7. **Product thinking** — applicant flow, analyst UX, real provider integrations

### Trade-offs

- **No ML risk model** → rules-first is explainable, auditable
- **No video liveness** → would need certified PAD provider
- **No Aadhaar/PAN API** → would require legal sandbox

All intentional and documented.

## Documentation

- [docs/architecture.md](docs/architecture.md) — module breakdown
- [docs/security.md](docs/security.md) — threat model, controls
- [docs/testing.md](docs/testing.md) — test strategy, commands
- [docs/deployment.md](docs/deployment.md) — local, K8s, cloud
- [docs/tradeoffs.md](docs/tradeoffs.md) — intentional limitations

## License

MIT. Built for educational/interview purposes.

### Ports used

`3000` (web), `3001` (grafana), `8000` (api), `5432` (postgres), `6379`
(redis), `8888` (webhook receiver), `9000` (minio), `9001` (minio console),
`9090` (prometheus). Make sure these are free before starting.

### Smoke suites

```bash
bash scripts/smoke-test.sh           # core
bash scripts/smoke-test.sh auth      # MD 03
bash scripts/smoke-test.sh consent   # MD 04
bash scripts/smoke-test.sh risk      # MD 07
bash scripts/smoke-test.sh webhooks  # MD 08
bash scripts/replay-webhooks.sh      # re-enqueue failed webhook deliveries
```

## Verify the stack

```bash
docker compose ps                 # all core services healthy
curl -f http://localhost:8000/health
bash scripts/smoke-test.sh        # core infra smoke
bash scripts/smoke-test.sh auth   # + auth checks (MD 03)
bash scripts/smoke-test.sh consent# + consent checks (MD 04)
```

## Seed data

After the stack is up, apply migrations and load deterministic seed data:

```bash
bash scripts/seed.sh
```

This creates one tenant (`Acme Onboarding`), a tenant admin
(`admin@truststack.local` / `change-me-local`), an analyst
(`analyst@truststack.local` / `change-me-local`), one applicant, and one active
consent notice. Credentials are configurable via `SEED_*` env vars.

## Tests

```bash
docker compose exec api pytest -q          # api unit/integration/security/privacy
docker compose exec worker pytest -q       # worker queue round-trip
docker compose exec web npm test           # web utility tests
docker compose exec web npm run lint       # web lint (next lint)
bash scripts/load-test.sh                  # lightweight load on /health
```

## Repository layout

```text
truststack_lite/
  apps/
    api/      FastAPI backend (app/, tests/, alembic/, Dockerfile)
    worker/   RQ worker (app/, tests/, Dockerfile)
    web/      Next.js app (app/, lib/, tests/, Dockerfile)
  packages/
    openapi/  generated openapi.json
  infra/
    docker-compose.yml, prometheus/, grafana/
  scripts/    wait-for-services / seed / smoke-test / load-test
  docs/       architecture, security, demo notes
  .github/workflows/ci.yml
  .env.example
```

## Environment variables

All configuration is environment-driven; see [.env.example](.env.example) for
the full annotated list. Key groups:

- **Auth/crypto:** `JWT_SECRET`, token lifetimes.
- **Postgres:** `DATABASE_URL`, `TEST_DATABASE_URL`, `POSTGRES_*`.
- **Redis:** `REDIS_URL`.
- **Object storage:** `S3_ENDPOINT_URL`, `S3_*`, `MINIO_*`.
- **External providers (optional):** `OCR_PROVIDER` + `GOOGLE_APPLICATION_CREDENTIALS` / `AWS_TEXTRACT_REGION`; `KYC_PROVIDER` + `KYC_API_KEY` + `KYC_API_URL`. Leaving these blank is supported — the system reports `not_configured` and fails loudly at the endpoints that need them.
- **Consent/privacy:** `DEFAULT_JURISDICTION` (default `IN-DPDP`), `DEFAULT_LANGUAGES` (`en,hi`).
- **Seed:** `SEED_*`.

## Security & privacy notes

- API keys are stored hashed; raw keys are shown once at creation only.
- Passwords are hashed with Argon2id.
- All queries are tenant-scoped; cross-tenant reads are not possible via the API.
- Consent is a versioned, immutable ledger with receipts — not a checkbox.
- No legal claim of DPDP compliance is made; consent text is placeholder pending
  legal review.
