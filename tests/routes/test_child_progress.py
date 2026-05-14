import pytest

from app.routes import child_progress
from tests.conftest import build_client


@pytest.mark.endpoint
def test_child_progress_dashboard_forbidden_for_child_user(fake_db, child_user):
    client = build_client(child_progress, fake_db, user=child_user)
    response = client.get("/api/v1/child-progress/2/dashboard")
    assert response.status_code == 403
