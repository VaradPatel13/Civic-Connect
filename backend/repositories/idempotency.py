import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.idempotency import IdempotencyKey


class IdempotencyRepository:
    """Repository for managing IdempotencyKey persistence in PostgreSQL."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_key(self, idempotency_key: str) -> IdempotencyKey | None:
        """Retrieves an existing idempotency record by key."""
        stmt = select(IdempotencyKey).where(IdempotencyKey.idempotency_key == idempotency_key)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def create(
        self,
        idempotency_key: str,
        request_hash: str,
        report_id: uuid.UUID | None = None,
        status_code: int = 201,
        response_snapshot: dict[str, Any] | None = None,
        ttl_hours: int = 24,
    ) -> IdempotencyKey:
        """Creates and stores a new idempotency key record with expiration."""
        expires_at = datetime.now(UTC) + timedelta(hours=ttl_hours)
        record = IdempotencyKey(
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            report_id=report_id,
            status_code=status_code,
            response_snapshot=response_snapshot,
            expires_at=expires_at,
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def update_snapshot(
        self,
        record: IdempotencyKey,
        status_code: int,
        response_snapshot: dict[str, Any],
        report_id: uuid.UUID | None = None,
    ) -> IdempotencyKey:
        """Updates an existing idempotency record with the final response payload."""
        record.status_code = status_code
        record.response_snapshot = response_snapshot
        if report_id:
            record.report_id = report_id
        await self.db.commit()
        await self.db.refresh(record)
        return record
