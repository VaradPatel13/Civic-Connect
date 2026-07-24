"""Base model definitions and shared utilities for CivicConnect.

This module provides:
- Declarative base for all SQLAlchemy models
- Common column mixins (timestamps, soft delete, UUID PK)
- Shared enums used across the user domain
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base declarative class for all models."""
    pass


class TimestampMixin:
    """Adds created_at and updated_at timestamps to a model."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class SoftDeleteMixin:
    """Adds soft-delete support via deleted_at timestamp."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )


class UUIDMixin:
    """Adds UUID primary key."""

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )


class Platform(str, Enum):
    """Device platform types for session tracking."""

    IOS = "ios"
    ANDROID = "android"
    WEB = "web"


class UserRole(str, Enum):
    """Role-based access control levels."""

    CITIZEN = "citizen"
    WORKER = "worker"
    OFFICER = "officer"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class PreferredLanguage(str, Enum):
    """Supported notification and UI languages."""

    EN = "en"
    HI = "hi"
    MR = "mr"
