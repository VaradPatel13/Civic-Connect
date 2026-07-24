"""Report domain models for CivicConnect.

Tables:
- wards:        PMC administrative boundaries (PostGIS MULTIPOLYGON)
- reports:      Citizen-submitted civic issue reports
- photos:       Uploaded photos linked to reports
- assignments:  Department assignment tracking (immutable history)
- status_logs:  Immutable status-transition log

Specs: docs/specs/database.md, docs/specs/reports.md
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.models.agent_executions import AgentExecution
    from backend.models.citizens import Citizen
    from backend.models.departments import Department
    from backend.models.rewards import RewardTransaction

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
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

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ReportStatus(str, Enum):
    """Lifecycle states for a civic report."""

    PENDING = "pending"
    PROCESSING = "processing"
    VERIFIED = "verified"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"
    CANCELLED = "cancelled"


class IssueCategory(str, Enum):
    """Supported civic issue categories."""

    ROADS = "roads"
    WATER_SUPPLY = "water_supply"
    DRAINAGE = "drainage"
    WASTE_MANAGEMENT = "waste_management"
    STREET_LIGHTING = "street_lighting"
    PUBLIC_HEALTH = "public_health"
    PARKS = "parks"
    ENCROACHMENT = "encroachment"
    TRAFFIC_INFRASTRUCTURE = "traffic_infrastructure"
    OTHER = "other"


class UrgencyLevel(str, Enum):
    """Priority levels for report urgency."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AssignmentStatus(str, Enum):
    """Current state of a department assignment."""

    PENDING = "pending"
    ACTIVE = "active"
    RESOLVED = "resolved"
    REASSIGNED = "reassigned"
    CANCELLED = "cancelled"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class Ward(Base, UUIDMixin, TimestampMixin):
    """PMC administrative ward boundary.

    Geometry is stored as a PostGIS MULTIPOLYGON (EPSG:4326).
    Derives ``ward`` and ``zone`` for linked reports.
    """

    __tablename__ = "wards"

    ward_name: Mapped[str] = mapped_column(String(255), nullable=False)
    ward_number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    zone: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    jurisdiction_geometry: Mapped[Geometry] = mapped_column(
        Geometry(
            geometry_type="MULTIPOLYGON",
            srid=4326,
            spatial_index=True,
        ),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    reports: Mapped[list[Report]] = relationship("Report", back_populates="ward_rel")

    def __repr__(self) -> str:
        return f"<Ward {self.ward_number} {self.ward_name} zone={self.zone}>"


class Report(Base, UUIDMixin, TimestampMixin):
    """Primary civic issue report submitted by a citizen.

    Immutable citizen content (``title``, ``description``) is never
    overwritten.  AI-generated fields (translation, summary, etc.)
    are written once after processing and remain fixed.
    """

    __tablename__ = "reports"

    # ── Foreign keys ───────────────────────────────────────────────────
    citizen_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("citizens.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    ward_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("wards.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Issue details ──────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(
        String(10), nullable=False, default="en", server_default="en"
    )

    # AI-generated (written once, never updated)
    translated_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    issue_category: Mapped[IssueCategory] = mapped_column(
        SQLEnum(IssueCategory, name="issue_category", native_enum=False),
        nullable=False,
        index=True,
    )
    urgency: Mapped[UrgencyLevel] = mapped_column(
        SQLEnum(UrgencyLevel, name="urgency_level", native_enum=False),
        nullable=False,
        default=UrgencyLevel.MEDIUM,
        server_default="medium",
        index=True,
    )
    status: Mapped[ReportStatus] = mapped_column(
        SQLEnum(ReportStatus, name="report_status", native_enum=False),
        nullable=False,
        default=ReportStatus.PENDING,
        server_default="pending",
        index=True,
    )

    # ── Location ───────────────────────────────────────────────────────
    latitude: Mapped[float | None] = mapped_column(nullable=True)
    longitude: Mapped[float | None] = mapped_column(nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ward: Mapped[str | None] = mapped_column(String(100), nullable=True)
    zone: Mapped[str | None] = mapped_column(String(100), nullable=True)

    location: Mapped[Geometry | None] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=True,
    )

    # ── AI metadata ────────────────────────────────────────────────────
    classification_confidence: Mapped[float | None] = mapped_column(nullable=True)
    moderation_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    forensics_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ai_tags: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    # ── Duplicate tracking ─────────────────────────────────────────────
    is_duplicate: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    duplicate_of_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reports.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Resolution ──────────────────────────────────────────────────────
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution_images: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Relationships ──────────────────────────────────────────────────
    citizen: Mapped[Citizen] = relationship("Citizen", back_populates="reports")
    ward_rel: Mapped[Ward | None] = relationship("Ward", back_populates="reports")
    photos: Mapped[list[Photo]] = relationship(
        "Photo",
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="Photo.created_at",
    )
    assignments: Mapped[list[Assignment]] = relationship(
        "Assignment",
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="desc(Assignment.assigned_at)",
    )
    status_logs: Mapped[list[StatusLog]] = relationship(
        "StatusLog",
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="StatusLog.created_at",
    )
    agent_executions: Mapped[list[AgentExecution]] = relationship(
        "AgentExecution",
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="AgentExecution.started_at",
    )
    rewards: Mapped[list[RewardTransaction]] = relationship(
        "RewardTransaction", back_populates="report"
    )

    def __repr__(self) -> str:
        return (
            f"<Report {self.id} category={self.issue_category} "
            f"status={self.status} citizen={self.citizen_id}>"
        )


class Photo(Base, UUIDMixin, TimestampMixin):
    """Single uploaded photo for a report.

    Stores Cloudinary metadata plus forensic analysis results.
    One report may contain multiple photos.
    """

    __tablename__ = "photos"

    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Cloudinary
    cloudinary_url: Mapped[str] = mapped_column(String(500), nullable=False)
    public_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    secure_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    format: Mapped[str | None] = mapped_column(String(20), nullable=True)
    bytes_size: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Forensic
    forensic_score: Mapped[float | None] = mapped_column(nullable=True)
    forensic_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    original_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_authentic: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Display ordering
    display_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    # ── Relationships ──────────────────────────────────────────────────
    report: Mapped[Report] = relationship("Report", back_populates="photos")

    def __repr__(self) -> str:
        return f"<Photo {self.id} report={self.report_id}>"


class Assignment(Base, UUIDMixin, TimestampMixin):
    """Immutable department assignment record for a report.

    Re-routing always creates a *new* record rather than
    updating an existing one.
    """

    __tablename__ = "assignments"

    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    status: Mapped[AssignmentStatus] = mapped_column(
        SQLEnum(AssignmentStatus, name="assignment_status", native_enum=False),
        nullable=False,
        default=AssignmentStatus.ACTIVE,
        server_default="active",
    )

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Routing metadata (from Department Router agent)
    routing_confidence: Mapped[float | None] = mapped_column(nullable=True)
    routing_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_by: Mapped[str] = mapped_column(
        String(50), nullable=False, default="system", server_default="system"
    )

    # Escalation
    escalated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    escalation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationships ──────────────────────────────────────────────────
    report: Mapped[Report] = relationship("Report", back_populates="assignments")
    department: Mapped[Department] = relationship("Department", back_populates="assignments")

    def __repr__(self) -> str:
        return f"<Assignment {self.report_id} -> {self.department_id} " f"status={self.status}>"


class StatusLog(Base, UUIDMixin, TimestampMixin):
    """Immutable status-transition record.

    Every state change on a report appends exactly one row.
    Records must never be modified or deleted.
    """

    __tablename__ = "status_logs"

    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    from_status: Mapped[ReportStatus | None] = mapped_column(
        SQLEnum(ReportStatus, name="report_status", native_enum=False),
        nullable=True,
    )
    to_status: Mapped[ReportStatus] = mapped_column(
        SQLEnum(ReportStatus, name="report_status", native_enum=False),
        nullable=False,
    )

    changed_by: Mapped[str] = mapped_column(
        String(50), nullable=False, default="system", server_default="system"
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # ── Relationships ──────────────────────────────────────────────────
    report: Mapped[Report] = relationship("Report", back_populates="status_logs")

    def __repr__(self) -> str:
        if self.from_status:
            return f"<StatusLog {self.report_id} " f"{self.from_status} -> {self.to_status}>"
        return f"<StatusLog {self.report_id} initial={self.to_status}>"
