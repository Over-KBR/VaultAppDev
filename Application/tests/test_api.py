"""API contract tests use Flask's in-process test client (no listening port)."""

import pytest

from src.api import VaultAPI
from src.database import add_account


@pytest.fixture
def api_client(tmp_db, encryption_key):
    add_account(
        "Example", "demo@example.invalid", "DummyPassword42!",
        "https://example.invalid/login", "Dummy note", None, encryption_key,
        totp_secret="GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
    )
    add_account(
        "Suffix lookalike", "other@example.invalid", "OtherPassword42!",
        "https://notexample.invalid/login", "", None, encryption_key,
    )
    api = VaultAPI()
    if api._app is None:
        pytest.skip("Flask is not installed")
    client = api._app.test_client()
    yield api, client, encryption_key
    api.clear_key()


def test_status_indicates_locked_and_unlocked(api_client):
    api, client, key = api_client

    assert client.get("/status").json["unlocked"] is False
    api.set_key(key)
    assert client.get("/status").json["unlocked"] is True


def test_accounts_returns_metadata_without_password(api_client, monkeypatch):
    api, client, key = api_client
    api.set_key(key)
    monkeypatch.setattr(
        "src.database.get_all_accounts",
        lambda *_args, **_kwargs: pytest.fail(
            "/accounts ne doit pas déchiffrer le coffre"
        ),
    )

    response = client.get("/accounts?url=https://example.invalid/login")
    assert response.status_code == 200
    account = response.json["accounts"][0]
    assert account["name"] == "Example"
    assert account["login"] == "demo@example.invalid"
    assert "password" not in account
    assert "totp_secret" not in account
    assert [item["name"] for item in response.json["accounts"]] == ["Example"]


def test_fill_requires_unlock_and_returns_selected_credentials(
    api_client, monkeypatch
):
    api, client, key = api_client
    assert client.post("/fill", json={"account_id": 1}).status_code == 403

    api.set_key(key)
    monkeypatch.setattr(
        "src.database.get_all_accounts",
        lambda *_args, **_kwargs: pytest.fail(
            "/fill ne doit pas déchiffrer les autres comptes"
        ),
    )
    response = client.post("/fill", json={"account_id": 1})
    assert response.status_code == 200
    assert response.json == {
        "login": "demo@example.invalid",
        "password": "DummyPassword42!",
    }
    assert "totp_secret" not in response.json


@pytest.mark.parametrize("payload", [{}, {"account_id": "1"}, {"account_id": True}])
def test_fill_rejects_invalid_account_id(api_client, payload):
    api, client, key = api_client
    api.set_key(key)

    assert client.post("/fill", json=payload).status_code == 400


def test_fill_returns_not_found_for_unknown_account(api_client):
    api, client, key = api_client
    api.set_key(key)

    assert client.post("/fill", json={"account_id": 999}).status_code == 404
