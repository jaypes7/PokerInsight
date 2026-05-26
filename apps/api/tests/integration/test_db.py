import pytest
from sqlalchemy import text

from app.db.session import SessionFactory


@pytest.mark.integration
async def test_db_select_one() -> None:
    async with SessionFactory() as session:
        result = await session.execute(text("SELECT 1"))

    assert result.scalar_one() == 1
