import random

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_reports_and_ai_pipeline(async_client: AsyncClient):
    rand_num = random.randint(10000000, 99999999)
    phone = f"97{rand_num}"

    # Register & Auth
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "phone": phone,
            "display_name": f"Reporter {rand_num}",
            "password": "Password123!",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Submit Report
    report_res = await async_client.post(
        "/api/v1/reports/",
        headers=headers,
        json={
            "title": f"Broken Pothole on Main St {rand_num}",
            "description": "Deep pothole causing traffic slowdown near civic center.",
            "issue_category": "roads",
            "urgency": "high",
            "latitude": 18.5204,
            "longitude": 73.8567,
            "address": "Main Street, Pune",
            "photos": ["https://example.com/pothole.jpg"],
        },
    )
    assert report_res.status_code == 201
    rep_data = report_res.json()
    report_id = rep_data["id"]

    # Get Single Report
    get_res = await async_client.get(f"/api/v1/reports/{report_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == report_id

    # List User Reports
    list_res = await async_client.get("/api/v1/reports/", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # Rewards check
    rewards_res = await async_client.get("/api/v1/rewards/summary", headers=headers)
    assert rewards_res.status_code == 200
    assert rewards_res.json()["total_points"] >= 50

    # Notifications check
    notif_res = await async_client.get("/api/v1/notifications/", headers=headers)
    assert notif_res.status_code == 200
    assert len(notif_res.json()) >= 1


def test_report_create_photo_url_validation_unit():
    """Unit test for ReportCreate photo URL validation (S-12)."""
    from pydantic import ValidationError

    from backend.models.reports import IssueCategory
    from backend.schemas.reports import ReportCreate

    # Valid http and https URLs
    valid_report = ReportCreate(
        title="Valid Report Title",
        description="This is a valid report description for testing.",
        issue_category=IssueCategory.ROADS,
        photos=["http://example.com/photo1.jpg", "https://cloudinary.com/photo2.jpg"],
    )
    assert len(valid_report.photos) == 2

    # Malicious javascript: URL scheme
    with pytest.raises(ValidationError) as exc_info:
        ReportCreate(
            title="Bad Report Title",
            description="This is a valid report description for testing.",
            issue_category=IssueCategory.ROADS,
            photos=["javascript:alert(1)"],
        )
    assert "Invalid photo URL" in str(exc_info.value)

    # Malicious data: URL scheme
    with pytest.raises(ValidationError) as exc_info2:
        ReportCreate(
            title="Bad Report Title 2",
            description="This is a valid report description for testing.",
            issue_category=IssueCategory.ROADS,
            photos=["data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg=="],
        )
    assert "Invalid photo URL" in str(exc_info2.value)


@pytest.mark.asyncio
async def test_add_photo_url_validation():
    """Verify ReportRepository.add_photo validates URL scheme and netloc (B-06)."""
    from unittest.mock import AsyncMock, MagicMock
    from uuid import uuid4

    from backend.repositories.reports import ReportRepository

    mock_session = MagicMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    repo = ReportRepository(session=mock_session)
    report_id = uuid4()

    # Valid URL
    photo = await repo.add_photo(report_id, "https://res.cloudinary.com/demo/image/upload/v123/sample.jpg")
    assert photo.cloudinary_url == "https://res.cloudinary.com/demo/image/upload/v123/sample.jpg"
    assert photo.public_id == "sample.jpg"

    # Invalid URL scheme (file://)
    with pytest.raises(ValueError) as exc:
        await repo.add_photo(report_id, "file:///etc/passwd")
    assert "Invalid photo URL format or scheme" in str(exc.value)

    # Invalid URL scheme (javascript:)
    with pytest.raises(ValueError) as exc2:
        await repo.add_photo(report_id, "javascript:alert(1)")
    assert "Invalid photo URL format or scheme" in str(exc2.value)


def test_report_created_at_indexes():
    """Verify Report model defines indexes on created_at for query performance (PR-03)."""
    from typing import cast

    from sqlalchemy import Table

    from backend.models.reports import Report

    table = cast(Table, Report.__table__)
    index_names = {index.name for index in table.indexes}
    assert "idx_reports_created_at" in index_names
    assert "idx_reports_citizen_created_at" in index_names





