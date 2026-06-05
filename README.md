# TrustStack Lite

Risk-adaptive onboarding, consent governance, document verification, fraud/risk
scoring, review operations, and signed webhook integration — built as one
coherent, cloud-native system.

> **Status:** MD 01–08 implemented — repo + Docker infra, backend core & schema,
> auth/tenancy/API keys/RBAC, consent & privacy ledger, document storage + real
> OCR + redaction, verification provider adapters, the explainable risk engine,
> and async workers + signed webhooks. Remaining MDs (operator dashboard,
> observability, tests/load gates, deployment) build on this foundation.

## One-command local stack

```bash
cp .env.example .env
docker compose up --build
```

Real services only — PostgreSQL, Redis, MinIO (S3-compatible), the API, the
async **RQ worker (same image as the API)**, the Next.js web app, a local
webhook receiver, Prometheus, and Grafana. No mocked dependencies. If external
OCR/KYC credentials are absent, the system reports them as `not_configured` and
dependent endpoints return `424 Failed Dependency` rather than faking success.

### What is real vs. what needs credentials

- **Real now:** object storage (MinIO), the redaction image pipeline, the
  deterministic risk engine, domain events, signed webhook delivery with
  retries/backoff/replay, idempotent case creation.
- **Real adapters, gated on credentials:** OCR (AWS Textract / Google Vision via
  `OCR_PROVIDER`) and KYC verification (Persona via `KYC_PROVIDER`). Without
  credentials these fail loudly with `424` (`dependency_not_configured` /
  `missing_provider_config`) — no fake OCR/KYC success path exists. Enable real
  external tests with `RUN_EXTERNAL_TESTS=true`.

### Service URLs

| Service        | URL                              | Notes                          |
|----------------|----------------------------------|--------------------------------|
| API            | http://localhost:8000            | FastAPI                        |
| API health     | http://localhost:8000/health     | DB / Redis / storage + providers |
| OpenAPI docs   | http://localhost:8000/docs       | Swagger UI                     |
| OpenAPI schema | http://localhost:8000/openapi.json |                              |
| Web app        | http://localhost:3000            | Next.js (operator UI in MD 09) |
| MinIO console  | http://localhost:9001            | user/pass from `.env`          |
| Prometheus     | http://localhost:9090            |                                |
| Grafana        | http://localhost:3001            | admin/admin by default         |
| Webhook receiver | http://localhost:8888          | local echo receiver (dev/demo) |

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
