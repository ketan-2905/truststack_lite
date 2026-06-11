"""Constrained domain enumerations.

These back native PostgreSQL enum types (created by the Alembic migration) so the
database itself rejects invalid states — not just the application layer.
"""

from __future__ import annotations

import enum


class RoleName(enum.StrEnum):
    tenant_admin = "tenant_admin"
    analyst = "analyst"
    viewer = "viewer"
    system = "system"


class CaseState(enum.StrEnum):
    created = "created"
    consent_pending = "consent_pending"
    documents_pending = "documents_pending"
    verifying = "verifying"
    in_review = "in_review"
    approved = "approved"
    rejected = "rejected"
    abandoned = "abandoned"


class VerificationStepType(enum.StrEnum):
    document_ocr = "document_ocr"
    document_authenticity = "document_authenticity"
    pan_check = "pan_check"
    aadhaar_check = "aadhaar_check"
    liveness = "liveness"
    face_match = "face_match"
    sanctions_screening = "sanctions_screening"


class VerificationStepStatus(enum.StrEnum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    needs_review = "needs_review"
    provider_error = "provider_error"
    dependency_not_configured = "dependency_not_configured"


class DecisionType(enum.StrEnum):
    auto_approve = "auto_approve"
    manual_review = "manual_review"
    auto_reject = "auto_reject"
    approved = "approved"
    rejected = "rejected"
    blocked_dependency = "blocked_dependency"


class RiskSeverity(enum.StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ReviewStatus(enum.StrEnum):
    open = "open"
    assigned = "assigned"
    approved = "approved"
    rejected = "rejected"
    escalated = "escalated"


class WebhookDeliveryStatus(enum.StrEnum):
    pending = "pending"
    delivered = "delivered"
    failed = "failed"
    retrying = "retrying"
    dead_letter = "dead_letter"


class DocumentType(enum.StrEnum):
    pan = "pan"
    aadhaar = "aadhaar"
    passport = "passport"
    driving_license = "driving_license"
    voter_id = "voter_id"
    other = "other"


class DocumentStatus(enum.StrEnum):
    uploaded = "uploaded"
    processing = "processing"
    processed = "processed"
    failed = "failed"
    quarantined = "quarantined"


class ConsentType(enum.StrEnum):
    applicant = "applicant"
    guardian = "guardian"


class RetentionRequestState(enum.StrEnum):
    requested = "requested"
    approved = "approved"
    completed = "completed"
    rejected = "rejected"
