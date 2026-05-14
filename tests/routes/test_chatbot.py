from types import SimpleNamespace

import pytest

from app.routes import chatbot
from tests.conftest import build_client


@pytest.mark.endpoint
def test_chat_success_with_mocked_generator(fake_db, parent_user, monkeypatch):
    mocked = chatbot.ChatResponse(response="ok", user_id="u1", recommended_videos=[])
    monkeypatch.setattr(chatbot, "_generate_chat_response", lambda **_kwargs: mocked)
    client = build_client(chatbot, fake_db, user=parent_user)

    response = client.post("/api/v1/chat", json={"message": "Assalam o Alaikum", "user_id": "u1"})
    assert response.status_code == 200
    assert response.json()["response"] == "ok"


@pytest.mark.endpoint
def test_chat_history_child_not_found(fake_db, parent_user):
    fake_db.query.return_value.filter.return_value.first.return_value = None
    client = build_client(chatbot, fake_db, user=parent_user)
    response = client.get("/api/v1/chat/history?child_id=99")
    assert response.status_code == 404
