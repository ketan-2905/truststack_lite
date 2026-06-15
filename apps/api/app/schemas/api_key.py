"""Tenant API key schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class ApiKeyCreate(BaseModel):
    name: str | None = Field(default=None, max_length=255)


class ApiKeyRotateRequest(BaseModel):
    expire_old: bool = True


class ApiKeyOut(ORMModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    prefix: str
    name: str | None
    is_active: bool
    last_used_at: datetime | None
    expires_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime


class ApiKeyCreatedOut(ApiKeyOut):
    # The raw key is returned exactly once, at creation/rotation.
    raw_key: str
