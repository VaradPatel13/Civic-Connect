from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from backend.models.rewards import RewardReason


class RewardTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    citizen_id: UUID
    report_id: UUID | None = None
    points: int
    reason: RewardReason
    description: str | None = None
    previous_balance: int
    new_balance: int
    awarded_by: str
    is_automated: bool
    created_at: datetime

class RewardBalanceResponse(BaseModel):
    citizen_id: UUID
    total_points: int
    tier: str = "Bronze"
    transactions: list[RewardTransactionResponse] = []
