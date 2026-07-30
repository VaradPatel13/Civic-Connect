"""
Tests for FastAPI lifespan context manager (F-01) and Request ID middleware (F-03).
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from backend.main import app, lifespan


@pytest.mark.asyncio
async def test_request_id_middleware_generates_header(async_client: AsyncClient):
    """Verify that incoming requests receive an X-Request-ID response header if omitted."""
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock()
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_conn
    mock_engine = MagicMock()
    mock_engine.begin.return_value = mock_cm

    with patch("backend.main.engine", mock_engine):
        response = await async_client.get("/health")
        assert response.status_code == 200
        assert "x-request-id" in response.headers
        # Verify valid UUID structure
        req_id = response.headers["x-request-id"]
        assert len(req_id) == 36
        uuid_obj = uuid.UUID(req_id)
        assert str(uuid_obj) == req_id


@pytest.mark.asyncio
async def test_request_id_middleware_propagates_existing_header(async_client: AsyncClient):
    """Verify that incoming X-Request-ID header is propagated to the response header."""
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock()
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_conn
    mock_engine = MagicMock()
    mock_engine.begin.return_value = mock_cm

    custom_request_id = "test-custom-request-id-12345"
    with patch("backend.main.engine", mock_engine):
        response = await async_client.get("/health", headers={"X-Request-ID": custom_request_id})
        assert response.status_code == 200
        assert response.headers.get("x-request-id") == custom_request_id


@pytest.mark.asyncio
async def test_lifespan_context_manager():
    """Verify that lifespan executes startup and shutdown blocks without error."""
    async with lifespan(app):
        # Application context active
        pass

