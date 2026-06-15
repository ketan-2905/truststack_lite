"""Authentication schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    # Plain string (not EmailStr): internal accounts use reserved TLDs such as
    # `.local` (e.g. admin@truststack.local) which strict email validation rejects.
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1)
    tenant_slug: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str
