"""RBAC roles and the user/role association."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import RoleName
from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.types import pg_enum


class Role(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "roles"

    name: Mapped[RoleName] = mapped_column(
        pg_enum(RoleName, "role_name"), nullable=False, unique=True, index=True
    )
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)


class UserRole(TimestampMixin, Base):
    __tablename__ = "user_roles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    )

    user: Mapped[User] = relationship(back_populates="roles")  # noqa: F821
    role: Mapped[Role] = relationship()
