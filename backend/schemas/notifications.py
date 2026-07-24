from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from backend.models.notifications import NotificationType, NotificationPriority, NotificationChannel, DeliveryStatus

class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    citizen_id: UUID
    report_id: Optional[UUID] = None
    title: str
    message: str
    notification_type: NotificationType
    priority: NotificationPriority
    channel: NotificationChannel
    delivery_status: DeliveryStatus
    read_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    deep_link: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    created_at: datetime

class NotificationMarkRead(BaseModel):
    notification_ids: list[UUID]
