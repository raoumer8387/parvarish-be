from types import SimpleNamespace

import pytest

from app.routes import activity_history
from tests.conftest import build_client


@pytest.mark.endpoint
def test_activity_summary_success_with_empty_data(fake_db, parent_user, monkeypatch):
    fake_db.query.return_value.filter.return_value.all.return_value = []
    fake_db.query.return_value.filter.return_value.scalar.return_value = 0
    monkeypatch.setattr(
        activity_history,
        "_verify_child_access",
        lambda _db, _user, child_id: SimpleNamespace(id=child_id, name="Ali"),
    )

    client = build_client(activity_history, fake_db, user=parent_user)
    response = client.get("/api/v1/activity-history/2/summary")
    assert response.status_code == 200
    assert response.json()["total_games_played"] == 0
