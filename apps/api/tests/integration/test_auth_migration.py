import asyncio
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import text

from alembic import command
from app.db.session import engine

API_ROOT = Path(__file__).resolve().parents[2]
AUTH_REVISION = "202605260100"


def _alembic_config() -> Config:
    return Config(str(API_ROOT / "alembic.ini"))


async def _fetch_scalar(statement: str) -> object:
    async with engine.connect() as connection:
        result = await connection.execute(text(statement))
        return result.scalar_one()


@pytest.mark.integration
async def test_auth_migration_upgrade_and_downgrade_clean() -> None:
    config = _alembic_config()

    await asyncio.to_thread(command.downgrade, config, "base")
    await asyncio.to_thread(command.upgrade, config, AUTH_REVISION)

    try:
        table_count = await _fetch_scalar(
            """
            SELECT count(*)
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name IN (
                'users',
                'user_oauth_accounts',
                'refresh_tokens',
                'audit_logs'
              )
            """
        )
        rls_count = await _fetch_scalar(
            """
            SELECT count(*)
            FROM pg_class
            WHERE relname IN (
                'users',
                'user_oauth_accounts',
                'refresh_tokens',
                'audit_logs'
              )
              AND relrowsecurity
            """
        )
        uuid_version = await _fetch_scalar(
            "SELECT substring(uuid_generate_v7()::text from 15 for 1)"
        )

        assert table_count == 4
        assert rls_count == 4
        assert uuid_version == "7"
    finally:
        await engine.dispose()
        await asyncio.to_thread(command.downgrade, config, "base")
        remaining_tables = await _fetch_scalar(
            """
            SELECT count(*)
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name IN (
                'users',
                'user_oauth_accounts',
                'refresh_tokens',
                'audit_logs'
              )
            """
        )
        assert remaining_tables == 0
        await engine.dispose()
        await asyncio.to_thread(command.upgrade, config, "head")
        await engine.dispose()
