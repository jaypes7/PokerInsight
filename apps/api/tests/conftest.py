import os
from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

os.environ.setdefault("APP_ENV", "ci")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:ci@localhost:5432/ci")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    from app.db.session import SessionFactory

    async with SessionFactory() as session:
        transaction = await session.begin()
        try:
            yield session
        finally:
            await transaction.rollback()


@pytest.fixture(autouse=True)
async def dispose_engine_between_tests() -> AsyncIterator[None]:
    yield
    from app.db.session import engine

    await engine.dispose()
