"""Verification endpoint tests: 424 when unconfigured, and the signed callback
flow that updates a step and raises risk signals."""

from __future__ import annotations

import hashlib
import hmac
import json

from app.enums import VerificationStepStatus, VerificationStepType

WEBHOOK_SECRET = "whsec_test_xyz"


def _hdr(raw: str) -> dict:
    return {"X-API-Key": raw}


def test_start_verification_requires_provider_config(
    client, make_tenant, make_api_key, make_applicant, make_case
):
    tenant = make_tenant(slug="verif-1")
    _, raw = make_api_key(tenant)
    applicant = make_applicant(tenant)
    case = make_case(tenant, applicant)

    resp = client.post(
        f"/v1/onboarding-cases/{case.id}/verifications",
        json={"step_type": "document_authenticity"},
        headers=_hdr(raw),
    )
    assert resp.status_code == 424
    assert resp.json()["detail"]["code"] == "missing_provider_config"


def _configure_persona(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "kyc_provider", "persona")
    monkeypatch.setattr(settings, "kyc_api_url", "https://withpersona.com/api/v1")
    monkeypatch.setattr(settings, "kyc_api_key", "sk_test")
    monkeypatch.setattr(settings, "kyc_webhook_secret", WEBHOOK_SECRET)
    monkeypatch.setattr(settings, "kyc_template_id", "itmpl_test")


def _signed_callback(provider_ref: str, status: str) -> tuple[bytes, dict]:
    body = {
        "data": {
            "type": "event",
            "attributes": {
                "name": f"inquiry.{status}",
                "payload": {"data": {"id": provider_ref, "attributes": {"status": status}}},
            },
        }
    }
    payload = json.dumps(body).encode()
    ts = "1700000000"
    sig = hmac.new(
        WEBHOOK_SECRET.encode(), f"{ts}.{payload.decode()}".encode(), hashlib.sha256
    ).hexdigest()
    return payload, {"Persona-Signature": f"t={ts},v1={sig}"}


def _insert_step(db_session, tenant, case, provider_ref):
    from app.models.verification import VerificationStep

    step = VerificationStep(
        tenant_id=tenant.id,
        case_id=case.id,
        step_type=VerificationStepType.document_authenticity,
        status=VerificationStepStatus.running,
        provider="persona",
        provider_ref=provider_ref,
    )
    db_session.add(step)
    db_session.commit()
    return step


def test_callback_updates_step_and_creates_risk_signal(
    client, make_tenant, make_applicant, make_case, db_session, monkeypatch
):
    _configure_persona(monkeypatch)
    tenant = make_tenant(slug="verif-2")
    applicant = make_applicant(tenant)
    case = make_case(tenant, applicant)
    _insert_step(db_session, tenant, case, "inq_decline_1")

    payload, headers = _signed_callback("inq_decline_1", "declined")
    resp = client.post(
        "/v1/verifications/callback/persona", content=payload, headers=headers
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "failed"

    from sqlalchemy import text

    signal = db_session.execute(
        text("SELECT code FROM risk_signals WHERE tenant_id = :t"),
        {"t": str(tenant.id)},
    ).scalar()
    assert signal == "identity_mismatch"


def test_callback_rejects_invalid_signature(
    client, make_tenant, make_applicant, make_case, db_session, monkeypatch
):
    _configure_persona(monkeypatch)
    tenant = make_tenant(slug="verif-3")
    applicant = make_applicant(tenant)
    case = make_case(tenant, applicant)
    _insert_step(db_session, tenant, case, "inq_x")

    payload, _ = _signed_callback("inq_x", "approved")
    resp = client.post(
        "/v1/verifications/callback/persona",
        content=payload,
        headers={"Persona-Signature": "t=1,v1=deadbeef"},
    )
    assert resp.status_code == 401
