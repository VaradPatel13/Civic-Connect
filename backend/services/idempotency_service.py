import hashlib
import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.idempotency import IdempotencyKey
from backend.repositories.idempotency import IdempotencyRepository

logger = logging.getLogger(__name__)


class IdempotencyService:
    """Service layer handling idempotency checks, request hashing, and response caching."""

    def __init__(self, db: AsyncSession):
        self.repo = IdempotencyRepository(db)

    @staticmethod
    def compute_request_hash(data: Any) -> str:
        """Computes a deterministic SHA-256 hash of a request body."""
        if hasattr(data, "model_dump_json"):
            json_str = data.model_dump_json(by_alias=True)
        elif isinstance(data, dict):
            json_str = json.dumps(data, sort_keys=True, default=str)
        else:
            json_str = str(data)
        return hashlib.sha256(json_str.encode("utf-8")).hexdigest()

    async def get_cached_response(
        self, idempotency_key: str | None, request_data: Any
    ) -> tuple[bool, dict[str, Any] | None, int]:
        """Checks for an existing idempotency record.

        Returns:
            (is_duplicate, cached_response_snapshot, status_code)
        """
        if not idempotency_key:
            return False, None, 201

        existing = await self.repo.get_by_key(idempotency_key)
        if not existing:
            return False, None, 201

        # Check key expiration
        now = datetime.now(UTC)
        if existing.expires_at and existing.expires_at < now:
            logger.info("Idempotency key %s has expired", idempotency_key)
            return False, None, 201

        # Check payload mismatch (same key, different request content)
        current_hash = self.compute_request_hash(request_data)
        if existing.request_hash != current_hash:
            logger.warning("Idempotency key %s reused with mismatched request payload", idempotency_key)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Idempotency-Key was already used with a different request payload.",
            )

        if existing.response_snapshot is not None:
            logger.info("Idempotency hit for key %s — returning cached response", idempotency_key)
            return True, existing.response_snapshot, existing.status_code

        return False, None, 201

    async def save_response(
        self,
        idempotency_key: str | None,
        request_data: Any,
        response_data: Any,
        status_code: int = 201,
        report_id: uuid.UUID | None = None,
    ) -> IdempotencyKey | None:
        """Persists the response snapshot for an idempotency key."""
        if not idempotency_key:
            return None

        request_hash = self.compute_request_hash(request_data)

        if hasattr(response_data, "model_dump"):
            snapshot = response_data.model_dump(mode="json", by_alias=True)
        elif isinstance(response_data, dict):
            snapshot = response_data
        else:
            try:
                from backend.schemas.reports import ReportResponse
                snapshot = ReportResponse.model_validate(response_data).model_dump(mode="json", by_alias=True)
            except Exception:
                snapshot = json.loads(json.dumps(response_data, default=str))

        existing = await self.repo.get_by_key(idempotency_key)
        if existing:
            return await self.repo.update_snapshot(
                record=existing,
                status_code=status_code,
                response_snapshot=snapshot,
                report_id=report_id,
            )

        return await self.repo.create(
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            report_id=report_id,
            status_code=status_code,
            response_snapshot=snapshot,
        )
