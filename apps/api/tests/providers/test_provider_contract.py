"""Provider adapter contract tests (pure — no network, no credentials).

These exercise the real adapter's status mapping, HMAC signature verification,
and callback parsing against representative provider payloads. They never mark a
verification as passed in the system; the registry still requires real config.
"""

from __future__ import annotations

import hashlib
import hmac
import json

import pytest

from app.enums import VerificationStepStatus
from app.errors import ProviderNotConfiguredError
from app.verification.persona import PersonaProvider, map_status, risk_codes_for

WEBHOOK_SECRET = "whsec_test_123"


def _provider() -> PersonaProvider:
    return PersonaProvider(
        api_url="https://withpersona.com/api/v1",
        api_key="sk_test",
        webhook_secret=WEBHOOK_SECRET,
        template_id="itmpl_test",
    )


def test_registry_fails_loudly_when_unconfigured():
    # Default local env has no KYC provider configured.
    with pytest.raises(ProviderNotConfiguredError) as exc:
        from app.verification import get_verification_provider

        get_verification_provider()
    assert exc.value.code == "missing_provider_config"
    assert "KYC_PROVIDER" in exc.value.detail["message"]


def test_status_mapping_covers_normalized_states():
    assert map_status("approved") == VerificationStepStatus.succeeded
    assert map_status("completed") == VerificationStepStatus.succeeded
    assert map_status("declined") == VerificationStepStatus.failed
    assert map_status("failed") == VerificationStepStatus.failed
    assert map_status("needs_review") == VerificationStepStatus.needs_review
    assert map_status("pending") == VerificationStepStatus.running
    assert map_status(None) == VerificationStepStatus.provider_error


def test_failure_outcomes_produce_risk_codes():
    codes = risk_codes_for(VerificationStepStatus.failed, {})
    assert "identity_mismatch" in codes
    tamper = risk_codes_for(
        VerificationStepStatus.failed,
        {"data": {"attributes": {"fraud-flagged": True}}},
    )
    assert "tamper_suspected" in tamper


def _signed(body: dict) -> tuple[bytes, str]:
    payload = json.dumps(body).encode()
    ts = "1700000000"
    signed = f"{ts}.{payload.decode()}".encode()
    sig = hmac.new(WEBHOOK_SECRET.encode(), signed, hashlib.sha256).hexdigest()
    return payload, f"t={ts},v1={sig}"


def test_signature_verification_accepts_valid_rejects_tampered():
    provider = _provider()
    body = {"data": {"attributes": {"name": "inquiry.completed"}}}
    payload, header = _signed(body)

    assert provider.verify_callback_signature(payload=payload, signature_header=header) is True
    # Tampered body -> signature no longer matches.
    assert provider.verify_callback_signature(
        payload=payload + b"x", signature_header=header
    ) is False
    # Missing header -> rejected.
    assert provider.verify_callback_signature(payload=payload, signature_header=None) is False


def test_parse_callback_normalizes_status_and_ref():
    provider = _provider()
    body = {
        "data": {
            "type": "event",
            "attributes": {
                "name": "inquiry.declined",
                "payload": {
                    "data": {
                        "id": "inq_abc123",
                        "attributes": {"status": "declined"},
                    }
                },
            },
        }
    }
    parsed = provider.parse_callback(payload=json.dumps(body).encode())
    assert parsed.provider_ref == "inq_abc123"
    assert parsed.status == VerificationStepStatus.failed
    assert parsed.event_type == "inquiry.declined"
    assert "identity_mismatch" in parsed.risk_codes


def test_provider_implements_interface():
    from app.verification.base import VerificationProvider

    assert isinstance(_provider(), VerificationProvider)
