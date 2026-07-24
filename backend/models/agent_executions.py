"""AI Pipeline audit trail model for CivicConnect.

Tables:
- agent_executions: One row per AI agent run per report

Specs: docs/specs/ai-pipeline.md, docs/specs/database.md
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin, UUIDMixin


class AgentStatus(str, Enum):
    """Execution outcomes for a single agent invocation."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class AgentExecution(Base, UUIDMixin, TimestampMixin):
    """Audit record for exactly one AI agent invocation.

    Every AI decision in the pipeline (forensics, classification,
    moderation, geo-validation, enhancement, routing) creates one row.
    Records are never modified or deleted.
    """

    __tablename__ = "agent_executions"

    # ── Foreign keys ───────────────────────────────────────────────────
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Optional linkage to a common workflow run (all agents in one
    # pipeline execution share the same workflow_id).
    workflow_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True, index=True
    )

    # ── Agent identity ─────────────────────────────────────────────────
    agent_name: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    model_used: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    model_version: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )

    # ── Timing ─────────────────────────────────────────────────────────
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    execution_ms: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )

    # ── Outcome ────────────────────────────────────────────────────────
    status: Mapped[AgentStatus] = mapped_column(
        SQLEnum(AgentStatus, name="agent_status", native_enum=False),
        nullable=False,
        default=AgentStatus.RUNNING,
        server_default="running",
        index=True,
    )
    confidence: Mapped[Optional[float]] = mapped_column(nullable=True)

    # ── Snapshots (JSONB for flexibility) ──────────────────────────────
    input_snapshot: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )
    output_snapshot: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )
    error_snapshot: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )

    # ── Retry tracking ─────────────────────────────────────────────────
    retry_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    is_final_attempt: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    # ── Relationships ──────────────────────────────────────────────────
    report: Mapped[Report] = relationship(
        "Report", back_populates="agent_executions"
    )

    def __repr__(self) -> str:
        return (
            f"<AgentExecution {self.id} agent={self.agent_name} "
            f"status={self.status} report={self.report_id}>"
        )
