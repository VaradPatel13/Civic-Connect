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
