from types import SimpleNamespace

import pytest

from app.routes import behavior_routes
from tests.conftest import build_client


@pytest.mark.endpoint
def test_personalized_questions_success(fake_db, parent_user, monkeypatch):
    fake_db.query.return_value.filter.return_value.first.return_value = SimpleNamespace(id=parent_user.id)
    monkeypatch.setattr(behavior_routes, "get_personalized_questions", lambda *_args, **_kwargs: [])

    client = build_client(behavior_routes, fake_db, user=parent_user)
    response = client.get("/api/v1/behavior/questions/personalized")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.endpoint
def test_submit_responses_requires_payload(fake_db, parent_user):
    client = build_client(behavior_routes, fake_db, user=parent_user)
    response = client.post("/api/v1/behavior/submit-responses", json={"child_id": 2, "responses": []})
    assert response.status_code == 400
