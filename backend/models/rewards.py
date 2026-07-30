"""Rewards domain models for CivicConnect.

Tables:
- reward_transactions: Immutable point-transaction audit trail

The denormalized ``citizens.points`` column provides fast balance reads;
this table provides the full audit history required by the spec.

Specs: docs/specs/rewards.md, docs/specs/database.md
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.models.citizens import Citizen
    from backend.models.reports import Report

from sqlalchemy import (
    Boolean,
    CheckConstraint,
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

# ---------------------------------------------------------------------------
# Enum
# ---------------------------------------------------------------------------


class RewardReason(str, Enum):
    """Enumerated reward event codes for point allocation / deduction."""

    # Awards
    REPORT_SUBMISSION = "report_submission"
    REPORT_VERIFIED = "report_verified"
    REPORT_RESOLVED = "report_resolved"
    COMMENT_ADDED = "comment_added"
    PHOTO_ADDED = "photo_added"
    MONTHLY_ACTIVE = "monthly_active"
    EARLY_RESOLUTION_BONUS = "early_resolution_bonus"
    REFERRAL_BONUS = "referral_bonus"

    # Deductions (negative points)
    REPORT_REJECTED = "report_rejected"
    SPAM_DETECTED = "spam_detected"
    FALSE_REPORT = "false_report"
    MALICIOUS_CONTENT = "malicious_content"


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------


class RewardTransaction(Base, UUIDMixin, TimestampMixin):
    """Single immutable point transaction.

    Every point change (award or deduction) creates one row.
    Balance snapshots guard against recalculating from scratch.
    """

    __tablename__ = "reward_transactions"
    __table_args__ = (
        CheckConstraint("new_balance = previous_balance + points", name="chk_reward_tx_balance_calc"),
        CheckConstraint("new_balance >= 0", name="chk_reward_tx_new_balance_non_negative"),
        CheckConstraint("previous_balance >= 0", name="chk_reward_tx_prev_balance_non_negative"),
    )


    # ── Foreign keys ───────────────────────────────────────────────────
    citizen_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("citizens.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    report_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reports.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Transaction ────────────────────────────────────────────────────
    points: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Positive = award, negative = deduction",
    )
    reason: Mapped[RewardReason] = mapped_column(
        SQLEnum(RewardReason, name="reward_reason", native_enum=False),
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Balance snapshot ───────────────────────────────────────────────
    previous_balance: Mapped[int] = mapped_column(Integer, nullable=False)
    new_balance: Mapped[int] = mapped_column(Integer, nullable=False)

    # ── Source tracking ────────────────────────────────────────────────
    awarded_by: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="system",
        server_default="system",
    )
    is_automated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    # ── Reversibility ──────────────────────────────────────────────────
    reversed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reverse_of_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )

    # ── Extra context ──────────────────────────────────────────────────
    extra_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # ── Relationships ──────────────────────────────────────────────────
    citizen: Mapped[Citizen] = relationship("Citizen", back_populates="reward_transactions")
    # String form avoids import-time circular reference with reports.py
    report: Mapped[Report | None] = relationship("Report", back_populates="rewards")

    def __repr__(self) -> str:
        sign = "+" if self.points > 0 else ""
        return (
            f"<RewardTransaction {self.id} {sign}{self.points}pts "
            f"citizen={self.citizen_id} reason={self.reason.value}>"
        )
