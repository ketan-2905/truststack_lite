# Testing Strategy

## Test Layers

| Layer | Tools | Coverage | Command |
|---|---|---|---|
| Unit | pytest | individual functions | `pytest tests/unit -q` |
| Integration | pytest + real DB | API + database | `pytest tests/integration -q` |
| External | pytest + gated | real providers | `RUN_EXTERNAL_TESTS=true pytest tests/external -q` |
| E2E | Playwright | full user journeys | `npm run test:e2e` |
| Load | k6 or curl | performance | `bash scripts/load-test.sh` |
| Security | pytest | auth, isolation, PII | `pytest tests/security -q` |

## Backend Tests

### Existing Test Coverage (MD 01-08)

```
tests/
├── conftest.py              # Shared fixtures (DB, API client, auth)
├── test_health.py           # Endpoint connectivity
├── documents/
│   ├── test_redaction_rules.py
│   └── test_upload_storage.py
├── events/
│   └── test_worker_jobs.py
├── external/
│   ├── test_persona_provider.py (gated by RUN_EXTERNAL_TESTS)
│   └── test_real_ocr_provider.py (gated by RUN_EXTERNAL_TESTS)
├── integration/
│   ├── test_cases_api.py
│   └── test_schema.py
├── privacy/
│   ├── test_consent_notices.py
│   ├── test_consent_receipts.py
│   └── test_minor_guardian_consent.py
├── providers/
│   ├── test_provider_contract.py
│   └── test_verification_api.py
├── risk/
│   ├── test_idempotent_recompute.py
│   ├── test_policy_decisions.py
│   └── test_signal_calculators.py
├── security/
│   ├── test_api_key_rotation.py
│   ├── test_auth.py
│   ├── test_tenant_isolation.py
│   ├── test_pii_log_redaction.py (NEW MD10)
│   ├── test_audit_coverage.py (NEW MD10)
│   └── test_upload_guards.py (NEW MD10)
├── webhooks/
│   ├── test_retries.py
│   └── test_signature.py
└── observability/
    └── test_metrics.py (NEW MD10)
```

### Running Backend Tests

```bash
# All tests
docker compose exec -T api pytest -q

# By category
docker compose exec -T api pytest tests/unit -q
docker compose exec -T api pytest tests/integration -q
docker compose exec -T api pytest tests/security -q

# With coverage
docker compose exec -T api pytest --cov=app --cov-report=html -q

# Only external tests (requires provider credentials)
RUN_EXTERNAL_TESTS=true docker compose exec -T api pytest tests/external -q

# Single test file
docker compose exec -T api pytest tests/security/test_auth.py -v
```

## Frontend Tests

### Existing Coverage

```
tests/
└── api.test.mjs  # Basic API helper tests
```

### Running Frontend Tests

```bash
# All tests
docker compose exec -T web npm test

# Watch mode for development
docker compose exec -T web npm test -- --watch

# With coverage
docker compose exec -T web npm test -- --coverage
```

## E2E Tests (Playwright)

Requires Playwright installation:

```bash
docker compose exec -T web npm install -D @playwright/test

# Run E2E
docker compose exec -T web npx playwright test

# Debug mode
docker compose exec -T web npx playwright test --debug
```

Example test scenarios to add:
- Login flow
- Applicant case creation
- Document upload
- Analyst review workflow
- Audit log search

## Load Testing

### Option 1: Simple curl-based (no deps)

```bash
bash scripts/load-test.sh
```

Runs 200 requests at 10 concurrent connections against `/health/live`.

### Option 2: k6 (better insights)

```bash
# Install k6: https://k6.io/docs/getting-started/installation

k6 run scripts/k6/cases.js --vus 20 --duration 60s
```

Measures:
- Throughput (requests/sec)
- Latency (p50, p95, p99)
- Error rate

### Targets for Interview Demo

- **Read latency**: p95 < 500ms for case list/detail
- **Write throughput**: 20 concurrent case submissions
- **Error rate**: < 1%
- **Sustained load**: 60 seconds at 20 concurrent VUs

## Static Analysis & Linting

### Backend

```bash
# Linting (ruff)
docker compose exec -T api ruff check app/

# Type checking (mypy)
docker compose exec -T api mypy app/ --strict

# Security scanning (bandit)
docker compose exec -T api bandit -r app/

# Complexity (radon)
docker compose exec -T api radon cc app/ -a
```

### Frontend

```bash
# Linting (eslint)
docker compose exec -T web npm run lint

# Type checking (tsc)
docker compose exec -T web npx tsc --noEmit
```

## CI Quality Gates

See `.github/workflows/ci.yml` for automated checks:

1. **Lint** — ruff check on `apps/api`
2. **Type check** — mypy (backend), tsc (frontend)
3. **Build** — Docker images build successfully
4. **Unit tests** — pytest on API
5. **Integration tests** — pytest with real DB
6. **Security scan** — Trivy on Docker images
7. **Coverage** — min 75% for critical modules
8. **Smoke test** — basic health checks

### Running CI Locally

```bash
# Using act (GitHub Actions runner locally)
act -j lint
act -j stack-test
act -j docker-build-scan
```

## External Provider Tests

These tests require real credentials and are gated by `RUN_EXTERNAL_TESTS=true`:

```bash
# Skip by default (tests return skipped)
docker compose exec -T api pytest tests/external -q

# Run with credentials configured
RUN_EXTERNAL_TESTS=true OCR_PROVIDER=google_vision \
  GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json \
  docker compose exec -T api pytest tests/external -q
```

If credentials are missing and `RUN_EXTERNAL_TESTS=true`, tests must fail loudly with a message like:
```
FAILED: OCR_PROVIDER set to google_vision but GOOGLE_APPLICATION_CREDENTIALS not found
```

## Test Data & Seeding

Seed data is auto-applied on migrations:

```bash
docker compose exec -T api python -m app.cli seed
```

Creates:
- 1 Tenant (acme)
- 1 Admin user
- 1 Analyst user
- 3 Applicants
- 3 Onboarding cases (various states)
- Sample audit events

## Debugging Tests

### Backend

```bash
# Verbose output
docker compose exec -T api pytest tests/ -vv

# Stop on first failure
docker compose exec -T api pytest tests/ -x

# Enter debugger on failure
docker compose exec -T api pytest tests/ --pdb

# Show print statements
docker compose exec -T api pytest tests/ -s
```

### Frontend

```bash
# Run single test
docker compose exec -T web npm test -- --testNamePattern="login"

# Watch mode
docker compose exec -T web npm test -- --watch
```

## Coverage Reports

### Backend

```bash
docker compose exec -T api pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

### Frontend

```bash
docker compose exec -T web npm test -- --coverage
# Open coverage/index.html in browser
```

## Test Failures

If a test fails:

1. **Read the error message** — includes file, line number, assertion
2. **Check logs** — `docker compose logs api` or `docker compose logs web`
3. **Run test in isolation** — `-k testname` flag to run only that test
4. **Debug with breakpoints** — use `--pdb` or `debugger`
5. **Check state** — verify database state, env vars, timestamps

Common issues:
- **Timing**: race conditions in async code → add explicit waits
- **Isolation**: tests affecting each other → use unique IDs, transactions rollback
- **Credentials**: missing env vars → check `.env` file
- **Port conflicts**: services already running → `docker compose down -v` before retry
