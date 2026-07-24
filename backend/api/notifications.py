from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.core.database import get_db
from backend.models.citizens import Citizen
from backend.schemas.notifications import NotificationMarkRead, NotificationResponse
from backend.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=list[NotificationResponse])
async def list_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: Citizen = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    return await service.list_notifications(citizen_id=current_user.id, skip=skip, limit=limit)


@router.post("/read")
async def mark_notifications_read(
    data: NotificationMarkRead,
    current_user: Citizen = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    count = await service.mark_as_read(
        citizen_id=current_user.id, notification_ids=data.notification_ids
    )
    return {"updated": count}
