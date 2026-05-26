from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.core.security import hash_password, token_hash
from app.services.auth import AuthService


class FakeSession:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1


class FakeUsersRepository:
    user_id = uuid4()
    refresh_id = uuid4()
    family_id = uuid4()
    password_hash = hash_password("secret")
    refresh_rows: dict[str, dict[str, object]] = {}
    created_refresh_tokens: list[dict[str, object]] = []
    revoked_families: list[object] = []
    used_hashes: list[str] = []
    marked_logins: list[object] = []

    def __init__(self, session: FakeSession) -> None:
        self.session = session

    async def create_user(
        self, email: str, display_name: str, password_hash_value: str, locale: str
    ) -> dict[str, object]:
        return {
            "id": self.user_id,
            "email": email,
            "display_name": display_name,
            "password_hash": password_hash_value,
            "locale": locale,
        }

    async def get_by_email(self, email: str) -> dict[str, object] | None:
        if email != "ada@example.com":
            return None
        return {
            "id": self.user_id,
            "email": email,
            "display_name": "Ada",
            "password_hash": self.password_hash,
        }

    async def mark_login(self, user_id: object) -> None:
        self.marked_logins.append(user_id)

    async def create_refresh_token(self, payload: dict[str, object]) -> None:
        self.created_refresh_tokens.append(payload)

    async def get_refresh_by_hash(self, hashed: str) -> dict[str, object] | None:
        return self.refresh_rows.get(hashed)

    async def revoke_refresh_family(self, family_id: object) -> None:
        self.revoked_families.append(family_id)

    async def mark_refresh_used(self, hashed: str) -> None:
        self.used_hashes.append(hashed)


@pytest.fixture(autouse=True)
def reset_fake_repository(monkeypatch) -> None:
    FakeUsersRepository.refresh_rows = {}
    FakeUsersRepository.created_refresh_tokens = []
    FakeUsersRepository.revoked_families = []
    FakeUsersRepository.used_hashes = []
    FakeUsersRepository.marked_logins = []

    from app.services import auth

    monkeypatch.setattr(auth, "UsersRepository", FakeUsersRepository)


def settings() -> Settings:
    return Settings(
        database_url="postgresql+asyncpg://postgres:ci@localhost:5432/ci",
        redis_url="redis://localhost:6379/0",
        jwt_access_ttl_seconds=900,
        jwt_refresh_ttl_seconds=3600,
    )


@pytest.mark.asyncio
async def test_register_hashes_password_and_commits() -> None:
    session = FakeSession()
    service = AuthService(session, settings())

    user_id = await service.register("ada@example.com", "secret", "Ada", "pt-BR")

    assert user_id == FakeUsersRepository.user_id
    assert session.commits == 1


@pytest.mark.asyncio
async def test_login_issues_access_and_refresh_tokens() -> None:
    session = FakeSession()
    service = AuthService(session, settings())

    result = await service.login("ada@example.com", "secret")

    assert result is not None
    user, access, refresh = result
    assert user["email"] == "ada@example.com"
    assert access.count(".") == 2
    assert refresh
    assert FakeUsersRepository.marked_logins == [FakeUsersRepository.user_id]
    assert FakeUsersRepository.created_refresh_tokens
    assert session.commits == 1


@pytest.mark.asyncio
async def test_login_rejects_unknown_user_or_wrong_password() -> None:
    service = AuthService(FakeSession(), settings())

    assert await service.login("missing@example.com", "secret") is None
    assert await service.login("ada@example.com", "wrong") is None


@pytest.mark.asyncio
async def test_refresh_rotates_valid_token() -> None:
    refresh_token = "refresh-token"
    FakeUsersRepository.refresh_rows[token_hash(refresh_token)] = {
        "id": FakeUsersRepository.refresh_id,
        "user_id": FakeUsersRepository.user_id,
        "family_id": FakeUsersRepository.family_id,
        "expires_at": datetime.now(UTC) + timedelta(minutes=5),
        "revoked_at": None,
    }
    session = FakeSession()
    service = AuthService(session, settings())

    result = await service.refresh(refresh_token)

    assert result is not None
    access, new_refresh = result
    assert access.count(".") == 2
    assert new_refresh != refresh_token
    assert FakeUsersRepository.used_hashes == [token_hash(refresh_token)]
    assert (
        FakeUsersRepository.created_refresh_tokens[-1]["parent_id"]
        == FakeUsersRepository.refresh_id
    )
    assert session.commits == 1


@pytest.mark.asyncio
async def test_refresh_rejects_unknown_token_without_commit() -> None:
    session = FakeSession()
    service = AuthService(session, settings())

    assert await service.refresh("missing-token") is None
    assert session.commits == 0


@pytest.mark.asyncio
async def test_refresh_revokes_expired_family() -> None:
    refresh_token = "expired-token"
    FakeUsersRepository.refresh_rows[token_hash(refresh_token)] = {
        "id": FakeUsersRepository.refresh_id,
        "user_id": FakeUsersRepository.user_id,
        "family_id": FakeUsersRepository.family_id,
        "expires_at": datetime.now(UTC) - timedelta(minutes=5),
        "revoked_at": None,
    }
    session = FakeSession()
    service = AuthService(session, settings())

    assert await service.refresh(refresh_token) is None
    assert FakeUsersRepository.revoked_families == [FakeUsersRepository.family_id]
    assert session.commits == 1


@pytest.mark.asyncio
async def test_logout_marks_refresh_used_when_present() -> None:
    session = FakeSession()
    service = AuthService(session, settings())

    await service.logout("refresh-token")
    await service.logout(None)

    assert FakeUsersRepository.used_hashes == [token_hash("refresh-token")]
    assert session.commits == 1
