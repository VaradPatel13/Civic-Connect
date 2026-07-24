from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.core.database import get_db
from backend.models.citizens import Citizen
from backend.schemas.rewards import RewardBalanceResponse
from backend.services.reward_service import RewardService

router = APIRouter(prefix="/rewards", tags=["Rewards"])


@router.get("/summary", response_model=RewardBalanceResponse)
async def get_reward_summary(
    current_user: Citizen = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    service = RewardService(db)
    return await service.get_user_summary(citizen_id=current_user.id)
