from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    hash_password,
    new_refresh_token,
    token_hash,
    verify_password,
)
from app.db.repositories.users import UsersRepository


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.users = UsersRepository(session)

    async def register(
        self,
        email: str,
        password: str,
        display_name: str,
        locale: str,
    ) -> UUID:
        user = await self.users.create_user(email, display_name, hash_password(password), locale)
        await self.session.commit()
        return cast(UUID, user["id"])

    async def login(self, email: str, password: str) -> tuple[dict[str, object], str, str] | None:
        user = await self.users.get_by_email(email)
        if user is None or not user["password_hash"]:
            return None
        if not verify_password(password, str(user["password_hash"])):
            return None
        await self.users.mark_login(user["id"])
        access = create_access_token(user["id"], self.settings)
        refresh = await self._issue_refresh(user["id"], None, None)
        await self.session.commit()
        return (
            {
                "id": user["id"],
                "email": user["email"],
                "display_name": user["display_name"],
                "plan": "free",
            },
            access,
            refresh,
        )

    async def refresh(self, refresh_token: str) -> tuple[str, str] | None:
        hashed = token_hash(refresh_token)
        row = await self.users.get_refresh_by_hash(hashed)
        now = datetime.now(UTC)
        if row is None:
            return None
        if row["revoked_at"] is not None or row["expires_at"] <= now:
            await self.users.revoke_refresh_family(row["family_id"])
            await self.session.commit()
            return None
        await self.users.mark_refresh_used(hashed)
        access = create_access_token(row["user_id"], self.settings)
        new_token = await self._issue_refresh(row["user_id"], row["family_id"], row["id"])
        await self.session.commit()
        return access, new_token

    async def logout(self, refresh_token: str | None) -> None:
        if refresh_token:
            await self.users.mark_refresh_used(token_hash(refresh_token))
            await self.session.commit()

    async def _issue_refresh(
        self,
        user_id: UUID,
        family_id: UUID | None,
        parent_id: UUID | None,
    ) -> str:
        token = new_refresh_token()
        await self.users.create_refresh_token(
            {
                "user_id": user_id,
                "token_hash": token_hash(token),
                "family_id": family_id or uuid4(),
                "parent_id": parent_id,
                "expires_at": datetime.now(UTC)
                + timedelta(seconds=self.settings.jwt_refresh_ttl_seconds),
            }
        )
        return token
