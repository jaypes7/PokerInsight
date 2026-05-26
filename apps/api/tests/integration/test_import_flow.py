import hashlib
from pathlib import Path
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app

FIXTURE = Path(__file__).resolve().parents[4] / "packages" / "hh-fixtures" / "heads_up.txt"


@pytest.mark.integration
async def test_register_login_import_and_list_hands() -> None:
    app = create_app()
    raw = FIXTURE.read_text(encoding="utf-8")
    email = f"flow-{uuid4().hex}@example.com"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        register = await client.post(
            "/v1/auth/register",
            json={
                "email": email,
                "password": "MinhaSenha12",
                "display_name": "Hero",
                "locale": "pt-BR",
                "accept_terms": True,
            },
        )
        assert register.status_code == 201

        login = await client.post(
            "/v1/auth/login",
            json={"email": email, "password": "MinhaSenha12"},
        )
        assert login.status_code == 200

        create_import = await client.post(
            "/v1/imports",
            json={
                "filename": "heads_up.txt",
                "size_bytes": len(raw.encode("utf-8")),
                "sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
            },
        )
        assert create_import.status_code == 201
        import_id = create_import.json()["import_id"]

        complete = await client.post(f"/v1/imports/{import_id}/complete", json={"raw_text": raw})
        assert complete.status_code == 202
        assert complete.json()["summary"]["imported"] == 1

        hands = await client.get("/v1/hands")
        assert hands.status_code == 200
        assert hands.json()["data"][0]["site_hand_id"] == "260820828718"
