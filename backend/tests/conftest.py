from typing import Any, cast

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.core.database import engine
from backend.main import app


@pytest_asyncio.fixture(autouse=True)
async def cleanup_db_connections():
    yield
    await engine.dispose()


@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=cast(Any, app))
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
