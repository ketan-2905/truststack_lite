"""HMAC-SHA256 webhook signatures (Stripe-style ``t=<ts>,v1=<hex>``).

The signed string is ``f"{timestamp}.{body}"``; receivers recompute the HMAC
with the shared endpoint secret to verify authenticity and integrity.
"""

from __future__ import annotations

import hashlib
import hmac
import time

SIGNATURE_HEADER = "X-TrustStack-Signature"
EVENT_HEADER = "X-TrustStack-Event"
DELIVERY_HEADER = "X-TrustStack-Delivery"


def _compute(secret: str, timestamp: str, body: bytes) -> str:
    signed = f"{timestamp}.{body.decode('utf-8')}".encode()
    return hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()


def sign_payload(secret: str, body: bytes, *, timestamp: str | None = None) -> str:
    ts = timestamp or str(int(time.time()))
    return f"t={ts},v1={_compute(secret, ts, body)}"


def verify_signature(
    secret: str,
    body: bytes,
    signature_header: str | None,
    *,
    tolerance_seconds: int | None = None,
) -> bool:
    if not signature_header:
        return False
    parts = dict(kv.split("=", 1) for kv in signature_header.split(",") if "=" in kv)
    ts = parts.get("t")
    provided = parts.get("v1")
    if not ts or not provided:
        return False
    if tolerance_seconds is not None:
        try:
            if abs(int(time.time()) - int(ts)) > tolerance_seconds:
                return False
        except ValueError:
            return False
    expected = _compute(secret, ts, body)
    return hmac.compare_digest(expected, provided)
