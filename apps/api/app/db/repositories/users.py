from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import RowMapping, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.schema import refresh_tokens, users


class UsersRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_user(
        self,
        email: str,
        display_name: str,
        password_hash: str,
        locale: str,
    ) -> RowMapping:
        result = await self.session.execute(
            insert(users)
            .values(
                email=email.lower(),
                display_name=display_name,
                password_hash=password_hash,
                locale=locale,
            )
            .returning(users)
        )
        return result.mappings().one()

    async def get_by_email(self, email: str) -> RowMapping | None:
        result = await self.session.execute(
            select(users).where(users.c.email == email.lower(), users.c.deleted_at.is_(None))
        )
        return result.mappings().one_or_none()

    async def get_by_id(self, user_id: UUID) -> RowMapping | None:
        result = await self.session.execute(
            select(users).where(users.c.id == user_id, users.c.deleted_at.is_(None))
        )
        return result.mappings().one_or_none()

    async def mark_login(self, user_id: UUID) -> None:
        await self.session.execute(
            update(users).where(users.c.id == user_id).values(last_login_at=datetime.now(UTC))
        )

    async def create_refresh_token(self, values: dict[str, Any]) -> RowMapping:
        result = await self.session.execute(
            insert(refresh_tokens).values(**values).returning(refresh_tokens)
        )
        return result.mappings().one()

    async def revoke_refresh_family(self, family_id: UUID) -> None:
        await self.session.execute(
            update(refresh_tokens)
            .where(refresh_tokens.c.family_id == family_id)
            .values(revoked_at=datetime.now(UTC))
        )

    async def get_refresh_by_hash(self, token_hash: str) -> RowMapping | None:
        result = await self.session.execute(
            select(refresh_tokens).where(refresh_tokens.c.token_hash == token_hash)
        )
        return result.mappings().one_or_none()

    async def mark_refresh_used(self, token_hash: str) -> None:
        await self.session.execute(
            update(refresh_tokens)
            .where(refresh_tokens.c.token_hash == token_hash)
            .values(used_at=datetime.now(UTC), revoked_at=datetime.now(UTC))
        )
