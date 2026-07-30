from collections.abc import AsyncGenerator
from typing import Any, cast

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import backend.models  # noqa: F401
from backend.api.deps import get_db
from backend.core.config import settings
from backend.main import app
from backend.models.base import Base

TEST_DATABASE_URL = settings.database_url.rsplit('/', 1)[0] + '/civicconnect_test'

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_and_cleanup_db():
    async with test_engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=cast(Any, app))
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
