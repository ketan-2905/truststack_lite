"""Webhook endpoint management and signed delivery with retries.

Outbound deliveries are real HTTP calls (httpx). Each attempt is persisted with
status code, response-body hash, duration, and error. Failures retry with
exponential backoff up to ``WEBHOOK_MAX_ATTEMPTS``, then terminate as ``failed``.
"""

from __future__ import annotations

import json
import secrets
import time
import uuid
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.enums import WebhookDeliveryStatus
from app.errors import NotFoundError
from app.hashing import sha256_hex
from app.models.webhook import WebhookDelivery, WebhookDeliveryAttempt, WebhookEndpoint
from app.services import audit
from app.webhooks.signing import (
    DELIVERY_HEADER,
    EVENT_HEADER,
    SIGNATURE_HEADER,
    sign_payload,
)


def _now() -> datetime:
    return datetime.now(UTC)


def generate_secret() -> str:
    return "whsec_" + secrets.token_urlsafe(32)


# ── Endpoints ────────────────────────────────────────────────────────────────
def create_endpoint(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    url: str,
    event_types: list[str],
    description: str | None = None,
) -> tuple[WebhookEndpoint, str]:
    secret = generate_secret()
    endpoint = WebhookEndpoint(
        tenant_id=tenant_id,
        url=url,
        signing_secret=secret,
        description=description,
        event_types=event_types,
        is_active=True,
    )
    db.add(endpoint)
    db.flush()
    return endpoint, secret


def list_endpoints(db: Session, tenant_id: uuid.UUID) -> list[WebhookEndpoint]:
    stmt = (
        select(WebhookEndpoint)
        .where(WebhookEndpoint.tenant_id == tenant_id, WebhookEndpoint.deleted_at.is_(None))
        .order_by(WebhookEndpoint.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def get_endpoint(db: Session, tenant_id: uuid.UUID, endpoint_id: uuid.UUID) -> WebhookEndpoint:
    endpoint = db.scalar(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == endpoint_id,
            WebhookEndpoint.tenant_id == tenant_id,
            WebhookEndpoint.deleted_at.is_(None),
        )
    )
    if endpoint is None:
        raise NotFoundError("Webhook endpoint")
    return endpoint


def rotate_secret(db: Session, tenant_id: uuid.UUID, endpoint_id: uuid.UUID) -> tuple[WebhookEndpoint, str]:
    endpoint = get_endpoint(db, tenant_id, endpoint_id)
    secret = generate_secret()
    endpoint.signing_secret = secret
    db.flush()
    return endpoint, secret


def deactivate_endpoint(db: Session, tenant_id: uuid.UUID, endpoint_id: uuid.UUID) -> WebhookEndpoint:
    endpoint = get_endpoint(db, tenant_id, endpoint_id)
    endpoint.is_active = False
    db.flush()
    return endpoint


def endpoints_for_event(db: Session, tenant_id: uuid.UUID, event_type: str) -> list[WebhookEndpoint]:
    candidates = db.scalars(
        select(WebhookEndpoint).where(
            WebhookEndpoint.tenant_id == tenant_id,
            WebhookEndpoint.is_active.is_(True),
            WebhookEndpoint.deleted_at.is_(None),
        )
    ).all()
    return [
        e for e in candidates if event_type in (e.event_types or []) or "*" in (e.event_types or [])
    ]


# ── Deliveries ───────────────────────────────────────────────────────────────
def create_delivery(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    endpoint: WebhookEndpoint,
    event_type: str,
    payload: dict,
    idempotency_key: str,
    case_id: uuid.UUID | None = None,
) -> WebhookDelivery:
    # Idempotent: one delivery per (event, endpoint).
    existing = db.scalar(
        select(WebhookDelivery).where(WebhookDelivery.idempotency_key == idempotency_key)
    )
    if existing is not None:
        return existing

    delivery = WebhookDelivery(
        tenant_id=tenant_id,
        endpoint_id=endpoint.id,
        case_id=case_id,
        event_type=event_type,
        status=WebhookDeliveryStatus.pending,
        payload=payload,
        idempotency_key=idempotency_key,
        attempt_count=0,
        next_attempt_at=_now(),
    )
    db.add(delivery)
    db.flush()
    return delivery


def _backoff_seconds(attempt_number: int) -> int:
    base = settings.webhook_backoff_base_seconds
    return min(base * (2 ** (attempt_number - 1)), 3600)


def attempt_delivery(db: Session, delivery: WebhookDelivery) -> bool:
    """Perform one real HTTP delivery attempt and persist the result."""
    endpoint = db.get(WebhookEndpoint, delivery.endpoint_id)
    if endpoint is None:
        delivery.status = WebhookDeliveryStatus.failed
        db.flush()
        return False

    body = json.dumps(delivery.payload, default=str).encode()
    signature = sign_payload(endpoint.signing_secret, body)
    delivery.signature = signature
    attempt_number = delivery.attempt_count + 1

    status_code: int | None = None
    success = False
    error: str | None = None
    response_text = ""
    started = time.monotonic()
    try:
        resp = httpx.post(
            endpoint.url,
            content=body,
            headers={
                "Content-Type": "application/json",
                SIGNATURE_HEADER: signature,
                EVENT_HEADER: delivery.event_type,
                DELIVERY_HEADER: str(delivery.id),
            },
            timeout=settings.webhook_timeout_seconds,
        )
        status_code = resp.status_code
        response_text = resp.text or ""
        success = 200 <= resp.status_code < 300
    except Exception as exc:  # noqa: BLE001 - record the real transport error
        error = f"{type(exc).__name__}: {exc}"
    duration_ms = int((time.monotonic() - started) * 1000)

    db.add(
        WebhookDeliveryAttempt(
            delivery_id=delivery.id,
            attempt_number=attempt_number,
            success=success,
            status_code=status_code,
            response_body_hash=sha256_hex(response_text) if response_text else None,
            duration_ms=duration_ms,
            error=error,
        )
    )

    delivery.attempt_count = attempt_number
    delivery.last_attempt_at = _now()
    delivery.response_status = status_code
    delivery.response_body = response_text[:2000] if response_text else None

    if success:
        delivery.status = WebhookDeliveryStatus.delivered
        delivery.next_attempt_at = None
    elif attempt_number >= settings.webhook_max_attempts:
        delivery.status = WebhookDeliveryStatus.failed
        delivery.next_attempt_at = None
        audit.record_event(
            db,
            tenant_id=delivery.tenant_id,
            actor_type="system",
            actor_id="webhook",
            action="webhook.delivery_failed",
            resource_type="webhook_delivery",
            resource_id=delivery.id,
            case_id=delivery.case_id,
            data={"attempts": attempt_number, "last_error": error, "status_code": status_code},
        )
    else:
        delivery.status = WebhookDeliveryStatus.retrying
        delivery.next_attempt_at = _now() + timedelta(seconds=_backoff_seconds(attempt_number))

    db.flush()
    return success


def list_deliveries(
    db: Session,
    tenant_id: uuid.UUID,
    *,
    status: WebhookDeliveryStatus | None = None,
) -> list[WebhookDelivery]:
    stmt = select(WebhookDelivery).where(WebhookDelivery.tenant_id == tenant_id)
    if status:
        stmt = stmt.where(WebhookDelivery.status == status)
    stmt = stmt.order_by(WebhookDelivery.created_at.desc())
    return list(db.scalars(stmt).all())


def find_failed_deliveries(db: Session, tenant_id: uuid.UUID | None = None) -> list[WebhookDelivery]:
    stmt = select(WebhookDelivery).where(
        WebhookDelivery.status == WebhookDeliveryStatus.failed
    )
    if tenant_id:
        stmt = stmt.where(WebhookDelivery.tenant_id == tenant_id)
    return list(db.scalars(stmt).all())


def reset_for_replay(db: Session, delivery: WebhookDelivery) -> None:
    delivery.status = WebhookDeliveryStatus.pending
    delivery.attempt_count = 0
    delivery.next_attempt_at = _now()
    db.flush()
