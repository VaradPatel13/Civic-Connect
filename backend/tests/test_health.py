from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_healthy(async_client: AsyncClient):
    """Verify health check returns 200 and healthy status when DB is available (PR-01)."""
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock()
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_conn

    mock_engine = MagicMock()
    mock_engine.begin.return_value = mock_cm

    with patch("backend.main.engine", mock_engine):
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "CivicConnect"
        assert data["checks"]["database"] == "healthy"


@pytest.mark.asyncio
async def test_health_check_unhealthy(async_client: AsyncClient):
    """Verify health check returns 503 and unhealthy status when DB connection fails (PR-01)."""
    mock_engine = MagicMock()
    mock_engine.begin.side_effect = ConnectionRefusedError("DB offline")

    with patch("backend.main.engine", mock_engine):
        response = await async_client.get("/health")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "unhealthy" in data["checks"]["database"]


@pytest.mark.asyncio
async def test_root_welcome(async_client: AsyncClient):
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "CivicConnect" in data["message"]
