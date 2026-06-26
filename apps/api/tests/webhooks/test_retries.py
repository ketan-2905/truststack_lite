"""Webhook delivery retries, dead-letter (failed), and replay.

Deliveries target an unroutable local port so the HTTP attempt really fails
(connection refused) — no mock. Backoff/attempt limits are tightened via config.
"""

from __future__ import annotations

from sqlalchemy import text

from app.enums import WebhookDeliveryStatus
from app.services import webhooks as webhook_service

UNREACHABLE_URL = "http://127.0.0.1:1/webhook"  # port 1 -> connection refused


def _tighten(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "webhook_max_attempts", 3)
    monkeypatch.setattr(settings, "webhook_backoff_base_seconds", 1)
    monkeypatch.setattr(settings, "webhook_timeout_seconds", 2.0)


def _make_delivery(db_session, tenant, url=UNREACHABLE_URL):
    endpoint, _ = webhook_service.create_endpoint(
        db_session, tenant_id=tenant.id, url=url, event_types=["case.created"]
    )
    delivery = webhook_service.create_delivery(
        db_session,
        tenant_id=tenant.id,
        endpoint=endpoint,
        event_type="case.created",
        payload={"event": "case.created", "data": {}},
        idempotency_key="evt-1:ep-1",
    )
    db_session.commit()
    return delivery


def test_failed_delivery_retries_then_fails(db_session, make_tenant, monkeypatch):
    _tighten(monkeypatch)
    tenant = make_tenant(slug="wh-retry")
    delivery = _make_delivery(db_session, tenant)

    # Attempt 1 and 2 -> retrying.
    webhook_service.attempt_delivery(db_session, delivery)
    db_session.commit()
    assert delivery.status == WebhookDeliveryStatus.retrying

    webhook_service.attempt_delivery(db_session, delivery)
    db_session.commit()
    assert delivery.status == WebhookDeliveryStatus.retrying

    # Attempt 3 -> failed (max attempts reached).
    webhook_service.attempt_delivery(db_session, delivery)
    db_session.commit()
    assert delivery.status == WebhookDeliveryStatus.failed
    assert delivery.attempt_count == 3

    # Each attempt was persisted with an error and no success.
    attempts = db_session.execute(
        text("SELECT success, error FROM webhook_delivery_attempts WHERE delivery_id = :d"),
        {"d": str(delivery.id)},
    ).all()
    assert len(attempts) == 3
    assert all(a.success is False and a.error for a in attempts)


def test_replay_resets_failed_delivery(db_session, make_tenant, monkeypatch):
    _tighten(monkeypatch)
    tenant = make_tenant(slug="wh-replay")
    delivery = _make_delivery(db_session, tenant)
    for _ in range(3):
        webhook_service.attempt_delivery(db_session, delivery)
    db_session.commit()
    assert delivery.status == WebhookDeliveryStatus.failed

    failed = webhook_service.find_failed_deliveries(db_session, tenant.id)
    assert delivery.id in {d.id for d in failed}

    webhook_service.reset_for_replay(db_session, delivery)
    db_session.commit()
    assert delivery.status == WebhookDeliveryStatus.pending
    assert delivery.attempt_count == 0


def test_delivery_succeeds_against_local_receiver(db_session, make_tenant, monkeypatch):
    """A reachable 2xx endpoint marks the delivery delivered (real HTTP).

    Targets the local webhook-receiver container (echoes 200 for any POST).
    """
    import os

    _tighten(monkeypatch)
    tenant = make_tenant(slug="wh-ok")
    receiver = os.environ.get("WEBHOOK_RECEIVER_URL", "http://webhook-receiver:8080/")
    delivery = _make_delivery(db_session, tenant, url=receiver)
    webhook_service.attempt_delivery(db_session, delivery)
    db_session.commit()
    assert delivery.status == WebhookDeliveryStatus.delivered
    assert delivery.response_status == 200
