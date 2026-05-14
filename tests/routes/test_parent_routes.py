from types import SimpleNamespace

import pytest

from app.routes import parent_routes
from tests.conftest import build_client


@pytest.mark.endpoint
def test_list_parent_children_success(fake_db, parent_user):
    child = SimpleNamespace(
        id=2,
        name="Ali",
        age=8,
        gender="M",
        school="ABC",
        class_name="3",
        temperament="calm",
        created_at=None,
    )
    fake_db.query.return_value.filter.return_value.all.return_value = [child]
    client = build_client(parent_routes, fake_db, user=parent_user)
    response = client.get("/api/v1/parent/children")
    assert response.status_code == 200
    assert response.json()["total"] == 1
