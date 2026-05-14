from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.routes import settings as settings_routes
from tests.conftest import build_client


@pytest.mark.endpoint
def test_get_parent_profile_success(fake_db, parent_user):
    profile = SimpleNamespace(
        id=parent_user.id,
        phone="123",
        country="PK",
        city="LHR",
        father_age=40,
        mother_age=35,
        married_since=2010,
        is_single_parent=False,
    )
    fake_db.query.return_value.filter.return_value.first.return_value = profile
    client = build_client(settings_routes, fake_db, user=parent_user)

    response = client.get("/api/v1/settings/parent/profile")
    assert response.status_code == 200
    assert response.json()["has_profile"] is True


@pytest.mark.endpoint
def test_add_child_missing_required_fields(fake_db, parent_user):
    client = build_client(settings_routes, fake_db, user=parent_user)
    response = client.post("/api/v1/settings/children", json={"username": "kid"})
    assert response.status_code == 400
