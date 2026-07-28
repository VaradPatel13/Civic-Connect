"""Idempotency engine model for CivicConnect API & AI Pipeline.

Table:
- idempotency_keys: Guarantees exactly-once report processing under network retries

Specs: docs/specs/database.md
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.models.reports import Report

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin, UUIDMixin


class IdempotencyKey(Base, UUIDMixin, TimestampMixin):
    """Stores request hashes and response snapshots to prevent duplicate operations."""

    __tablename__ = "idempotency_keys"

    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    report_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reports.id", ondelete="SET NULL"),
        nullable=True,
    )

    status_code: Mapped[int] = mapped_column(nullable=False, default=201)
    response_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # ── Relationships ──────────────────────────────────────────────────
    report: Mapped[Report | None] = relationship("Report", backref="idempotency_keys")

    def __repr__(self) -> str:
        return f"<IdempotencyKey {self.idempotency_key} report={self.report_id}>"
