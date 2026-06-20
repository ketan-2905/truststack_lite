"""Risk endpoints: recompute a decision and read the explanation."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import ALL_TENANT_ROLES, WRITE_ROLES, Principal, require_roles
from app.risk.engine import latest_decision, recompute_case_risk
from app.schemas.risk import RiskDecisionOut, RiskSignalOut, RiskSummaryOut
from app.services import cases as case_service
from app.services import risk as risk_service

WRITER = require_roles(*WRITE_ROLES)
READER = require_roles(*ALL_TENANT_ROLES)

router = APIRouter(prefix="/v1/onboarding-cases", tags=["risk"])


@router.post("/{case_id}/risk/recompute", response_model=RiskDecisionOut)
def recompute_risk(
    case_id: uuid.UUID,
    principal: Principal = Depends(WRITER),
    db: Session = Depends(get_db),
) -> RiskDecisionOut:
    decided_by_user = (
        uuid.UUID(principal.actor_id)
        if principal.actor_type == "user" and principal.actor_id
        else None
    )
    decision = recompute_case_risk(
        db,
        tenant_id=principal.tenant_id,
        case_id=case_id,
        decided_by="user" if decided_by_user else "system",
        decided_by_user_id=decided_by_user,
    )
    return RiskDecisionOut.model_validate(decision)


@router.get("/{case_id}/risk", response_model=RiskSummaryOut)
def get_risk(
    case_id: uuid.UUID,
    principal: Principal = Depends(READER),
    db: Session = Depends(get_db),
) -> RiskSummaryOut:
    case = case_service.get_case(db, principal.tenant_id, case_id)
    decision = latest_decision(db, principal.tenant_id, case.id)
    signals = risk_service.list_signals(db, principal.tenant_id, case.id)
    return RiskSummaryOut(
        decision=RiskDecisionOut.model_validate(decision) if decision else None,
        signals=[RiskSignalOut.model_validate(s) for s in signals],
    )


@router.get("/{case_id}/risk/signals", response_model=list[RiskSignalOut])
def list_risk_signals(
    case_id: uuid.UUID,
    principal: Principal = Depends(READER),
    db: Session = Depends(get_db),
) -> list[RiskSignalOut]:
    case = case_service.get_case(db, principal.tenant_id, case_id)
    signals = risk_service.list_signals(db, principal.tenant_id, case.id)
    return [RiskSignalOut.model_validate(s) for s in signals]
