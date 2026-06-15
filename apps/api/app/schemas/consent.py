"""Consent notice and consent record (receipt) schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.enums import ConsentType
from app.schemas.common import ORMModel


class ConsentNoticeCreate(BaseModel):
    key: str = Field(min_length=1, max_length=100)
    version: int = Field(ge=1)
    jurisdiction: str = Field(min_length=1, max_length=32)
    language: str = Field(min_length=1, max_length=16)
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1)
    purposes: list[str] = Field(min_length=1)


class ConsentNoticeOut(ORMModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    key: str
    version: int
    jurisdiction: str
    language: str
    title: str
    body: str
    purposes: list[str]
    content_hash: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ConsentNoticePublicOut(ORMModel):
    """Public notice view (no internal ids beyond the notice id)."""

    id: uuid.UUID
    key: str
    version: int
    jurisdiction: str
    language: str
    title: str
    body: str
    purposes: list[str]
    content_hash: str


class ConsentGrant(BaseModel):
    notice_id: uuid.UUID
    granted: bool = True
    consent_type: ConsentType = ConsentType.applicant
    # Required when the applicant is a minor and consent_type is guardian.
    guardian_name: str | None = Field(default=None, max_length=255)
    guardian_relationship: str | None = Field(default=None, max_length=64)


class ConsentWithdraw(BaseModel):
    notice_id: uuid.UUID
    reason: str | None = None


class ConsentRecordOut(ORMModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    case_id: uuid.UUID
    applicant_id: uuid.UUID
    notice_id: uuid.UUID
    consent_type: ConsentType
    granted: bool
    notice_version: int
    language: str
    jurisdiction: str
    purposes: list[str]
    source_ip: str | None
    user_agent: str | None
    guardian_name: str | None
    guardian_relationship: str | None
    receipt_hash: str
    created_at: datetime
