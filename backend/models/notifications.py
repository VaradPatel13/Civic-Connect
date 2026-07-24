"""Notification domain models for CivicConnect.

Tables:
- notifications: In-app / push / SMS notification records for citizens

Specs: docs/specs/notifications.md, docs/specs/database.md
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.models.citizens import Citizen

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin, UUIDMixin


class NotificationType(str, Enum):
    """Event type that triggered the notification."""

    AUTH = "auth"
    REPORT_UPDATE = "report_update"
    ASSIGNMENT = "assignment"
    RESOLUTION = "resolution"
    REWARD = "reward"
    SYSTEM = "system"


class NotificationPriority(str, Enum):
    """Delivery urgency."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationChannel(str, Enum):
    """Transport mechanism."""

    PUSH = "push"
    SMS = "sms"
    EMAIL = "email"
    IN_APP = "in_app"


class DeliveryStatus(str, Enum):
    """Lifecycle of delivery to a channel provider."""

    QUEUED = "queued"
    SENDING = "sending"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class Notification(Base, UUIDMixin, TimestampMixin):
    """Immutable notification record.

    Delivery failures must never affect report processing.
    Retry logic is tracked via ``retry_count`` / ``error_message``.
    """

    __tablename__ = "notifications"

    # ── Foreign keys ───────────────────────────────────────────────────
    citizen_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("citizens.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    report_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # ── Content ────────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    notification_type: Mapped[NotificationType] = mapped_column(
        SQLEnum(NotificationType, name="notification_type", native_enum=False),
        nullable=False,
        index=True,
    )
    priority: Mapped[NotificationPriority] = mapped_column(
        SQLEnum(
            NotificationPriority,
            name="notification_priority",
            native_enum=False,
        ),
        nullable=False,
        default=NotificationPriority.NORMAL,
        server_default="normal",
    )

    # ── Channel ────────────────────────────────────────────────────────
    channel: Mapped[NotificationChannel] = mapped_column(
        SQLEnum(
            NotificationChannel,
            name="notification_channel",
            native_enum=False,
        ),
        nullable=False,
        default=NotificationChannel.IN_APP,
        server_default="in_app",
    )

    # ── Delivery lifecycle ──────────────────────────────────────────────
    delivery_status: Mapped[DeliveryStatus] = mapped_column(
        SQLEnum(DeliveryStatus, name="delivery_status", native_enum=False),
        nullable=False,
        default=DeliveryStatus.QUEUED,
        server_default="queued",
        index=True,
    )

    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Deep linking ────────────────────────────────────────────────────
    deep_link: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # ── Channel-specific payload ────────────────────────────────────────
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # ── Relationships ──────────────────────────────────────────────────
    citizen: Mapped[Citizen] = relationship("Citizen", back_populates="notifications")

    def __repr__(self) -> str:
        return (
            f"<Notification {self.id} type={self.notification_type} "
            f"status={self.delivery_status} citizen={self.citizen_id}>"
        )
