# Tradeoffs: What's Intentionally Not Built

## Not Built

### 1. ML Risk Model
**Why we use rules instead:**
- Explainability matters in fraud (audit trail, compliance)
- Rules are deterministic (same input = same decision, always)
- Reason codes are human-readable ("duplicate_artifact", not "feature_12 = 0.8")
- Testing is simpler (no data drift, no retraining)
- Compliance easier (regulators can audit rules, not ML weights)

**Trade-off:** Rules may miss fraud patterns that ML could detect; maintainer must update rules as fraud tactics evolve.

### 2. Video Liveness / PAD (Presentation Attack Detection)
**Why not implemented:**
- Requires certified provider (Persona, Onfido, HyperVerge, etc.)
- Must comply with NIST/iBeta PAD standards
- Costs extra per verification
- Introduces latency (video processing is slow)

**Consequence:** System supports only static face photo verification. Spoofing with high-quality prints might succeed.

**Workaround:** Enable real Persona/Onfido integration by providing credentials in `.env`.

### 3. Real Aadhaar / PAN Verification
**Why not implemented:**
- Requires legal sandbox access from UIDAI / NSDL
- Application process is bureaucratic (6-12 weeks)
- Must comply with Aadhaar Act 2016 & MEITY guidelines
- Credential sharing severely restricted

**Consequence:** System has adapter structure but no live endpoint. Verification returns 424 if not configured.

**Workaround:** Integrate your own legal sandbox account (e.g., Signzy, Surepass with NSDL tie-up).

### 4. Encryption at Rest (S3)
**Why not configured by default:**
- Adds latency (minimal, but non-zero)
- Requires KMS key management (another service)
- Increases AWS bill slightly

**Trade-off:** Documents in S3 are not encrypted by default. In production, enable S3 server-side encryption (SSE-S3) via AWS console or Terraform.

### 5. Automatic Secret Rotation
**Why not automated:**
- Requires secret manager integration (AWS Secrets Manager, Vault)
- Need Lambda/k8s controller to rotate and redeploy
- Adds operational complexity

**Consequence:** Secrets must be rotated manually by ops team. Document rotation schedule in runbook.

### 6. Multi-Region Deployment
**Why not built:**
- Adds significant complexity (cross-region DB sync, S3 replication, etc.)
- Most interview audiences don't need it
- Can be added later with managed services (Aurora, DynamoDB)

**Trade-off:** Single region only. If region goes down, system is offline.

### 7. Automatic Scaling by Queue Depth
**Why not implemented:**
- Kubernetes HPA + custom metrics required
- ARQ queue depth metric must be exposed to Prometheus
- Needs testing under load

**Consequence:** Worker pod count must be scaled manually (or via CI/CD).

**Workaround:** Use Kubernetes `kubectl scale deployment worker --replicas=N` or set `.spec.replicas` in deployment YAML.

### 8. Rate Limiting by Tenant
**Why not per-tenant:**
- Would require distributed counter (Redis atomic ops, Lua scripts)
- Adds query latency for every request

**Current:** Global rate limits (10 auth attempts/min/IP).

**Trade-off:** Tenant A could consume rate limit quota meant for Tenant B (unfair).

**Workaround:** Implement in nginx/ingress controller if needed.

### 9. Mobile App
**Why not built:**
- Scope is already large
- Web app + React Native = duplicate effort
- Can be built on top of existing API

**Workaround:** Use progressive web app (PWA) features, or build native app using same API.

### 10. Stripe / Payment Processing
**Why not integrated:**
- Out of scope for identity/risk platform
- Would require PCI-DSS compliance (huge effort)
- Not relevant to interview

**Consequence:** No payment flow. System assumes B2B SaaS (tenant pays via enterprise agreement).

## Known Limitations

### 1. OCR Text Extraction Quality
**Limitation:** OCR quality depends on document image quality, angle, lighting.

**Mitigation:** Implement client-side validation (angle detection, sharpness check) before upload.

### 2. Webhook Delivery Guarantee
**Limitation:** "At-least-once" delivery, not "exactly-once". Retries could cause duplicate webhook calls.

**Mitigation:** Implement idempotent webhook handler on client side (check for duplicate delivery_id).

### 3. Audit Log Retention
**Limitation:** Audit table grows unbounded over time.

**Mitigation:** Implement retention policy (archive to cold storage after 7 years, per DPDP).

### 4. Performance: Case Listing
**Limitation:** List cases with many filters (`status`, `risk_severity`, `created_at`) could be slow without proper indexes.

**Mitigation:** Ensure indexes on (`tenant_id`, `created_at`, `status`, `risk_severity`). Monitor query performance in production.

### 5. Consent Notice Versioning
**Limitation:** No support for A/B testing notices (all users in a locale see the same version).

**Mitigation:** If A/B testing needed, create two notice versions explicitly and assign by user cohort.

## What You Should Add Before Production

1. **Secret rotation** — integrate AWS Secrets Manager, rotate quarterly
2. **Database backups** — daily automated backups to S3 or cross-region RDS
3. **DLP (Data Loss Prevention)** — tools like Cloudflare DLP or AWS Macie
4. **Incident response** — PagerDuty/Opsgenie for alerts, runbook for major incidents
5. **Legal review** — DPDP/GDPR compliance review before launch
6. **Penetration testing** — professional security audit
7. **Load testing** — run load test with real data patterns
8. **Disaster recovery** — test RTO/RPO (recovery time/point objectives)

## Intentional Simplifications for Interview

- **Single database instance** (not replicated) — good enough for interview demo
- **MinIO locally** instead of production S3 — faster setup
- **Demo seeded data** instead of user-generated — repeatability
- **No API rate limiting per tenant** — simpler auth
- **Rules-based risk** instead of ML — explainability
- **Synchronous auth** — simpler than OAuth/SAML

All are justified trade-offs for demonstrating competence in a time-boxed context.
