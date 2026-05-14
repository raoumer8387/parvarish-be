import pytest

from app.routes import google_auth
from tests.conftest import build_client


@pytest.mark.endpoint
def test_google_auth_status(fake_db):
    client = build_client(google_auth, fake_db)
    response = client.get("/api/v1/auth/google/status")
    assert response.status_code == 200
    assert "google_oauth_enabled" in response.json()


@pytest.mark.endpoint
def test_google_redirect_uri(fake_db):
    client = build_client(google_auth, fake_db)
    response = client.get("/api/v1/auth/google/redirect-uri")
    assert response.status_code == 200
    assert "effective_redirect_uri" in response.json()
