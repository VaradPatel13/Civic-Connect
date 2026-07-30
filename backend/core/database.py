from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.core.config import settings

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=10,
    max_overflow=20,
    connect_args={"statement_cache_size": 0},
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
