from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


def test_healthz_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version_returns_version_and_sha() -> None:
    client = TestClient(app)

    response = client.get("/version")

    assert response.status_code == 200
    assert response.json()["version"]
    assert "sha" in response.json()


def test_production_disables_openapi_docs(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    get_settings.cache_clear()

    from app.main import create_app

    production_app = create_app()

    assert production_app.docs_url is None
    assert production_app.redoc_url is None

    monkeypatch.setenv("APP_ENV", "ci")
    get_settings.cache_clear()
