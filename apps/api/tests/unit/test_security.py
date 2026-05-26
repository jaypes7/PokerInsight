from datetime import datetime, timedelta, tzinfo
from uuid import uuid4

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    hash_password,
    token_hash,
    verify_access_token,
    verify_password,
)


def test_password_hash_round_trip_and_rejects_invalid_values() -> None:
    encoded = hash_password("correct horse battery staple")

    assert verify_password("correct horse battery staple", encoded)
    assert not verify_password("wrong", encoded)
    assert not verify_password("secret", "not-a-valid-hash")
    assert not verify_password("secret", "argon2$1$payload")


def test_access_token_round_trip_and_tamper_detection() -> None:
    settings = Settings(
        database_url="postgresql+asyncpg://postgres:ci@localhost:5432/ci",
        redis_url="redis://localhost:6379/0",
        git_sha="test-secret",
    )
    user_id = uuid4()

    token = create_access_token(user_id, settings)
    header, payload, signature = token.split(".")

    assert verify_access_token(token, settings) == user_id
    assert verify_access_token(f"{header}.{payload}.{signature}x", settings) is None
    assert verify_access_token("not-a-jwt", settings) is None


def test_access_token_rejects_expired_payload() -> None:
    settings = Settings(
        database_url="postgresql+asyncpg://postgres:ci@localhost:5432/ci",
        redis_url="redis://localhost:6379/0",
        jwt_access_ttl_seconds=60,
    )
    original_now = datetime.now
    token = create_access_token(uuid4(), settings)

    class FutureDateTime(datetime):
        @classmethod
        def now(cls, tz: tzinfo | None = None) -> datetime:
            return original_now(tz) + timedelta(minutes=5)

    from app.core import security

    security.datetime = FutureDateTime
    try:
        assert verify_access_token(token, settings) is None
    finally:
        security.datetime = datetime


def test_token_hash_is_stable_sha256() -> None:
    assert token_hash("refresh") == token_hash("refresh")
    assert token_hash("refresh") != token_hash("other")
