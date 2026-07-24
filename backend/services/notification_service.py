from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.notifications import Notification
from backend.repositories.notifications import NotificationRepository


class NotificationService:
    def __init__(self, session: AsyncSession):
        self.notification_repo = NotificationRepository(session)

    async def list_notifications(self, citizen_id: UUID, skip: int = 0, limit: int = 50) -> Sequence[Notification]:
        return await self.notification_repo.list_for_user(citizen_id=citizen_id, skip=skip, limit=limit)

    async def mark_as_read(self, citizen_id: UUID, notification_ids: list[UUID]) -> int:
        return await self.notification_repo.mark_as_read(citizen_id=citizen_id, notification_ids=notification_ids)
