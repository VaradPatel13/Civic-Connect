import pytest
from httpx import AsyncClient
from sqlalchemy import select, func

from backend.models.idempotency import IdempotencyKey
from backend.models.reports import Report
from backend.repositories.user import UserRepository
from backend.services.auth_service import AuthService
from backend.tests.conftest import TestingSessionLocal


@pytest.mark.asyncio
async def test_idempotency_report_creation(async_client: AsyncClient):
    async with TestingSessionLocal() as db_session:
        user_repo = UserRepository(db_session)
        auth_service = AuthService(user_repo)
        user = await user_repo.create(
            phone="+919876543210",
            display_name="Idempotency Test User",
            password_hash="test_hash",
            is_active=True,
        )
        token = auth_service.create_access_token(str(user.id), role=str(user.role.value))

    headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "test-key-uuid-12345"}

    payload = {
        "title": "Idempotent Pothole Report",
        "description": "Pothole near main gate causing traffic issues.",
        "issue_category": "roads",
        "urgency": "medium",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "address": "123 Main St",
        "photos": ["https://example.com/pothole.jpg"],
    }

    # 1. First request — creates report and saves idempotency snapshot
    response1 = await async_client.post("/api/v1/reports/", json=payload, headers=headers)
    assert response1.status_code == 201
    data1 = response1.json()
    assert data1["title"] == "Idempotent Pothole Report"
    report_id = data1["id"]

    # Verify 1 report in DB and key stored
    async with TestingSessionLocal() as db_session:
        count_stmt = select(func.count(Report.id))
        res = await db_session.execute(count_stmt)
        assert res.scalar_one() == 1

        key_stmt = select(IdempotencyKey).where(IdempotencyKey.idempotency_key == "test-key-uuid-12345")
        key_res = await db_session.execute(key_stmt)
        key_record = key_res.scalar_one_or_none()
        assert key_record is not None
        assert key_record.response_snapshot is not None
        assert key_record.response_snapshot["id"] == report_id

    # 2. Second request — identical Idempotency-Key and payload -> returns cached snapshot
    response2 = await async_client.post("/api/v1/reports/", json=payload, headers=headers)
    assert response2.status_code == 201
    data2 = response2.json()
    assert data2["id"] == report_id

    # Verify STILL only 1 report in DB (no duplicate created)
    async with TestingSessionLocal() as db_session:
        res_after = await db_session.execute(count_stmt)
        assert res_after.scalar_one() == 1

    # 3. Third request — same Idempotency-Key with DIFFERENT payload -> 422 Unprocessable Entity
    mismatched_payload = {**payload, "title": "Different Mismatched Title"}
    response3 = await async_client.post("/api/v1/reports/", json=mismatched_payload, headers=headers)
    assert response3.status_code == 422
    assert "different request payload" in response3.json()["detail"].lower()
