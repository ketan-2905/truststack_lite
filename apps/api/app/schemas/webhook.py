"""Webhook endpoint and delivery schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.enums import WebhookDeliveryStatus
from app.schemas.common import ORMModel


class WebhookEndpointCreate(BaseModel):
    url: str = Field(min_length=1, max_length=2048)
    event_types: list[str] = Field(min_length=1)
    description: str | None = Field(default=None, max_length=255)


class WebhookEndpointOut(ORMModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    url: str
    event_types: list[str]
    description: str | None
    is_active: bool
    created_at: datetime


class WebhookEndpointCreatedOut(WebhookEndpointOut):
    # The signing secret is returned exactly once (creation/rotation).
    signing_secret: str


class WebhookSecretOut(BaseModel):
    id: uuid.UUID
    signing_secret: str


class WebhookDeliveryOut(ORMModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    endpoint_id: uuid.UUID
    case_id: uuid.UUID | None
    event_type: str
    status: WebhookDeliveryStatus
    attempt_count: int
    response_status: int | None
    last_attempt_at: datetime | None
    next_attempt_at: datetime | None
    created_at: datetime
