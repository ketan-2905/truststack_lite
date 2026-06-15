"""Audit event schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from app.schemas.common import ORMModel


class AuditEventOut(ORMModel):
    id: uuid.UUID
    tenant_id: uuid.UUID | None
    actor_type: str
    actor_id: str | None
    action: str
    resource_type: str
    resource_id: str | None
    case_id: uuid.UUID | None
    request_id: str | None
    data: dict | None
    created_at: datetime
