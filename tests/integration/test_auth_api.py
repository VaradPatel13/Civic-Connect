import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_root_and_health():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "Welcome" in response.json()["message"]

        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


def test_register_and_login_flow():
    with TestClient(app) as client:
        test_phone = "9876543210"
        test_password = "SecurePassword123!"

        # 1. Register Citizen
        reg_payload = {
            "display_name": "Jane Citizen",
            "phone": test_phone,
            "password": test_password,
            "email": "jane@example.com",
            "preferred_language": "en",
        }
        reg_res = client.post("/api/v1/auth/register", json=reg_payload)
        assert reg_res.status_code in [201, 409]  # 201 if fresh, 409 if already exists

        if reg_res.status_code == 201:
            data = reg_res.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["user"]["phone"] == test_phone
            assert data["user"]["display_name"] == "Jane Citizen"

        # 2. Login Citizen
        login_payload = {
            "phone": test_phone,
            "password": test_password,
        }
        login_res = client.post("/api/v1/auth/login", json=login_payload)
        assert login_res.status_code == 200
        login_data = login_res.json()
        assert "access_token" in login_data
        assert "refresh_token" in login_data

        token = login_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Get Me Profile
        me_res = client.get("/api/v1/auth/me", headers=headers)
        assert me_res.status_code == 200
        assert me_res.json()["phone"] == test_phone

        # 4. Refresh Token
        refresh_res = client.post("/api/v1/auth/refresh", json={"refresh_token": login_data["refresh_token"]})
        assert refresh_res.status_code == 200
        assert "access_token" in refresh_res.json()

        # 5. Logout
        logout_res = client.post("/api/v1/auth/logout", headers=headers)
        assert logout_res.status_code == 200
        assert logout_res.json()["message"] == "Logged out successfully"
