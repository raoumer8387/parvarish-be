import pytest

from app.routes import lacking_routes
from tests.conftest import build_client


@pytest.mark.endpoint
def test_analyze_all_children_forbidden_for_child_user(fake_db, child_user):
    client = build_client(lacking_routes, fake_db, user=child_user)
    response = client.get("/api/v1/parent/lacking/analyze/all")
    assert response.status_code == 403
