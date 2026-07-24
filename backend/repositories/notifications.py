from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.models.notifications import (
    DeliveryStatus,
    Notification,
    NotificationChannel,
    NotificationPriority,
    NotificationType,
)


class NotificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_notification(
        self,
        citizen_id: UUID,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.SYSTEM,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        channel: NotificationChannel = NotificationChannel.IN_APP,
        report_id: UUID | None = None,
        deep_link: str | None = None,
        payload: dict | None = None,
    ) -> Notification:
        notification = Notification(
            citizen_id=citizen_id,
            report_id=report_id,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            channel=channel,
            delivery_status=DeliveryStatus.DELIVERED,
            delivered_at=datetime.now(UTC),
            deep_link=deep_link,
            payload=payload,
        )
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)
        return notification

    async def list_for_user(
        self, citizen_id: UUID, skip: int = 0, limit: int = 50
    ) -> Sequence[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.citizen_id == citizen_id)
            .order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def mark_as_read(self, citizen_id: UUID, notification_ids: list[UUID]) -> int:
        stmt = (
            update(Notification)
            .where(Notification.citizen_id == citizen_id)
            .where(Notification.id.in_(notification_ids))
            .values(delivery_status=DeliveryStatus.READ, read_at=datetime.now(UTC))
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount
