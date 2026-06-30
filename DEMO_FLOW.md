# TrustStack Lite — Demo Flow Visual Guide

## 🎬 Complete User Journey (Visual)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        START HERE                                    │
│                  http://localhost:3000                               │
└─────────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │   Login Screen     │
                    │                    │
                    │ Email: admin@..    │
                    │ Password: ****     │
                    │ Tenant: acme       │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────────────┐
                    │   Dashboard Home           │
                    │                            │
                    │ 📊 Metrics Cards:          │
                    │   • Total Cases: 1         │
                    │   • Pending Review: 0      │
                    │   • Approved: 1            │
                    │   • Rejected: 0            │
                    └─────────┬──────────────────┘
                              │
                    ┌─────────▼──────────────────┐
                    │  Choose User Role          │
                    │                            │
                    │  👤 Admin/Applicant        │
                    │     or                     │
                    │  👔 Switch to Analyst      │
                    └──────────┬─────────────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
    ┌───────────▼──────────────┐  ┌─────────▼─────────────────┐
    │  APPLICANT FLOW           │  │  ANALYST DASHBOARD        │
    │  (Identity Submission)    │  │  (Review & Approval)      │
    └───────────┬──────────────┘  └─────────┬─────────────────┘
                │                            │
    ┌───────────▼──────────────────────┐    │
    │ 1️⃣ START CASE                     │    │
    │ ✏️  Fill form:                     │    │
    │   • First Name: John              │    │
    │   • Last Name: Doe                │    │
    │   • Email: john@example.com       │    │
    │   • Phone: +91 9876543210         │    │
    │   • Document: AADHAR              │    │
    │ ✅ Click: "Create & Start Case"   │    │
    └───────────┬──────────────────────┘    │
                │                            │
    ┌───────────▼──────────────────────┐    │
    │ 2️⃣ ACCEPT CONSENT                │    │
    │ 📋 View notice text               │    │
    │    (versioned, immutable)         │    │
    │ ✅ Click: "Accept Consent"        │    │
    │                                   │    │
    │ 🔐 Audit event recorded:          │    │
    │    • consent.recorded             │    │
    └───────────┬──────────────────────┘    │
                │                            │
    ┌───────────▼──────────────────────┐    │
    │ 3️⃣ UPLOAD DOCUMENT               │    │
    │ 📄 Select image/PDF file          │    │
    │ ⏳ Processing:                     │    │
    │   • File → MinIO (S3)             │    │
    │   • Checksum computed             │    │
    │   • OCR queued to Redis           │    │
    │   • Risk engine evaluates         │    │
    │                                   │    │
    │ 🔐 Audit events:                  │    │
    │    • document.uploaded            │    │
    │    • risk_evaluation.completed    │    │
    └───────────┬──────────────────────┘    │
                │                            │
    ┌───────────▼──────────────────────┐    │
    │ 4️⃣ VIEW CASE STATUS              │    │
    │ ✅ Decision: APPROVED             │    │
    │ 📊 Risk Score: 15 (Low)           │    │
    │ 🏷️  Reason Codes: (none)          │    │
    │ 📑 Audit Timeline:                │    │
    │    • case.created                 │    │
    │    • consent.recorded             │    │
    │    • document.uploaded            │    │
    │    • risk_evaluation.completed    │    │
    │    • case.approved                │    │
    │                                   │    │
    │ 🔐 Webhook sent (signed)          │    │
    └───────────┬──────────────────────┘    │
                │                            │
                │                  ┌────────▼────────────────────┐
                │                  │ VIEW CASES LIST             │
                │                  │                             │
                │                  │ 📋 Table:                   │
                │                  │   John Doe | APPROVED | 15  │
                │                  │                             │
                │                  │ 🔍 Filters:                 │
                │                  │   • All                     │
                │                  │   • Submitted               │
                │                  │   • Approved                │
                │                  │   • Rejected                │
                │                  │                             │
                │                  │ ➜ Click row → Case detail   │
                │                  └────────┬────────────────────┘
                │                           │
                │                  ┌────────▼────────────────────┐
                │                  │ REVIEW QUEUE                │
                │                  │                             │
                │                  │ 🔍 Pending tasks:           │
                │                  │   (empty - auto-approved)   │
                │                  │                             │
                │                  │ 💡 If high-risk case:      │
                │                  │   • Would show task here    │
                │                  │   • Analyst clicks to view  │
                │                  │   • Reviews risk score      │
                │                  │   • Sees reason codes       │
                │                  │   • Views doc preview       │
                │                  │   • Resolves: approve/      │
                │                  │     reject/escalate         │
                │                  └────────┬────────────────────┘
                │                           │
                │                  ┌────────▼────────────────────┐
                │                  │ AUDIT LOG                   │
                │                  │                             │
                │                  │ 🔍 Immutable events:        │
                │                  │   2026-06-30 16:10          │
                │                  │   case.created              │
                │                  │   consent.recorded          │
                │                  │   document.uploaded         │
                │                  │   risk_evaluation           │
                │                  │   case.approved             │
                │                  │                             │
                │                  │ 🔐 PII redacted:            │
                │                  │   (no doc numbers, OCR,     │
                │                  │    phone, email)            │
                │                  │                             │
                │                  │ 🔍 Search/filter by:        │
                │                  │   • Action type             │
                │                  │   • Resource type           │
                │                  │   • Actor                   │
                │                  └────────┬────────────────────┘
                │                           │
                │                  ┌────────▼────────────────────┐
                │                  │ WEBHOOK MANAGEMENT          │
                │                  │                             │
                │                  │ ➕ Create endpoint:         │
                │                  │    URL, events              │
                │                  │                             │
                │                  │ 🔑 View secret:             │
                │                  │    HMAC-SHA256 key          │
                │                  │                             │
                │                  │ 📤 Test send:               │
                │                  │    Sample payload           │
                │                  │                             │
                │                  │ 📊 View history:            │
                │                  │    Delivery status, retries │
                │                  └────────┬────────────────────┘
                │                           │
                │                  ┌────────▼────────────────────┐
                │                  │ LOGOUT                      │
                │                  │ ✅ Back to login            │
                │                  └────────────────────────────┘
                │
                └─────────────────────────────────────────────
```

---

## 🔄 Data Flow Behind the Scenes

```
┌──────────────────────────────────────────────────────────────────────┐
│                      FRONTEND (Next.js)                              │
│                    http://localhost:3000                             │
│  - Login form, dashboard, case flows, review pages                   │
│  - Real API calls (no fake data)                                     │
└────────────────────────┬─────────────────────────────────────────────┘
                         │ (JWT Token in Authorization Header)
                         │ HTTP/JSON
                         │
┌────────────────────────▼─────────────────────────────────────────────┐
│                      API BACKEND (FastAPI)                           │
│                    http://localhost:8000                             │
│                                                                       │
│  POST /v1/auth/login ────────────────────────► JWT Token             │
│  POST /v1/applicants ────────────────────────► Create applicant      │
│  POST /v1/onboarding-cases ──────────────────► Start case            │
│  POST /v1/consent ───────────────────────────► Record consent        │
│  POST /v1/documents ────────────────────────► Upload document        │
│  GET  /v1/risk/decisions ───────────────────► Get risk score         │
│  POST /v1/review/tasks/{id}/resolve ────────► Resolve task           │
│  GET  /v1/audit-events ─────────────────────► Audit log              │
│  GET  /v1/webhooks ─────────────────────────► List webhooks          │
│                                                                       │
│  All responses: JSON with proper error codes                         │
│  - 200 OK                                                            │
│  - 401 Unauthorized                                                  │
│  - 404 Not Found                                                     │
│  - 424 Failed Dependency (missing OCR/KYC)                           │
└──┬────────────────────────────────────┬─────────────────────┬───────┘
   │                                    │                     │
   │ (Job Queue)                        │ (Direct queries)    │ (API Docs)
   │                                    │                     │
   │            HTTP/Swagger
   │            http://localhost:8000/docs
   │
┌──▼────────────────────────────────────▼─────────────────────┬───────┐
│  REDIS QUEUE      │      POSTGRESQL       │      MinIO       │       │
│  (Background)     │      (Database)       │      (Storage)   │       │
│                   │                       │                  │       │
│  ARQ job queue    │  - Tenants            │  Document files  │       │
│  for:             │  - Users              │  (encrypted)     │       │
│                   │  - Applicants         │                  │       │
│  1. OCR jobs      │  - Cases              │  Redacted        │       │
│  2. Risk engine   │  - Documents          │  previews        │       │
│  3. Webhooks      │  - Consent            │                  │       │
│                   │  - Verification       │                  │       │
│                   │  - Risk Decisions     │                  │       │
│                   │  - Audit Trail        │                  │       │
│                   │  - Webhooks           │                  │       │
│                   │  - Events             │                  │       │
│                   │                       │                  │       │
│                   │  Indexes:             │                  │       │
│                   │  - tenant_id          │                  │       │
│                   │  - case_id            │                  │       │
│                   │  - created_at         │                  │       │
│                   │  - status             │                  │       │
└────────────────────────────────────────────────────────────┬───────┘
                                                              │
                                                    ┌─────────▼────────┐
                                                    │ OBSERVABILITY    │
                                                    │                  │
                                                    │ Prometheus       │
                                                    │ :9090            │
                                                    │                  │
                                                    │ Grafana          │
                                                    │ :3001            │
                                                    │                  │
                                                    │ • Metrics        │
                                                    │ • Dashboards     │
                                                    │ • Alerts         │
                                                    └──────────────────┘
```

---

## 📊 Request/Response Examples

### **1. Login**
```
REQUEST:
POST http://localhost:8000/v1/auth/login
{
  "email": "admin@truststack.local",
  "password": "change-me-local",
  "tenant_slug": "acme"
}

RESPONSE:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "00000000-0000-4000-8000-000000000002",
    "email": "admin@truststack.local",
    "role": "tenant_admin"
  }
}
```

### **2. Create Case**
```
REQUEST:
POST http://localhost:8000/v1/onboarding-cases
Authorization: Bearer eyJ0eXAiOiJKV1Q...
{
  "applicant_id": "00000000-0000-4000-8000-000000000004"
}

RESPONSE:
{
  "id": "case-uuid-123",
  "applicant_id": "applicant-uuid-456",
  "tenant_id": "tenant-uuid-789",
  "state": "created",
  "risk_score": null,
  "decision": null,
  "created_at": "2026-06-30T16:10:14Z",
  "updated_at": "2026-06-30T16:10:14Z"
}
```

### **3. Upload Document**
```
REQUEST:
POST http://localhost:8000/v1/documents
Authorization: Bearer eyJ0eXAiOiJKV1Q...
Content-Type: multipart/form-data

file: <binary image data>
case_id: "case-uuid-123"
document_type: "AADHAR"

RESPONSE:
{
  "id": "doc-uuid-111",
  "case_id": "case-uuid-123",
  "file_name": "aadhar.jpg",
  "file_size": 102400,
  "content_type": "image/jpeg",
  "checksum": "sha256:a1b2c3d4...",
  "redacted_url": "http://localhost:9000/truststack-documents/doc-redacted-111.jpg",
  "upload_status": "uploaded",
  "ocr_status": "queued",
  "created_at": "2026-06-30T16:10:20Z"
}
```

### **4. Get Risk Decision**
```
REQUEST:
GET http://localhost:8000/v1/risk/decisions?case_id=case-uuid-123
Authorization: Bearer eyJ0eXAiOiJKV1Q...

RESPONSE:
{
  "case_id": "case-uuid-123",
  "risk_score": 15,
  "severity": "low",
  "decision": "approved",
  "reason_codes": [],
  "evaluated_at": "2026-06-30T16:10:45Z",
  "policy_version": "v1",
  "signals": {
    "document_quality": 85,
    "consent_present": true,
    "applicant_info_complete": true,
    "duplicate_check": false
  }
}
```

### **5. Get Audit Events**
```
REQUEST:
GET http://localhost:8000/v1/audit-events?limit=5
Authorization: Bearer eyJ0eXAiOiJKV1Q...

RESPONSE:
{
  "events": [
    {
      "id": "event-1",
      "timestamp": "2026-06-30T16:10:14Z",
      "action": "case.created",
      "resource_type": "onboarding_case",
      "resource_id": "case-uuid-123",
      "actor_id": "user-id-1",
      "actor_type": "user",
      "status": "success",
      "details": {}
    },
    {
      "id": "event-2",
      "timestamp": "2026-06-30T16:10:20Z",
      "action": "document.uploaded",
      "resource_type": "document",
      "resource_id": "doc-uuid-111",
      "actor_id": "user-id-1",
      "actor_type": "user",
      "status": "success",
      "details": {
        "file_size": 102400,
        "checksum": "sha256:a1b2c3d4..."
      }
    }
  ],
  "total": 5
}
```

---

## 🎯 Key Interactions on UI

### **Status Badges**
| Badge | Meaning | Color |
|---|---|---|
| ✅ APPROVED | Auto-approved | Green |
| ⏳ PENDING_REVIEW | Needs analyst | Yellow |
| ❌ REJECTED | Document rejected | Red |
| 🔄 PROCESSING | OCR in progress | Blue |

### **Risk Scores**
| Range | Severity | Decision |
|---|---|---|
| 0-20 | ✅ Low | Auto-approved |
| 20-40 | ⚠️ Medium | Auto-approved |
| 40-60 | 🟡 High | Manual review |
| 60-80 | 🔴 Very High | Manual review |
| 80-100 | ⛔ Critical | Manual review + escalate |

### **Reason Codes** (Appear in Review)
```
duplicate_artifact       → Document appears to be duplicate
missing_consent         → Consent not accepted
poor_document_quality   → Image quality too low
invalid_applicant_data  → Applicant info incomplete
fraud_signal_detected   → System detected potential fraud
```

---

## ✨ Behind-the-Scenes Magic

When you upload a document:

```
1. FILE UPLOAD
   └─► MinIO stores file
   └─► SHA-256 checksum computed
   └─► DB records document metadata

2. OCR JOB QUEUED
   └─► Redis queue receives job
   └─► Worker picks up job
   └─► (Returns 424 if no OCR provider configured)

3. DOCUMENT PROCESSING
   └─► Bounding boxes extracted
   └─► PII detection (Aadhaar, PAN, phone)
   └─► Redaction applied
   └─► Results stored in DB

4. RISK ENGINE EVALUATION
   └─► Extract signals from case
   └─► Evaluate fraud rules
   └─► Calculate risk score
   └─► Determine decision (approve/review)
   └─► Store decision in DB

5. AUDIT LOG
   └─► document.uploaded → recorded
   └─► risk_evaluation.completed → recorded
   └─► case.approved/manual_review → recorded

6. WEBHOOK DELIVERY
   └─► Generate signed payload (HMAC-SHA256)
   └─► Queue delivery attempts
   └─► Retry up to 5 times on failure
   └─► Store delivery status
```

---

## 🚀 Performance Expectations

| Operation | Time |
|---|---|
| Login | < 100ms |
| Load dashboard | < 200ms |
| Create case | < 50ms |
| Upload document (5MB) | < 500ms |
| OCR processing | 2-10s (async) |
| Risk evaluation | < 200ms |
| Get audit log (100 records) | < 300ms |

---

## 📋 Demo Checklist

Before presenting:

- [ ] Stack running: `docker compose ps` shows 9 healthy containers
- [ ] Database seeded: `bash scripts/seed.sh` completes
- [ ] Frontend loads: `http://localhost:3000` accessible
- [ ] API responds: `curl http://localhost:8000/health` returns 200
- [ ] Credentials work: admin@truststack.local / change-me-local
- [ ] Metrics available: `http://localhost:9090` accessible
- [ ] Grafana dashboard: `http://localhost:3001` (admin/admin)

After each interaction:

- [ ] Check audit log for events recorded
- [ ] Verify no errors in `docker compose logs`
- [ ] Confirm webhook "signed" in logs
- [ ] Review metrics spike in Prometheus

---

**Ready to demo! 🎬**

