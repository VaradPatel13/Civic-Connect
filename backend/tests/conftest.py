from typing import Any, cast

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

import backend.models  # noqa: F401
from backend.core.database import engine
from backend.main import app
from backend.models.base import Base


@pytest_asyncio.fixture(autouse=True)
async def setup_and_cleanup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=cast(Any, app))
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
