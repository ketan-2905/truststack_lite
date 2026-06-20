"""Webhook endpoint management, test sends, and delivery listing."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import ALL_TENANT_ROLES, Principal, require_roles
from app.enums import RoleName, WebhookDeliveryStatus
from app.schemas.webhook import (
    WebhookDeliveryOut,
    WebhookEndpointCreate,
    WebhookEndpointCreatedOut,
    WebhookEndpointOut,
    WebhookSecretOut,
)
from app.services import audit
from app.services import webhooks as webhook_service

ADMIN = require_roles(RoleName.tenant_admin)
READER = require_roles(*ALL_TENANT_ROLES)

router = APIRouter(tags=["webhooks"])


@router.post(
    "/v1/webhook-endpoints",
    response_model=WebhookEndpointCreatedOut,
    status_code=status.HTTP_201_CREATED,
)
def create_endpoint(
    payload: WebhookEndpointCreate,
    principal: Principal = Depends(ADMIN),
    db: Session = Depends(get_db),
) -> WebhookEndpointCreatedOut:
    endpoint, secret = webhook_service.create_endpoint(
        db,
        tenant_id=principal.tenant_id,
        url=payload.url,
        event_types=payload.event_types,
        description=payload.description,
    )
    audit.record_event(
        db,
        tenant_id=principal.tenant_id,
        actor_type=principal.actor_type,
        actor_id=principal.actor_id,
        action="webhook_endpoint.created",
        resource_type="webhook_endpoint",
        resource_id=endpoint.id,
        request=principal.request,
        data={"url": endpoint.url, "event_types": endpoint.event_types},
    )
    base = WebhookEndpointOut.model_validate(endpoint).model_dump()
    return WebhookEndpointCreatedOut(**base, signing_secret=secret)


@router.get("/v1/webhook-endpoints", response_model=list[WebhookEndpointOut])
def list_endpoints(
    principal: Principal = Depends(READER),
    db: Session = Depends(get_db),
) -> list[WebhookEndpointOut]:
    endpoints = webhook_service.list_endpoints(db, principal.tenant_id)
    return [WebhookEndpointOut.model_validate(e) for e in endpoints]


@router.post("/v1/webhook-endpoints/{endpoint_id}/rotate-secret", response_model=WebhookSecretOut)
def rotate_secret(
    endpoint_id: uuid.UUID,
    principal: Principal = Depends(ADMIN),
    db: Session = Depends(get_db),
) -> WebhookSecretOut:
    endpoint, secret = webhook_service.rotate_secret(db, principal.tenant_id, endpoint_id)
    audit.record_event(
        db,
        tenant_id=principal.tenant_id,
        actor_type=principal.actor_type,
        actor_id=principal.actor_id,
        action="webhook_endpoint.secret_rotated",
        resource_type="webhook_endpoint",
        resource_id=endpoint.id,
        request=principal.request,
    )
    return WebhookSecretOut(id=endpoint.id, signing_secret=secret)


@router.post("/v1/webhook-endpoints/{endpoint_id}/deactivate", response_model=WebhookEndpointOut)
def deactivate_endpoint(
    endpoint_id: uuid.UUID,
    principal: Principal = Depends(ADMIN),
    db: Session = Depends(get_db),
) -> WebhookEndpointOut:
    endpoint = webhook_service.deactivate_endpoint(db, principal.tenant_id, endpoint_id)
    return WebhookEndpointOut.model_validate(endpoint)


@router.post("/v1/webhook-endpoints/{endpoint_id}/test", response_model=WebhookDeliveryOut)
def send_test_event(
    endpoint_id: uuid.UUID,
    principal: Principal = Depends(ADMIN),
    db: Session = Depends(get_db),
) -> WebhookDeliveryOut:
    """Send a real signed test event to the endpoint synchronously."""
    endpoint = webhook_service.get_endpoint(db, principal.tenant_id, endpoint_id)
    delivery = webhook_service.create_delivery(
        db,
        tenant_id=principal.tenant_id,
        endpoint=endpoint,
        event_type="webhook.test",
        payload={"event": "webhook.test", "data": {"message": "TrustStack test event"}},
        idempotency_key=f"test:{endpoint.id}:{uuid.uuid4()}",
    )
    webhook_service.attempt_delivery(db, delivery)
    return WebhookDeliveryOut.model_validate(delivery)


@router.get("/v1/webhook-deliveries", response_model=list[WebhookDeliveryOut])
def list_deliveries(
    principal: Principal = Depends(READER),
    db: Session = Depends(get_db),
    delivery_status: WebhookDeliveryStatus | None = Query(default=None),
) -> list[WebhookDeliveryOut]:
    deliveries = webhook_service.list_deliveries(
        db, principal.tenant_id, status=delivery_status
    )
    return [WebhookDeliveryOut.model_validate(d) for d in deliveries]
