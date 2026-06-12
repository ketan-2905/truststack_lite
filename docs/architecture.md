# Architecture

## Module Breakdown

### Frontend (`apps/web/`)

**Next.js 14 + React 18 + TypeScript**

Routes:
- `/login` — JWT login form
- `/dashboard/*` — Analyst views (cases, review queue, audit log, webhooks)
- `/applicant/*` — Applicant views (start case, upload document, view status)

API helpers: typed wrappers around `apiFetch` for all backend endpoints

Components: shared UI (LoadingSpinner, ErrorBanner, StatusBadge, NavBar)

### Backend API (`apps/api/app/`)

**FastAPI + SQLAlchemy + Alembic**

#### Core Layers

- `config.py` — environment loading, settings validation
- `db.py` — SQLAlchemy session, connection pool
- `security.py` — JWT creation/validation, password hashing
- `logging_config.py` — structured JSON logs, request correlation
- `middleware.py` — CORS, correlation ID, rate limiting, security headers
- `metrics.py` — Prometheus metrics collection

#### Domain Models (`models/`)

- `tenant.py` — tenant (multi-tenancy root)
- `user.py` — dashboard users
- `role.py` — RBAC roles
- `applicant.py` — end-user applicant
- `onboarding_case.py` — case lifecycle
- `document.py` — uploaded documents
- `consent.py` — consent notices + records
- `verification.py` — provider interactions
- `risk.py` — risk signals + decisions
- `review.py` — manual review tasks
- `audit.py` — immutable audit trail
- `webhook.py` — outbound webhooks
- `event.py` — domain events

#### Services (`services/`)

- `auth.py` — login, JWT, password hashing
- `tenants.py` — multi-tenancy enforcement
- `applicants.py` — applicant CRUD
- `cases.py` — case lifecycle
- `consent.py` — consent ledger operations
- `documents.py` — upload, storage, checksum
- `ocr.py` — OCR provider dispatch
- `verification.py` — KYC provider dispatch
- `risk.py` — risk engine orchestration
- `review.py` — review task assignment
- `webhooks.py` — webhook delivery, retries
- `audit.py` — audit event recording
- `events.py` — domain event emission

#### Routers (`routers/`)

- `auth.py` — POST `/v1/auth/login`, `/refresh`, `/logout`
- `applicants.py` — CRUD applicants
- `cases.py` — CRUD cases, case status
- `consent.py` — consent acceptance, timeline
- `documents.py` — upload, get, redacted preview
- `verification.py` — initiate verification, callback webhook
- `risk.py` — get risk decision, reason codes
- `review.py` — list tasks, get detail, resolve
- `audit.py` — list events, search
- `webhooks.py` — endpoint CRUD, test send

#### OCR Pipeline (`ocr/`)

- `base.py` — provider interface
- `google_vision.py` — Google Cloud Vision adapter
- `google_document_ai.py` — Document AI adapter
- `textract.py` — AWS Textract adapter
- `registry.py` — provider dispatch by env var

Returns OCR with bounding boxes → redaction layer masks PII

#### Verification Adapters (`verification/`)

- `base.py` — provider interface (create_session → callback → status)
- `persona.py` — Persona API adapter
- `registry.py` — provider dispatch by env var

Returns normalized verification state + reason for failure

#### Risk Engine (`risk/`)

- `engine.py` — orchestration
- `calculators.py` — pure signal functions
- `facts.py` — extract signals from case
- `policies/v1.py` — rules (hard blocks, thresholds, reason codes)

Policy returns: decision (approve/review/reject), score, reason codes

#### Tasks (`tasks/`)

- `documents.py` — async OCR job
- `risk.py` — async risk recomputation
- `webhooks.py` — async webhook delivery with retries

### Async Worker (`apps/api/app/worker.py`)

**ARQ (Redis-backed task queue)**

Starts on container command `python -m app.worker`. Processes jobs from Redis queue:

1. Document OCR → store bounding boxes
2. Risk recomputation → save score + decision
3. Webhook delivery → HMAC-SHA256 sign, retry up to 5x, dead-letter

### Database Schema (`alembic/versions/`)

**PostgreSQL 16**

Core tables:
- `tenants` — multi-tenancy boundary
- `users` — dashboard users
- `roles` — RBAC definitions
- `applicants` — end-user subjects
- `onboarding_cases` — case state machine
- `documents` — uploads (checksum, redacted URL)
- `consent_notices` — versioned policies
- `consent_records` — immutable receipts
- `verification_steps` — provider interactions
- `risk_signals` — intermediate calculations
- `risk_decisions` — final score + reason codes
- `review_tasks` — manual queue
- `audit_events` — immutable log
- `webhook_endpoints` — outbound targets
- `webhook_deliveries` — delivery attempts + retry tracking
- `domain_events` — event sourcing log

Indexes on: `tenant_id`, `case_id`, `created_at`, `status`

### Observability

**Prometheus** — scrapes `/metrics` every 30s:
- `http_requests_total` — request count by method/path
- `http_request_duration_seconds` — latency histogram
- `ocr_request_duration_seconds` — provider latency
- `case_decisions_total` — decision count by type
- `webhook_deliveries_total` — delivery count by endpoint
- Job queue depth (from Redis)

**Grafana** — pre-built dashboards in `infra/grafana/dashboards/truststack.json`

**Structured JSON logs** — every request logs `method`, `path`, `status_code`, `duration_ms`, `tenant_id`, `actor_id`, request_id

PII redacted (no raw OCR, provider payloads, document numbers)

## Data Flow

### Happy Path (Case Approval)

1. Applicant logs in (`/v1/auth/login`) → JWT token
2. Applicant creates case (`POST /v1/onboarding-cases`) → Case stored with `state=submitted`
3. Applicant uploads document (`POST /v1/documents`) → File to MinIO, async OCR job queued
4. Worker receives OCR job → calls real OCR provider → stores bounding boxes
5. Risk engine re-computes → policy evaluates → score < 40 → decision = `approved`
6. Webhook dispatched (async) → signed payload → client receives notification
7. Analyst logs in, sees case in dashboard with `state=approved`
8. Audit trail shows: created → submitted → ocr_complete → approved

### Risky Path (Manual Review)

1. Similar to happy path, but risk score >= 40
2. Risk engine sets decision = `manual_review`
3. Review task created
4. Analyst logs in, sees task in review queue
5. Analyst views detail page (risk score, reason codes, redacted preview, audit trail)
6. Analyst resolves with decision=`approved` + notes
7. Webhook sent with final decision
8. Case transitions to `approved`

## Scaling Considerations

### Horizontal Scale

- **API pods** — stateless, use JWT (no sessions) → any pod can handle any request
- **Worker pods** — read from same Redis queue → adds capacity
- **Database** — managed service (RDS, Cloud SQL) handles replicas/failover
- **Object storage** — S3 bucket scales automatically

### Vertical Scale

- **Worker RAM** — OCR is memory-heavy (image processing)
- **API CPU** — risk engine runs on CPU
- **Database** — index strategy on `tenant_id`, `case_id`, `created_at` for query performance

### Async Processing

- OCR/KYC happens in background (worker) → API responds quickly
- Webhook retries happen automatically (no human wait)
- Risk recomputation can run async if policy changes

## Error Handling

**Missing OCR Provider:**
```python
if not settings.ocr_configured:
    return JSONResponse(status_code=424, content={"error": "ocr_provider_not_configured"})
```

**Missing KYC Provider:**
```python
if not settings.kyc_configured:
    return JSONResponse(status_code=424, content={"error": "kyc_provider_not_configured"})
```

**Webhook Delivery Failure:**
- Retry with exponential backoff (2s base, 5 attempts max)
- Store failure reason in `webhook_deliveries` table
- Dashboard shows delivery status

**Database Connection Loss:**
- Health check (`/health/live`) fails
- Pod is removed from load balancer
- Kubernetes restarts pod

## Testing Strategy

- **Unit tests** (`tests/unit/`) — mock external services, test business logic
- **Integration tests** (`tests/integration/`) — real DB, real Redis, test API endpoints
- **External tests** (`tests/external/`) — gated by `RUN_EXTERNAL_TESTS=true`, require real provider credentials
- **Load tests** (`scripts/load-test.sh`) — curl loop, k6 scenarios
- **E2E tests** (via Playwright) — full applicant + analyst flow
