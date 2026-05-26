import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode
from uuid import UUID

from app.core.config import Settings


@dataclass(frozen=True)
class PresignedPut:
    upload_url: str
    upload_method: str
    expires_at: datetime
    storage_key: str


class ObjectStorage:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.local_root = Path(".storage") / settings.s3_bucket_hh

    def import_key(self, user_id: UUID, import_id: UUID) -> str:
        return f"users/{user_id}/imports/{import_id}.txt"

    def generate_presigned_put(self, user_id: UUID, import_id: UUID) -> PresignedPut:
        expires_at = datetime.now(UTC) + timedelta(minutes=15)
        key = self.import_key(user_id, import_id)
        signature = hashlib.sha256(f"{key}:{expires_at.timestamp()}".encode()).hexdigest()
        query = urlencode({"expires": int(expires_at.timestamp()), "signature": signature})
        endpoint = str(self.settings.s3_endpoint).rstrip("/")
        return PresignedPut(
            f"{endpoint}/{self.settings.s3_bucket_hh}/{key}?{query}", "PUT", expires_at, key
        )

    async def put_object(self, key: str, content: bytes) -> None:
        path = self.local_root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    async def get_object(self, key: str) -> bytes:
        return (self.local_root / key).read_bytes()
