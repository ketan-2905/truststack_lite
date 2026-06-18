"""Verification step orchestration over the provider boundary.

Only normalized state and a response hash are persisted — never raw provider
identity payloads. Provider failures become risk signals.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums import RiskSeverity, VerificationStepStatus, VerificationStepType
from app.errors import NotFoundError
from app.hashing import sha256_hex
from app.models.onboarding_case import OnboardingCase
from app.models.verification import VerificationStep
from app.services import audit
from app.services import risk as risk_service
from app.verification import get_verification_provider
from app.verification.base import ParsedCallback, ProviderSession

# Risk reason code -> (severity, score weight).
_RISK_WEIGHTS: dict[str, tuple[RiskSeverity, float]] = {
    "identity_mismatch": (RiskSeverity.high, 45),
    "provider_failure": (RiskSeverity.medium, 25),
    "tamper_suspected": (RiskSeverity.critical, 70),
    "duplicate_identity": (RiskSeverity.high, 50),
    "provider_needs_review": (RiskSeverity.low, 10),
    "liveness_failed": (RiskSeverity.high, 45),
}


def _now() -> datetime:
    return datetime.now(UTC)


def start_verification(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    case: OnboardingCase,
    step_type: VerificationStepType,
) -> VerificationStep:
    """Create a provider session and persist the verification step.

    Raises ``ProviderNotConfiguredError`` (424) if no provider is configured —
    no fake session is ever created.
    """
    provider = get_verification_provider()
    session: ProviderSession = provider.create_session(reference=str(case.id))

    step = VerificationStep(
        tenant_id=tenant_id,
        case_id=case.id,
        step_type=step_type,
        status=session.status,
        provider=provider.name,
        provider_ref=session.provider_ref,
        response_hash=sha256_hex(str(session.raw)),
        request_payload={"reference": str(case.id), "step_type": step_type.value},
        response_payload={"status": session.status.value, "provider": provider.name},
        started_at=_now(),
    )
    db.add(step)
    db.flush()
    audit.record_event(
        db,
        tenant_id=tenant_id,
        actor_type="system",
        actor_id="verification",
        action="verification.started",
        resource_type="verification_step",
        resource_id=step.id,
        case_id=case.id,
        data={"step_type": step_type.value, "provider": provider.name, "provider_ref": session.provider_ref},
    )
    return step


def list_steps(db: Session, tenant_id: uuid.UUID, case_id: uuid.UUID) -> list[VerificationStep]:
    stmt = (
        select(VerificationStep)
        .where(VerificationStep.tenant_id == tenant_id, VerificationStep.case_id == case_id)
        .order_by(VerificationStep.created_at.asc())
    )
    return list(db.scalars(stmt).all())


def get_step_by_provider_ref(db: Session, provider_ref: str) -> VerificationStep | None:
    return db.scalar(
        select(VerificationStep).where(VerificationStep.provider_ref == provider_ref)
    )


def apply_callback(db: Session, parsed: ParsedCallback) -> VerificationStep:
    """Apply a parsed provider callback to its verification step (idempotent)."""
    step = get_step_by_provider_ref(db, parsed.provider_ref)
    if step is None:
        raise NotFoundError("Verification step for provider_ref")

    step.status = parsed.status
    step.response_payload = {
        "status": parsed.status.value,
        "event_type": parsed.event_type,
        "provider": step.provider,
    }
    step.response_hash = sha256_hex(str(parsed.raw))
    if parsed.status in {
        VerificationStepStatus.succeeded,
        VerificationStepStatus.failed,
        VerificationStepStatus.provider_error,
    }:
        step.completed_at = _now()
    db.flush()

    _signals_from_callback(db, step, parsed)

    audit.record_event(
        db,
        tenant_id=step.tenant_id,
        actor_type="system",
        actor_id="verification",
        action="verification.callback",
        resource_type="verification_step",
        resource_id=step.id,
        case_id=step.case_id,
        data={"status": parsed.status.value, "event_type": parsed.event_type},
    )
    return step


def _signals_from_callback(db: Session, step: VerificationStep, parsed: ParsedCallback) -> None:
    for code in parsed.risk_codes:
        severity, weight = _RISK_WEIGHTS.get(code, (RiskSeverity.medium, 20))
        risk_service.add_signal(
            db,
            tenant_id=step.tenant_id,
            case_id=step.case_id,
            code=code,
            description=f"Verification provider outcome: {code}",
            severity=severity,
            weight=weight,
            evidence={
                "step_id": str(step.id),
                "provider": step.provider,
                "provider_ref": step.provider_ref,
                "event_type": parsed.event_type,
            },
        )
