"""Immutable Event Store model for CivicConnect domain event sourcing.

Table:
- report_events: Append-only ledger of domain state transition events

Specs: docs/specs/database.md
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.models.reports import Report

from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin, UUIDMixin


class ReportEvent(Base, UUIDMixin, TimestampMixin):
    """Immutable event sourcing record capturing state mutations on civic reports."""

    __tablename__ = "report_events"

    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    aggregate_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    event_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    triggered_by: Mapped[str] = mapped_column(String(100), nullable=False, default="system")
    trace_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    # ── Relationships ──────────────────────────────────────────────────
    report: Mapped[Report] = relationship("Report", backref="domain_events")

    def __repr__(self) -> str:
        return f"<ReportEvent {self.event_type} v{self.aggregate_version} report={self.report_id}>"
