from datetime import datetime
from types import SimpleNamespace

import pytest

from app.routes import tasks as task_routes
from tests.conftest import build_client


@pytest.mark.endpoint
def test_create_tasks_from_chat_success(fake_db, parent_user, monkeypatch):
    child = SimpleNamespace(id=2, parent_id=parent_user.id, name="Ali")
    fake_db.query.return_value.filter.return_value.first.return_value = child

    task = SimpleNamespace(
        id=1,
        child_id=2,
        title="Practice patience",
        description="Breathing before reacting",
        category="emotional",
        xp_reward=10,
        difficulty=1,
        status="pending",
        source="chatbot",
        meta={},
        created_at=datetime.utcnow(),
    )
    monkeypatch.setattr(
        task_routes,
        "generate_tasks_from_chat",
        lambda **_: {
            "count": 1,
            "tasks": [task],
            "categories_considered": ["emotional"],
            "categories_low_score": ["emotional"],
            "keywords_detected": ["anger"],
        },
    )
    client = build_client(task_routes, fake_db, user=parent_user)

    response = client.post(
        "/api/v1/tasks/from-chat",
        json={"child_id": 2, "chatbot_response": "child has anger issues"},
    )
    assert response.status_code == 201
    assert response.json()["count"] == 1


@pytest.mark.endpoint
def test_get_child_tasks_forbidden_for_child_user(fake_db, child_user):
    client = build_client(task_routes, fake_db, user=child_user)
    response = client.get("/api/v1/tasks/child/2")
    assert response.status_code == 403
