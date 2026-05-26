from typing import cast
from uuid import UUID

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.schema import sessions


class SessionsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_for_import_window(
        self,
        user_id: UUID,
        started_at: object,
        ended_at: object,
        total_hands: int,
        net_profit_cents: int,
        currency: str,
    ) -> UUID:
        result = await self.session.execute(
            insert(sessions)
            .values(
                user_id=user_id,
                started_at=started_at,
                ended_at=ended_at,
                total_hands=total_hands,
                net_profit_cents=net_profit_cents,
                currency=currency,
            )
            .returning(sessions.c.id)
        )
        return cast(UUID, result.scalar_one())
