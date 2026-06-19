"""Verification endpoints: start a provider session, list steps, receive callbacks."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import ALL_TENANT_ROLES, WRITE_ROLES, Principal, require_roles
from app.errors import NotFoundError, UnauthorizedError
from app.schemas.verification import VerificationStartRequest, VerificationStepOut
from app.services import cases as case_service
from app.services import verification as verification_service
from app.verification import get_verification_provider

WRITER = require_roles(*WRITE_ROLES)
READER = require_roles(*ALL_TENANT_ROLES)

router = APIRouter(tags=["verification"])


@router.post(
    "/v1/onboarding-cases/{case_id}/verifications",
    response_model=VerificationStepOut,
    status_code=status.HTTP_201_CREATED,
)
def start_verification(
    case_id: uuid.UUID,
    payload: VerificationStartRequest,
    principal: Principal = Depends(WRITER),
    db: Session = Depends(get_db),
) -> VerificationStepOut:
    case = case_service.get_case(db, principal.tenant_id, case_id)
    # Raises 424 missing_provider_config when no provider is configured.
    step = verification_service.start_verification(
        db, tenant_id=principal.tenant_id, case=case, step_type=payload.step_type
    )
    return VerificationStepOut.model_validate(step)


@router.get(
    "/v1/onboarding-cases/{case_id}/verifications",
    response_model=list[VerificationStepOut],
)
def list_verifications(
    case_id: uuid.UUID,
    principal: Principal = Depends(READER),
    db: Session = Depends(get_db),
) -> list[VerificationStepOut]:
    case = case_service.get_case(db, principal.tenant_id, case_id)
    steps = verification_service.list_steps(db, principal.tenant_id, case.id)
    return [VerificationStepOut.model_validate(s) for s in steps]


@router.post("/v1/verifications/callback/{provider_name}", status_code=status.HTTP_200_OK)
async def verification_callback(
    provider_name: str,
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    """Provider status callback. Signature-verified; updates the step by
    provider_ref. Not tenant-scoped (the provider has no tenant context); the
    step itself carries the tenant."""
    provider = get_verification_provider()  # 424 if unconfigured
    if provider_name.lower() != provider.name:
        raise NotFoundError("Verification provider")

    body = await request.body()
    signature = request.headers.get("Persona-Signature") or request.headers.get("X-Signature")
    if not provider.verify_callback_signature(payload=body, signature_header=signature):
        raise UnauthorizedError("Invalid provider callback signature.")

    parsed = provider.parse_callback(payload=body)
    step = verification_service.apply_callback(db, parsed)
    return {"status": step.status.value, "step_id": str(step.id)}
