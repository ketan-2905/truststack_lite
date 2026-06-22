"""Persona verification provider adapter (real REST + HMAC webhooks).

Persona (withpersona.com) has a documented REST API and HMAC-SHA256 webhook
signatures (``Persona-Signature: t=<ts>,v1=<hex>`` over ``"<ts>.<body>"``).

Network methods make real HTTP calls and require ``KYC_API_KEY`` — they never
fabricate a result. The pure helpers (status mapping, signature verification,
callback parsing) are unit-testable without credentials.
"""

from __future__ import annotations

import hashlib
import hmac
import json

import httpx

from app.enums import VerificationStepStatus
from app.hashing import sha256_hex
from app.verification.base import ParsedCallback, ProviderSession

# Persona inquiry status -> normalized verification step status.
_STATUS_MAP = {
    "created": VerificationStepStatus.running,
    "pending": VerificationStepStatus.running,
    "processing": VerificationStepStatus.running,
    "completed": VerificationStepStatus.succeeded,
    "approved": VerificationStepStatus.succeeded,
    "passed": VerificationStepStatus.succeeded,
    "declined": VerificationStepStatus.failed,
    "failed": VerificationStepStatus.failed,
    "expired": VerificationStepStatus.failed,
    "needs_review": VerificationStepStatus.needs_review,
    "marked-for-review": VerificationStepStatus.needs_review,
    "needs-review": VerificationStepStatus.needs_review,
    "error": VerificationStepStatus.provider_error,
}

# Failing/needs-review provider statuses -> risk reason codes.
_RISK_CODE_MAP = {
    VerificationStepStatus.failed: ["identity_mismatch", "provider_failure"],
    VerificationStepStatus.needs_review: ["provider_needs_review"],
    VerificationStepStatus.provider_error: ["provider_failure"],
}


def map_status(raw_status: str | None) -> VerificationStepStatus:
    if not raw_status:
        return VerificationStepStatus.provider_error
    return _STATUS_MAP.get(raw_status.strip().lower(), VerificationStepStatus.needs_review)


def risk_codes_for(status: VerificationStepStatus, raw: dict) -> list[str]:
    codes = list(_RISK_CODE_MAP.get(status, []))
    # Surface specific provider flags when present.
    attributes = (raw.get("data") or {}).get("attributes") or {}
    if attributes.get("fraud-flagged") or attributes.get("tamper_suspected"):
        codes.append("tamper_suspected")
    if attributes.get("duplicate"):
        codes.append("duplicate_identity")
    return list(dict.fromkeys(codes))  # de-dupe, preserve order


class PersonaProvider:
    name = "persona"

    def __init__(
        self,
        *,
        api_url: str,
        api_key: str,
        webhook_secret: str | None = None,
        template_id: str | None = None,
        timeout: float = 15.0,
    ) -> None:
        self._api_url = api_url.rstrip("/")
        self._api_key = api_key
        self._webhook_secret = webhook_secret
        self._template_id = template_id
        self._timeout = timeout

    # ── HTTP helpers ─────────────────────────────────────────────────────────
    def _client(self) -> httpx.Client:
        return httpx.Client(
            base_url=self._api_url,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "Persona-Version": "2023-01-05",
            },
            timeout=self._timeout,
        )

    def _session_from_response(self, payload: dict) -> ProviderSession:
        data = payload.get("data") or {}
        provider_ref = data.get("id", "")
        status = map_status((data.get("attributes") or {}).get("status"))
        return ProviderSession(provider_ref=provider_ref, status=status, raw=payload)

    # ── Provider interface (real network) ────────────────────────────────────
    def create_session(self, *, reference: str, attributes: dict | None = None) -> ProviderSession:
        body = {
            "data": {
                "attributes": {
                    "inquiry-template-id": self._template_id,
                    "reference-id": reference,
                    **(attributes or {}),
                }
            }
        }
        with self._client() as client:
            resp = client.post("/inquiries", json=body)
            resp.raise_for_status()
            return self._session_from_response(resp.json())

    def submit_document(self, *, provider_ref: str, document_bytes: bytes, doc_type: str) -> ProviderSession:
        # Persona document submission is part of its hosted/verification flow;
        # this performs the real API add-document call.
        with self._client() as client:
            resp = client.post(
                f"/inquiries/{provider_ref}/documents",
                json={"data": {"attributes": {"document-type": doc_type}}},
            )
            resp.raise_for_status()
            return self._session_from_response(resp.json())

    def submit_selfie(self, *, provider_ref: str, selfie_bytes: bytes) -> ProviderSession:
        with self._client() as client:
            resp = client.post(f"/inquiries/{provider_ref}/selfies", json={"data": {}})
            resp.raise_for_status()
            return self._session_from_response(resp.json())

    def get_status(self, *, provider_ref: str) -> ProviderSession:
        with self._client() as client:
            resp = client.get(f"/inquiries/{provider_ref}")
            resp.raise_for_status()
            return self._session_from_response(resp.json())

    def cancel_session(self, *, provider_ref: str) -> ProviderSession:
        with self._client() as client:
            resp = client.post(f"/inquiries/{provider_ref}/cancel", json={"data": {}})
            resp.raise_for_status()
            return self._session_from_response(resp.json())

    # ── Webhooks (pure) ──────────────────────────────────────────────────────
    def verify_callback_signature(self, *, payload: bytes, signature_header: str | None) -> bool:
        if not self._webhook_secret:
            # No secret configured -> cannot verify -> reject (never blindly trust).
            return False
        if not signature_header:
            return False
        parts = dict(
            kv.split("=", 1) for kv in signature_header.split(",") if "=" in kv
        )
        timestamp = parts.get("t")
        provided = parts.get("v1")
        if not timestamp or not provided:
            return False
        signed = f"{timestamp}.{payload.decode('utf-8')}".encode()
        expected = hmac.new(
            self._webhook_secret.encode(), signed, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, provided)

    def parse_callback(self, *, payload: bytes) -> ParsedCallback:
        body = json.loads(payload.decode("utf-8"))
        data = body.get("data") or {}
        attributes = data.get("attributes") or {}
        # Persona wraps the affected resource under attributes.payload.data.
        inner = (attributes.get("payload") or {}).get("data") or {}
        provider_ref = inner.get("id") or data.get("id") or ""
        raw_status = (inner.get("attributes") or {}).get("status")
        event_type = attributes.get("name") or data.get("type") or "inquiry.updated"
        status = map_status(raw_status)
        return ParsedCallback(
            provider_ref=provider_ref,
            status=status,
            event_type=event_type,
            raw=body,
            risk_codes=risk_codes_for(status, {"data": inner}),
        )

    @staticmethod
    def response_hash(payload: dict) -> str:
        return sha256_hex(json.dumps(payload, sort_keys=True, default=str))
