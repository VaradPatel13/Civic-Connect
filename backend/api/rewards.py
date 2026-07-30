from fastapi import APIRouter, Depends

from backend.api.deps import get_current_user, get_reward_service
from backend.models.citizens import Citizen
from backend.schemas.rewards import RewardBalanceResponse
from backend.services.reward_service import RewardService

router = APIRouter(prefix="/rewards", tags=["Rewards"])


@router.get("/summary", response_model=RewardBalanceResponse)
async def get_reward_summary(
    current_user: Citizen = Depends(get_current_user),
    service: RewardService = Depends(get_reward_service),
):
    return await service.get_user_summary(citizen_id=current_user.id)

