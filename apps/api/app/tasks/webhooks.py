"""Webhook delivery worker task with self-rescheduling retries."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from app.db import SessionLocal
from app.enums import WebhookDeliveryStatus
from app.logging_config import get_logger
from app.models.webhook import WebhookDelivery
from app.queue import QUEUE_WEBHOOKS, get_queue
from app.services import webhooks as webhook_service

logger = get_logger("truststack.tasks.webhooks")

DELIVER_TASK = "app.tasks.webhooks.deliver_webhook"


def deliver_webhook(delivery_id: str) -> str:
    """RQ entrypoint: attempt one delivery; reschedule on retryable failure."""
    with SessionLocal() as db:
        delivery = db.get(WebhookDelivery, uuid.UUID(str(delivery_id)))
        if delivery is None:
            logger.warning("webhook_delivery_missing", extra={"fields": {"id": delivery_id}})
            return "missing"
        if delivery.status == WebhookDeliveryStatus.delivered:
            return "already_delivered"

        webhook_service.attempt_delivery(db, delivery)
        status = delivery.status
        next_at = delivery.next_attempt_at
        db.commit()

    if status == WebhookDeliveryStatus.retrying and next_at is not None:
        delay = max(1, int((next_at - datetime.now(UTC)).total_seconds()))
        get_queue(QUEUE_WEBHOOKS).enqueue_in(
            timedelta(seconds=delay), DELIVER_TASK, str(delivery_id)
        )
    logger.info(
        "webhook_delivery_attempted",
        extra={"fields": {"delivery_id": delivery_id, "status": status.value}},
    )
    return status.value
