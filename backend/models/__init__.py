"""CivicConnect SQLAlchemy model registry.

Import this module to register all models with the SQLAlchemy metadata
before calling ``Base.metadata.create_all(...)`` or running migrations.

Typical usage::

    from backend.models import Base
    # all models are now registered
"""

from backend.models.agent_executions import (
    AgentExecution,
    AgentStatus,
)
from backend.models.base import Base
from backend.models.citizens import Citizen, OTPCode, Session
from backend.models.departments import Department, DepartmentCategory
from backend.models.notifications import (
    DeliveryStatus,
    Notification,
    NotificationChannel,
    NotificationPriority,
    NotificationType,
)
from backend.models.reports import (
    Assignment,
    AssignmentStatus,
    IssueCategory,
    Photo,
    Report,
    ReportStatus,
    StatusLog,
    UrgencyLevel,
    Ward,
)
from backend.models.rewards import (
    RewardReason,
    RewardTransaction,
)

__all__ = [
    # Base
    "Base",
    # Citizens
    "Citizen",
    "Session",
    "OTPCode",
    # Wards & Reports
    "Ward",
    "Report",
    "Photo",
    "Assignment",
    "StatusLog",
    # Departments
    "Department",
    "DepartmentCategory",
    # Notifications
    "Notification",
    # Rewards
    "RewardTransaction",
    # AI Pipeline
    "AgentExecution",
    # Enums
    "ReportStatus",
    "IssueCategory",
    "UrgencyLevel",
    "AssignmentStatus",
    "NotificationType",
    "NotificationPriority",
    "NotificationChannel",
    "DeliveryStatus",
    "RewardReason",
    "AgentStatus",
]
