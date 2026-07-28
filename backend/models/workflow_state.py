"""Workflow State model for CivicConnect AI Pipeline crash recovery.

Table:
- workflow_states: Persists step-by-step state for reports during pipeline processing

Specs: docs/specs/ai-pipeline.md
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.models.reports import Report

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin, UUIDMixin


class WorkflowStatus(str, Enum):
    """Execution status of an orchestrated pipeline workflow."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PAUSED_HUMAN_REVIEW = "paused_human_review"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowState(Base, UUIDMixin, TimestampMixin):
    """Persisted state for an execution workflow run.

    Allows resuming pipeline execution from the exact last completed node
    if a worker node or container crashes mid-processing.
    """

    __tablename__ = "workflow_states"

    # ── Foreign keys ───────────────────────────────────────────────────
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    trace_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    current_step: Mapped[str] = mapped_column(String(100), nullable=False, default="supervisor")
    failed_step: Mapped[str | None] = mapped_column(String(100), nullable=True)

    status: Mapped[WorkflowStatus] = mapped_column(
        SQLEnum(WorkflowStatus, name="workflow_status", native_enum=False),
        nullable=False,
        default=WorkflowStatus.RUNNING,
        server_default="running",
        index=True,
    )

    # Serialized JSONB snapshot of all completed agent outputs
    state_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Timing ─────────────────────────────────────────────────────────
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Relationships ──────────────────────────────────────────────────
    report: Mapped[Report] = relationship("Report", backref="workflow_states")

    def __repr__(self) -> str:
        return f"<WorkflowState {self.trace_id} step={self.current_step} status={self.status}>"
