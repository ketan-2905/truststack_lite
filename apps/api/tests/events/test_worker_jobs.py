"""Domain events create deliveries, and worker jobs update real DB state."""

from __future__ import annotations

import os

from sqlalchemy import text

from app.enums import ConsentType, WebhookDeliveryStatus
from app.services import consent as consent_service
from app.services import events as event_service
from app.services import webhooks as webhook_service

RECEIVER = os.environ.get("WEBHOOK_RECEIVER_URL", "http://webhook-receiver:8080/")


def _count(db, table, tenant):
    return db.execute(
        text(f"SELECT count(*) FROM {table} WHERE tenant_id = :t"), {"t": str(tenant.id)}
    ).scalar()


def test_emit_event_records_event_and_creates_delivery(db_session, make_tenant):
    tenant = make_tenant(slug="evt-1")
    webhook_service.create_endpoint(
        db_session, tenant_id=tenant.id, url=RECEIVER, event_types=["case.created"]
    )
    db_session.commit()

    event_service.emit_event(
        db_session,
        tenant_id=tenant.id,
        event_type=event_service.EVENT_CASE_CREATED,
        payload={"case_id": "x"},
    )
    db_session.commit()

    assert _count(db_session, "domain_events", tenant) == 1
    assert _count(db_session, "webhook_deliveries", tenant) == 1


def test_emit_event_without_subscriber_creates_no_delivery(db_session, make_tenant):
    tenant = make_tenant(slug="evt-2")
    event_service.emit_event(
        db_session,
        tenant_id=tenant.id,
        event_type=event_service.EVENT_CASE_CREATED,
        payload={"case_id": "x"},
    )
    db_session.commit()
    assert _count(db_session, "domain_events", tenant) == 1
    assert _count(db_session, "webhook_deliveries", tenant) == 0


def test_event_subscription_filters_by_type(db_session, make_tenant):
    tenant = make_tenant(slug="evt-3")
    webhook_service.create_endpoint(
        db_session, tenant_id=tenant.id, url=RECEIVER, event_types=["risk.decided"]
    )
    db_session.commit()
    # case.created not subscribed -> no delivery.
    event_service.emit_event(
        db_session, tenant_id=tenant.id, event_type="case.created", payload={}
    )
    db_session.commit()
    assert _count(db_session, "webhook_deliveries", tenant) == 0


def test_deliver_webhook_job_updates_state(db_session, make_tenant):
    """The async job performs a real signed delivery and updates DB state."""
    from app.tasks.webhooks import deliver_webhook

    tenant = make_tenant(slug="evt-4")
    endpoint, _ = webhook_service.create_endpoint(
        db_session, tenant_id=tenant.id, url=RECEIVER, event_types=["case.created"]
    )
    delivery = webhook_service.create_delivery(
        db_session,
        tenant_id=tenant.id,
        endpoint=endpoint,
        event_type="case.created",
        payload={"event": "case.created", "data": {}},
        idempotency_key="evt4:1",
    )
    db_session.commit()
    delivery_id = str(delivery.id)

    result = deliver_webhook(delivery_id)
    assert result == "delivered"

    status = db_session.execute(
        text("SELECT status FROM webhook_deliveries WHERE id = :i"), {"i": delivery_id}
    ).scalar()
    assert status == WebhookDeliveryStatus.delivered.value


def test_risk_recompute_job_writes_decision(
    db_session, make_tenant, make_applicant, make_case, make_consent_notice
):
    from app.tasks.risk import recompute_case_risk_task

    tenant = make_tenant(slug="evt-5")
    applicant = make_applicant(tenant)
    case = make_case(tenant, applicant)
    notice = make_consent_notice(tenant)
    consent_service.record_consent(
        db_session, tenant_id=tenant.id, case=case, applicant=applicant,
        notice=notice, granted=True, consent_type=ConsentType.applicant,
    )
    db_session.commit()

    decision = recompute_case_risk_task(str(tenant.id), str(case.id))
    assert decision == "approved"

    count = db_session.execute(
        text("SELECT count(*) FROM risk_decisions WHERE case_id = :c"), {"c": str(case.id)}
    ).scalar()
    assert count == 1
