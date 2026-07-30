"""Citizen and session models for CivicConnect.

These models implement the user system described in:
- docs/specs/users.md
- docs/specs/auth.md
- docs/specs/database.md

They are intentionally focused only on the citizen domain. Administrative
users, departments, and report entities are modeled separately.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.models.notifications import Notification
    from backend.models.reports import Report
    from backend.models.rewards import RewardTransaction

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, PreferredLanguage, TimestampMixin, UserRole, UUIDMixin


class Citizen(Base, UUIDMixin, TimestampMixin):
    """Primary citizen account table.

    Maps to the `citizens` table defined in docs/specs/database.md.
    """

    __tablename__ = "citizens"
    __table_args__ = (
        CheckConstraint("points >= 0", name="chk_citizen_points_non_negative"),
    )


    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    preferred_language: Mapped[PreferredLanguage] = mapped_column(
        Enum(PreferredLanguage, name="preferred_language", native_enum=False),
        nullable=False,
        default=PreferredLanguage.EN,
    )
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    push_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notification_preferences: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False),
        nullable=False,
        default=UserRole.CITIZEN,
    )

    sessions: Mapped[list[Session]] = relationship(
        "Session",
        back_populates="citizen",
        cascade="all, delete-orphan",
    )

    reports: Mapped[list[Report]] = relationship(
        "Report",
        back_populates="citizen",
        cascade="all, delete-orphan",
    )
    notifications: Mapped[list[Notification]] = relationship(
        "Notification",
        back_populates="citizen",
        cascade="all, delete-orphan",
    )
    reward_transactions: Mapped[list[RewardTransaction]] = relationship(
        "RewardTransaction",
        back_populates="citizen",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Citizen {self.id} phone={self.phone} active={self.is_active}>"


class Session(Base, UUIDMixin, TimestampMixin):
    """Refresh token session for multi-device login support.

    Only hashed refresh tokens are persisted. Plaintext tokens are never stored.
    """

    __tablename__ = "sessions"

    citizen_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("citizens.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    refresh_token_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    device_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    platform: Mapped[str | None] = mapped_column(String(20), nullable=True)
    app_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    citizen: Mapped[Citizen] = relationship("Citizen", back_populates="sessions")

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None

    def __repr__(self) -> str:
        return f"<Session {self.id} citizen={self.citizen_id} revoked={self.is_revoked}>"


class OTPCode(Base, UUIDMixin, TimestampMixin):
    """One-time password records for phone verification and password reset.

    These records are short-lived and should be purged after expiry.
    """

    __tablename__ = "otp_codes"

    citizen_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("citizens.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    purpose: Mapped[str] = mapped_column(String(50), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    @property
    def is_expired(self) -> bool:
        return datetime.now(UTC) >= self.expires_at

    @property
    def is_consumed(self) -> bool:
        return self.consumed_at is not None

    def __repr__(self) -> str:
        return f"<OTPCode {self.id} phone={self.phone} purpose={self.purpose} expired={self.is_expired}>"
