from uuid import uuid4

import pytest

from app.core.config import Settings
from app.services.storage import ObjectStorage


@pytest.mark.asyncio
async def test_object_storage_generates_scoped_key_and_local_round_trip(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    settings = Settings(
        database_url="postgresql+asyncpg://postgres:ci@localhost:5432/ci",
        redis_url="redis://localhost:6379/0",
        s3_endpoint="http://localhost:9000",
        s3_bucket_hh="hh-fixtures",
    )
    storage = ObjectStorage(settings)
    user_id = uuid4()
    import_id = uuid4()

    presigned = storage.generate_presigned_put(user_id, import_id)

    assert presigned.upload_method == "PUT"
    assert presigned.storage_key == f"users/{user_id}/imports/{import_id}.txt"
    assert presigned.upload_url.startswith("http://localhost:9000/hh-fixtures/users/")
    assert "signature=" in presigned.upload_url

    await storage.put_object(presigned.storage_key, b"hand history")

    assert await storage.get_object(presigned.storage_key) == b"hand history"
