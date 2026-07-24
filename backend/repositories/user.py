import uuid
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.citizens import Citizen, OTPCode, Session


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_phone(self, phone: str) -> Citizen | None:
        result = await self.db.execute(select(Citizen).where(Citizen.phone == phone))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Citizen | None:
        result = await self.db.execute(select(Citizen).where(Citizen.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, citizen_id: uuid.UUID) -> Citizen | None:
        result = await self.db.execute(select(Citizen).where(Citizen.id == citizen_id))
        return result.scalar_one_or_none()

    async def create(self, **kwargs: Any) -> Citizen:
        citizen = Citizen(**kwargs)
        self.db.add(citizen)
        await self.db.commit()
        await self.db.refresh(citizen)
        return citizen

    async def create_otp(self, **kwargs: Any) -> OTPCode:
        otp = OTPCode(**kwargs)
        self.db.add(otp)
        await self.db.commit()
        await self.db.refresh(otp)
        return otp

    async def get_latest_otp(self, phone: str, purpose: str = "register") -> OTPCode | None:
        result = await self.db.execute(
            select(OTPCode)
            .where(OTPCode.phone == phone, OTPCode.purpose == purpose)
            .order_by(OTPCode.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create_session(self, **kwargs: Any) -> Session:
        session = Session(**kwargs)
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_session(self, session_id: uuid.UUID) -> Session | None:
        result = await self.db.execute(select(Session).where(Session.id == session_id))
        return result.scalar_one_or_none()

    async def revoke_session(self, session_id: uuid.UUID) -> None:
        await self.db.execute(
            update(Session)
            .where(Session.id == session_id)
            .values(revoked_at=func.now())
        )
        await self.db.commit()

    async def revoke_all_sessions(self, citizen_id: uuid.UUID) -> None:
        await self.db.execute(
            update(Session)
            .where(Session.citizen_id == citizen_id, Session.revoked_at.is_(None))
            .values(revoked_at=func.now())
        )
        await self.db.commit()
