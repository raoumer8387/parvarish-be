from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.routes import auth as auth_routes
from tests.conftest import build_client


@pytest.mark.endpoint
def test_register_user_success(fake_db, monkeypatch):
    query = MagicMock()
    query.filter.return_value.first.return_value = None
    fake_db.query.return_value = query

    monkeypatch.setattr(auth_routes, "get_password_hash", lambda _: "hashed")
    monkeypatch.setattr(auth_routes, "create_access_token", lambda data: "token-123")

    def _refresh(user):
        user.id = 11

    fake_db.refresh.side_effect = _refresh
    client = build_client(auth_routes, fake_db)

    response = client.post(
        "/api/v1/auth/register",
        json={"email": "new@example.com", "password": "secret12", "name": "New User"},
    )

    assert response.status_code == 201
    assert response.json()["access_token"] == "token-123"


@pytest.mark.endpoint
def test_login_requires_identifier(fake_db):
    client = build_client(auth_routes, fake_db)
    response = client.post("/api/v1/auth/login", json={"password": "secret12"})
    assert response.status_code == 400


@pytest.mark.endpoint
def test_validate_token_success(fake_db, parent_user):
    client = build_client(auth_routes, fake_db, user=parent_user)
    response = client.get("/api/v1/auth/validate")
    assert response.status_code == 200
    payload = response.json()
    assert payload["valid"] is True
    assert payload["user_id"] == parent_user.id
