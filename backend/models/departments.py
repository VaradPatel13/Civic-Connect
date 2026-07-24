"""Department domain models for CivicConnect.

Tables:
- departments:          PMC municipal department records
- department_categories: Category-to-department routing rules (seeded)

Specs: docs/specs/departments.md, docs/specs/database.md
"""

from __future__ import annotations

import uuid
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.models.reports import Assignment

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin, UUIDMixin


class DepartmentCode(str, Enum):
    """Unique short identifier for each PMC department.

    The ``ADMIN`` code is the fallback routing target when the
    Department Router agent cannot determine a primary department.
    """

    ROADS = "ROADS"
    WATER = "WATER"
    DRAIN = "DRAIN"
    ELEC = "ELEC"
    HEALTH = "HEALTH"
    SANIT = "SANIT"
    FIRE = "FIRE"
    BUILD = "BUILD"
    TRAFF = "TRAFF"
    PARKS = "PARKS"
    ADMIN = "ADMIN"


class Department(Base, UUIDMixin, TimestampMixin):
    """Pune Municipal Corporation department.

    Pre-seeded reference data.  Routing decisions resolve codes
    to department IDs via ``department_categories``.
    """

    __tablename__ = "departments"

    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # ── Contact ─────────────────────────────────────────────────────────
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    operating_hours: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # ── SLA targets ─────────────────────────────────────────────────────
    sla_low_days: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    sla_medium_days: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    sla_high_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
    sla_critical_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=4)

    # ── Spatial ─────────────────────────────────────────────────────────
    jurisdiction_geometry: Mapped[Geometry | None] = mapped_column(
        Geometry(
            geometry_type="MULTIPOLYGON",
            srid=4326,
            spatial_index=True,
        ),
        nullable=True,
    )

    # ── Capacity (observability, not routing) ───────────────────────────
    active_report_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    weekly_capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    # ── Relationships ──────────────────────────────────────────────────
    assignments: Mapped[list[Assignment]] = relationship("Assignment", back_populates="department")
    category_links: Mapped[list[DepartmentCategory]] = relationship(
        "DepartmentCategory", back_populates="department"
    )

    def __repr__(self) -> str:
        return f"<Department {self.code} {self.name} active={self.is_active}>"


class DepartmentCategory(Base, UUIDMixin, TimestampMixin):
    """Category-to-department routing rule.

    Seeded at database-creation time.  The Department Router agent
    reads these rows; no routing logic is hardcoded.
    """

    __tablename__ = "department_categories"
    __table_args__ = (
        UniqueConstraint(
            "issue_category",
            "department_id",
            name="uq_category_department",
        ),
    )

    issue_category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    # ── Relationships ──────────────────────────────────────────────────
    department: Mapped[Department] = relationship("Department", back_populates="category_links")

    def __repr__(self) -> str:
        return f"<DepartmentCategory {self.issue_category} " f"-> {self.department_id}>"
