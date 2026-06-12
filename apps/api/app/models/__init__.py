"""SQLAlchemy ORM models for TrustStack Lite.

Importing this package imports every model so that ``Base.metadata`` is fully
populated (used by Alembic autogenerate and the test schema bootstrap).
"""

from app.models.api_key import TenantApiKey
from app.models.applicant import Applicant
from app.models.audit import AuditEvent
from app.models.base import Base
from app.models.consent import ConsentNotice, ConsentRecord
from app.models.document import Document
from app.models.event import DomainEvent
from app.models.idempotency import IdempotencyKey
from app.models.onboarding_case import OnboardingCase
from app.models.retention import RetentionRequest
from app.models.review import ReviewTask
from app.models.risk import RiskDecision, RiskSignal
from app.models.role import Role, UserRole
from app.models.tenant import Tenant
from app.models.user import User
from app.models.verification import VerificationStep
from app.models.webhook import WebhookDelivery, WebhookDeliveryAttempt, WebhookEndpoint

__all__ = [
    "Base",
    "Tenant",
    "User",
    "Role",
    "UserRole",
    "TenantApiKey",
    "Applicant",
    "OnboardingCase",
    "ConsentNotice",
    "ConsentRecord",
    "Document",
    "VerificationStep",
    "RiskSignal",
    "RiskDecision",
    "ReviewTask",
    "AuditEvent",
    "WebhookEndpoint",
    "WebhookDelivery",
    "WebhookDeliveryAttempt",
    "DomainEvent",
    "IdempotencyKey",
    "RetentionRequest",
]
