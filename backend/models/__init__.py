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
from backend.models.idempotency import IdempotencyKey
from backend.models.model_registry import ModelRegistry
from backend.models.notifications import (
    DeliveryStatus,
    Notification,
    NotificationChannel,
    NotificationPriority,
    NotificationType,
)
from backend.models.report_events import ReportEvent
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
from backend.models.workflow_state import (
    WorkflowState,
    WorkflowStatus,
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
    # AI Pipeline & Persistence Engine
    "AgentExecution",
    "WorkflowState",
    "IdempotencyKey",
    "ModelRegistry",
    "ReportEvent",
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
    "WorkflowStatus",
]
