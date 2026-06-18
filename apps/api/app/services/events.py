"""Domain event emission and fan-out to webhook deliveries."""

from __future__ import annotations

import uuid
from datetime import timedelta

from sqlalchemy.orm import Session

from app.config import settings
from app.models.event import DomainEvent
from app.queue import QUEUE_WEBHOOKS, get_queue
from app.services import webhooks as webhook_service

# Canonical domain event types.
EVENT_CASE_CREATED = "case.created"
EVENT_CONSENT_GRANTED = "consent.granted"
EVENT_DOCUMENT_UPLOADED = "document.uploaded"
EVENT_OCR_COMPLETED = "ocr.completed"
EVENT_RISK_DECIDED = "risk.decided"
EVENT_REVIEW_RESOLVED = "review.resolved"
EVENT_CASE_COMPLETED = "case.completed"

DELIVER_TASK = "app.tasks.webhooks.deliver_webhook"


def emit_event(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    event_type: str,
    payload: dict,
    case_id: uuid.UUID | None = None,
) -> DomainEvent:
    """Record a domain event and create + schedule a webhook delivery for every
    active endpoint subscribed to the event type."""
    event = DomainEvent(
        tenant_id=tenant_id,
        case_id=case_id,
        event_type=event_type,
        payload=payload,
        dispatched=False,
    )
    db.add(event)
    db.flush()

    endpoints = webhook_service.endpoints_for_event(db, tenant_id, event_type)
    delivery_ids: list[str] = []
    for endpoint in endpoints:
        delivery = webhook_service.create_delivery(
            db,
            tenant_id=tenant_id,
            endpoint=endpoint,
            event_type=event_type,
            payload={"event": event_type, "event_id": str(event.id), "data": payload},
            idempotency_key=f"{event.id}:{endpoint.id}",
            case_id=case_id,
        )
        delivery_ids.append(str(delivery.id))

    event.dispatched = True
    db.flush()

    # Schedule delivery after a short delay so the producing transaction commits
    # first (the worker uses a separate session).
    queue = get_queue(QUEUE_WEBHOOKS)
    for delivery_id in delivery_ids:
        queue.enqueue_in(
            timedelta(seconds=settings.webhook_initial_dispatch_delay_seconds),
            DELIVER_TASK,
            delivery_id,
        )
    return event
