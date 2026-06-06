import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.routes import games as games_routes
from tests.conftest import build_client


@pytest.mark.endpoint
def test_memory_submit_success(fake_db, child_user, monkeypatch):
    res = SimpleNamespace(id=uuid.uuid4(), analysis_score={"cognitive": 80})
    child_profile = SimpleNamespace(id=child_user.id, name="Child User", parent_id=10)
    monkeypatch.setattr(games_routes, "save_memory_game_result", lambda *a, **k: res)
    monkeypatch.setattr(games_routes, "generate_tasks_from_scores", lambda *a, **k: {"count": 0})
    monkeypatch.setattr(games_routes, "notify_parent_child_game_completed", lambda *a, **k: None)
    monkeypatch.setattr(
        games_routes,
        "refresh_and_notify_dashboard",
        lambda *a, **k: {"overall_score": 72, "upgraded_categories": [], "downgraded_categories": []},
    )
    q = MagicMock()
    q.filter.return_value.first.return_value = child_profile
    fake_db.query.return_value = q
    client = build_client(games_routes, fake_db, user=child_user)
    r = client.post(
        "/api/v1/games/memory/submit",
        json={
            "child_id": child_user.id,
            "total_flips": 10,
            "correct_matches": 4,
            "wrong_matches": 6,
            "time_taken_seconds": 30,
        },
    )
    assert r.status_code == 200
    assert "result_id" in r.json()


@pytest.mark.endpoint
def test_complete_mood_session_success(fake_db, child_user, monkeypatch):
    child_profile = SimpleNamespace(id=child_user.id, name="Child User", parent_id=10)
    monkeypatch.setattr(
        games_routes,
        "save_mood_result",
        lambda *a, **k: SimpleNamespace(analysis_score={"emotional": 70}),
    )
    monkeypatch.setattr(games_routes, "generate_tasks_from_scores", lambda *a, **k: {"count": 0})
    monkeypatch.setattr(games_routes, "notify_parent_child_game_completed", lambda *a, **k: None)
    monkeypatch.setattr(
        games_routes,
        "refresh_and_notify_dashboard",
        lambda *a, **k: {"overall_score": 72, "upgraded_categories": [], "downgraded_categories": []},
    )
    q = MagicMock()
    q.filter.return_value.first.return_value = child_profile
    fake_db.query.return_value = q
    payload = {
        "child_id": child_user.id,
        "total_time_seconds": 120,
        "responses": [
            {"scenario_id": i, "selected_mood": "Forgive", "time_taken": 20} for i in range(1, 6)
        ],
    }
    client = build_client(games_routes, fake_db, user=child_user)
    r = client.post("/api/v1/games/session/mood/complete", json=payload)
    assert r.status_code == 200
    assert r.json().get("success") is True
