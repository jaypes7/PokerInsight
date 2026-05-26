import base64
import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from app.core.config import Settings


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 390_000)
    return "pbkdf2_sha256$390000$" + base64.urlsafe_b64encode(salt + digest).decode()


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, payload = encoded.split("$", 2)
        if algorithm != "pbkdf2_sha256":
            return False
        raw = base64.urlsafe_b64decode(payload.encode())
        salt = raw[:16]
        expected = raw[16:]
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iterations))
        return hmac.compare_digest(digest, expected)
    except (ValueError, TypeError):
        return False


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def create_access_token(user_id: UUID, settings: Settings) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=settings.jwt_access_ttl_seconds)).timestamp()),
    }
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = ".".join(
        [_b64_json(header), _b64_json(payload)],
    )
    signature = hmac.new(_jwt_secret(settings), signing_input.encode(), hashlib.sha256).digest()
    return signing_input + "." + _b64(signature)


def verify_access_token(token: str, settings: Settings) -> UUID | None:
    try:
        header, payload, signature = token.split(".")
        signing_input = f"{header}.{payload}"
        expected = hmac.new(_jwt_secret(settings), signing_input.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(_b64(expected), signature):
            return None
        data = json.loads(base64.urlsafe_b64decode(_pad(payload)).decode())
        if int(data["exp"]) < int(datetime.now(UTC).timestamp()):
            return None
        return UUID(str(data["sub"]))
    except (KeyError, ValueError, json.JSONDecodeError):
        return None


def _jwt_secret(settings: Settings) -> bytes:
    return f"{settings.app_name}:{settings.git_sha}".encode()


def _b64_json(value: dict[str, Any]) -> str:
    return _b64(json.dumps(value, separators=(",", ":"), sort_keys=True).encode())


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _pad(value: str) -> bytes:
    return (value + "=" * (-len(value) % 4)).encode()
