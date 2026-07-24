import random

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_auth_full_flow(async_client: AsyncClient):
    rand_num = random.randint(10000000, 99999999)
    phone = f"98{rand_num}"
    email = f"user_{rand_num}@civicconnect.org"
    password = "TestPassword123!"

    # 1. Register User
    reg_response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "phone": phone,
            "email": email,
            "display_name": f"Test Citizen {rand_num}",
            "password": password,
            "preferred_language": "en",
        },
    )
    assert reg_response.status_code == 201
    reg_data = reg_response.json()
    assert "access_token" in reg_data
    assert "refresh_token" in reg_data
    assert reg_data["user"]["phone"] == phone

    # 2. Login User
    login_response = await async_client.post(
        "/api/v1/auth/login",
        json={"phone": phone, "password": password},
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    token = login_data["access_token"]
    refresh_token = login_data["refresh_token"]

    # 3. Get User Profile (/me)
    headers = {"Authorization": f"Bearer {token}"}
    me_response = await async_client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["phone"] == phone

    # 4. Refresh Token
    ref_response = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert ref_response.status_code == 200
    assert "access_token" in ref_response.json()

    # 5. Logout
    logout_response = await async_client.post("/api/v1/auth/logout", headers=headers)
    assert logout_response.status_code == 200
