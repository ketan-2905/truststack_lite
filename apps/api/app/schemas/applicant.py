"""Applicant schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ORMModel


class ApplicantCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=32)
    external_ref: str | None = Field(default=None, max_length=255)
    date_of_birth: date | None = None
    attributes: dict | None = None


class ApplicantOut(ORMModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    full_name: str
    email: str | None
    phone: str | None
    external_ref: str | None
    date_of_birth: date | None
    attributes: dict | None
    created_at: datetime
    updated_at: datetime
