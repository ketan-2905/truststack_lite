# Security & Audit

## PII Handling

**Protected Data:**
- Identity document numbers (PAN, Aadhaar)
- Phone numbers, email addresses
- OCR-extracted raw text
- Provider API payloads

**Redaction Strategy:**
- Logs contain only safe metadata (IDs, counts, actions)
- Document content is redacted at display layer using bounding boxes
- Raw OCR text and provider responses never appear in logs
- Audit events reference document IDs, not content

## Audit Logging

Every sensitive action is immutably logged:

| Action | Resource | Logged Data |
|---|---|---|
| `consent.recorded` | consent_record | consent_id, case_id, notice_id |
| `document.uploaded` | document | doc_id, checksum, size |
| `case.approved` | onboarding_case | case_id, risk_score |
| `case.rejected` | onboarding_case | case_id, risk_score, reason |
| `review_task.resolved` | review_task | task_id, decision, notes |
| `provider_callback` | verification_step | step_id, provider, status |
| `auth.login` | user | user_id, tenant_id, roles |

Audit table guarantees:
- Immutable: once written, cannot be modified
- Tenant-scoped: each tenant only sees own events
- Timestamped with millisecond precision
- Includes actor (user_id), request_id for correlation

## Security Headers

API returns:
- `X-Content-Type-Options: nosniff` — prevent MIME-type sniffing
- `X-Frame-Options: DENY` — disable framing attacks
- `Strict-Transport-Security: max-age=31536000` — enforce HTTPS in cloud
- `Content-Security-Policy: default-src 'self'` — strict CSP

## Authentication & Authorization

**Auth Layer:**
- JWT with HS256 (HMAC-SHA256)
- Argon2id password hashing (secure default cost factors)
- Refresh token rotation with Redis JTI tracking

**Tenant Isolation:**
- All queries filtered by `tenant_id` at ORM level
- API key auth tied to tenant
- Cross-tenant access returns 403 Forbidden

**RBAC:**
- Roles: tenant_admin, analyst, viewer, system
- Enforced at endpoint + service layer
- UI respects roles (analyst-only routes)

## Secret Management

**Local Development:**
- Secrets in `.env` (git-ignored)
- Demo credentials seeded to DB, changed at deployment
- JWT secret in env var (min 32 bytes)
- S3 credentials in env vars

**Production (placeholder):**
- Assume AWS Secrets Manager or HashiCorp Vault
- Environment variables sourced from secret manager
- No hardcoded keys in code or images
- Rotation schedule for API keys, database passwords

## File Upload Protections

**Validations:**
- MIME type whitelist: `image/jpeg`, `image/png`, `application/pdf`
- Extension whitelist: `.jpg`, `.jpeg`, `.png`, `.pdf`
- Max size: 10 MB (configurable)
- SHA-256 checksum computed and stored
- Duplicate checksum detected (same document twice)

**Storage:**
- MinIO enforces access control (authenticated only)
- Object names do not leak applicant PII
- Redacted artifacts stored with separate namespace

## External Dependency Safety

**OCR Failure:**
- Missing OCR provider → 424 Failed Dependency
- No fallback extraction
- Task marked as `failed_dependency`

**KYC Failure:**
- Missing KYC provider → 424 Failed Dependency
- No fake verification success
- Case remains in `submitted` state

**Webhook Failure:**
- Dead-letter tracking for failed deliveries
- No silent drops
- Observability logs all webhook attempts

## Threat Model

### Threats Mitigated

1. **Brute Force Login**
   - Rate limiting: 10 auth attempts per minute per IP
   - Argon2id slows hash computation
   - Lockout after N attempts (configurable)

2. **Cross-Tenant Data Leak**
   - All queries filtered by tenant_id
   - API enforces tenant isolation
   - Audit logs are tenant-scoped

3. **Replay Attacks**
   - JTI (JWT ID) tracked in Redis
   - Refresh tokens cannot be reused
   - Idempotency keys prevent duplicate actions

4. **Man-in-the-Middle**
   - HTTPS enforced in production (HSTS header)
   - Webhook signatures (HMAC-SHA256) prevent spoofing

5. **PII Exfiltration via Logs**
   - Logs redact all sensitive data
   - OCR text never logged
   - Provider payloads never logged

### Known Limitations

- **No secret rotation automation** (requires deployment/ops setup)
- **No encryption at rest** (S3 server-side encryption not configured)
- **No DLP tools** (data loss prevention requires external service)
- **No video liveness** (no PAD beyond static image)
- **Real Aadhaar/PAN verification** requires legal sandbox access

## Compliance Notes

**DPDP (India):**
- Consent notices versioned and receipts immutable
- Withdrawal recorded as new audit event
- Retention requests honor deletion timelines
- Data minimization: only required fields stored

**GDPR (if applicable):**
- Right to access via audit log export
- Right to delete via retention request workflow
- Data processing agreement covers third-party providers

**PCI (if processing payments):**
- No payment data stored (out of scope)
- But document upload includes PII → strong controls needed
