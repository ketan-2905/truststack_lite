"""Webhook HMAC signature signing/verification (pure)."""

from __future__ import annotations

from app.webhooks.signing import sign_payload, verify_signature


def test_valid_signature_verifies():
    secret = "whsec_abc"
    body = b'{"event":"case.created"}'
    header = sign_payload(secret, body, timestamp="1700000000")
    assert verify_signature(secret, body, header) is True


def test_tampered_body_fails():
    secret = "whsec_abc"
    body = b'{"event":"case.created"}'
    header = sign_payload(secret, body, timestamp="1700000000")
    assert verify_signature(secret, body + b" ", header) is False


def test_wrong_secret_fails():
    body = b'{"a":1}'
    header = sign_payload("secret-one", body, timestamp="1700000000")
    assert verify_signature("secret-two", body, header) is False


def test_missing_or_malformed_header_fails():
    assert verify_signature("s", b"{}", None) is False
    assert verify_signature("s", b"{}", "garbage") is False


def test_timestamp_tolerance_rejects_old():
    secret = "whsec_abc"
    body = b"{}"
    header = sign_payload(secret, body, timestamp="1000000000")  # far in the past
    assert verify_signature(secret, body, header, tolerance_seconds=300) is False
    # Without tolerance it still verifies the HMAC.
    assert verify_signature(secret, body, header) is True
