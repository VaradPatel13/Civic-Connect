from typing import Optional, Sequence
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from backend.models.rewards import RewardTransaction, RewardReason

class RewardRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_balance(self, citizen_id: UUID) -> int:
        stmt = (
            select(func.coalesce(func.sum(RewardTransaction.points), 0))
            .where(RewardTransaction.citizen_id == citizen_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def add_transaction(
        self,
        citizen_id: UUID,
        points: int,
        reason: RewardReason,
        description: Optional[str] = None,
        report_id: Optional[UUID] = None,
        awarded_by: str = "system"
    ) -> RewardTransaction:
        current_balance = await self.get_user_balance(citizen_id)
        new_balance = current_balance + points

        tx = RewardTransaction(
            citizen_id=citizen_id,
            report_id=report_id,
            points=points,
            reason=reason,
            description=description,
            previous_balance=current_balance,
            new_balance=new_balance,
            awarded_by=awarded_by,
            is_automated=True
        )
        self.session.add(tx)
        await self.session.commit()
        await self.session.refresh(tx)
        return tx

    async def list_transactions(self, citizen_id: UUID, skip: int = 0, limit: int = 50) -> Sequence[RewardTransaction]:
        stmt = (
            select(RewardTransaction)
            .where(RewardTransaction.citizen_id == citizen_id)
            .order_by(RewardTransaction.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
