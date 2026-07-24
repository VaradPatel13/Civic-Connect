from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.rewards import RewardRepository
from backend.schemas.rewards import RewardBalanceResponse, RewardTransactionResponse

class RewardService:
    def __init__(self, session: AsyncSession):
        self.reward_repo = RewardRepository(session)

    async def get_user_summary(self, citizen_id: UUID) -> RewardBalanceResponse:
        balance = await self.reward_repo.get_user_balance(citizen_id)
        transactions = await self.reward_repo.list_transactions(citizen_id)

        tier = "Bronze"
        if balance >= 1000:
            tier = "Gold"
        elif balance >= 500:
            tier = "Silver"

        tx_responses = [RewardTransactionResponse.model_validate(tx) for tx in transactions]

        return RewardBalanceResponse(
            citizen_id=citizen_id,
            total_points=balance,
            tier=tier,
            transactions=tx_responses
        )
