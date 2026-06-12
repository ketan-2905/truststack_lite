"""Shared SQLAlchemy column helpers."""

from __future__ import annotations

import enum

from sqlalchemy import Enum as SAEnum


def pg_enum(py_enum: type[enum.Enum], name: str) -> SAEnum:
    """Native PostgreSQL enum that persists the member *values*."""
    return SAEnum(
        py_enum,
        name=name,
        values_callable=lambda e: [member.value for member in e],
        native_enum=True,
        validate_strings=True,
    )
