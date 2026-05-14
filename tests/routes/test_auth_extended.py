from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.routes import auth as auth_routes
from tests.conftest import build_client


@pytest.mark.endpoint
def test_google_login_missing_fields(fake_db):
    client = build_client(auth_routes, fake_db)
    r = client.post("/api/v1/auth/google-login", json={})
    assert r.status_code == 400


@pytest.mark.endpoint
def test_register_duplicate_email(fake_db, monkeypatch):
    existing = SimpleNamespace(id=1)
    fake_db.query.return_value.filter.return_value.first.return_value = existing
    client = build_client(auth_routes, fake_db)
    r = client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "secret12", "name": "N"},
    )
    assert r.status_code == 400


@pytest.mark.endpoint
def test_login_invalid_user(fake_db):
    fake_db.query.return_value.filter.return_value.first.return_value = None
    client = build_client(auth_routes, fake_db)
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "none@example.com", "password": "secret12"},
    )
    assert r.status_code == 401
