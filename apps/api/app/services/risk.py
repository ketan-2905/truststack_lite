"""Risk signal helpers shared by the document pipeline (MD 05), verification
adapters (MD 06), and the risk engine (MD 07)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums import RiskSeverity
from app.models.risk import RiskSignal


def add_signal(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    code: str,
    description: str,
    severity: RiskSeverity,
    weight: float = 0,
    evidence: dict | None = None,
    dedupe: bool = True,
) -> RiskSignal | None:
    """Append a risk signal. When ``dedupe`` is set, an identical (case, code)
    signal is not duplicated."""
    if dedupe:
        existing = db.scalar(
            select(RiskSignal).where(
                RiskSignal.case_id == case_id, RiskSignal.code == code
            )
        )
        if existing is not None:
            return existing

    signal = RiskSignal(
        tenant_id=tenant_id,
        case_id=case_id,
        code=code,
        description=description,
        severity=severity,
        weight=weight,
        evidence=evidence,
    )
    db.add(signal)
    db.flush()
    return signal


def list_signals(db: Session, tenant_id: uuid.UUID, case_id: uuid.UUID) -> list[RiskSignal]:
    stmt = (
        select(RiskSignal)
        .where(RiskSignal.tenant_id == tenant_id, RiskSignal.case_id == case_id)
        .order_by(RiskSignal.created_at.asc())
    )
    return list(db.scalars(stmt).all())
