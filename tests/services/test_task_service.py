from unittest.mock import MagicMock

import pytest

from app.services import task_service


@pytest.mark.unit
def test_extract_categories_from_text_detects_keywords():
    categories, keywords = task_service._extract_categories_from_text("Child gets angry and needs focus")
    assert "emotional" in categories
    assert "cognitive" in categories
    assert "angry" in keywords


@pytest.mark.unit
def test_generate_tasks_from_chat_returns_empty_when_no_candidates(monkeypatch):
    fake_db = MagicMock()
    monkeypatch.setattr(task_service, "_get_low_score_categories", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(task_service, "_recent_task_categories", lambda *_args, **_kwargs: set())

    result = task_service.generate_tasks_from_chat(
        db=fake_db,
        child_id=5,
        chatbot_response="No mapped keywords here",
        chatbot_tags=[],
    )

    assert result["count"] == 0
    assert result["tasks"] == []
