from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from backend.models.notifications import (
    DeliveryStatus,
    NotificationChannel,
    NotificationPriority,
    NotificationType,
)


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    citizen_id: UUID
    report_id: UUID | None = None
    title: str
    message: str
    notification_type: NotificationType
    priority: NotificationPriority
    channel: NotificationChannel
    delivery_status: DeliveryStatus
    read_at: datetime | None = None
    delivered_at: datetime | None = None
    deep_link: str | None = None
    payload: dict[str, Any] | None = None
    created_at: datetime

class NotificationMarkRead(BaseModel):
    notification_ids: list[UUID]
