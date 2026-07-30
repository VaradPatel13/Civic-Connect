from typing import Any, cast

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

import backend.models  # noqa: F401
from backend.core.database import engine
from backend.main import app
from backend.models.base import Base


@pytest_asyncio.fixture(autouse=True)
async def setup_and_cleanup_db():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield
        # D-03: Drop tables after each test to prevent stale data pollution between runs
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()
    except Exception:
        yield




@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=cast(Any, app))
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
