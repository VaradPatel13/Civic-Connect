from typing import Sequence, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.notifications import NotificationRepository
from backend.models.notifications import Notification

class NotificationService:
    def __init__(self, session: AsyncSession):
        self.notification_repo = NotificationRepository(session)

    async def list_notifications(self, citizen_id: UUID, skip: int = 0, limit: int = 50) -> Sequence[Notification]:
        return await self.notification_repo.list_for_user(citizen_id=citizen_id, skip=skip, limit=limit)

    async def mark_as_read(self, citizen_id: UUID, notification_ids: List[UUID]) -> int:
        return await self.notification_repo.mark_as_read(citizen_id=citizen_id, notification_ids=notification_ids)
