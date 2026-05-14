from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services import task_service


@pytest.mark.unit
def test_mark_task_completed_updates(monkeypatch):
    task = SimpleNamespace(
        id=1,
        status="pending",
        meta={},
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = task

    out = task_service.mark_task_completed(db, 1)
    assert out is task
    assert task.status == "completed"
    assert "completed_at" in task.meta


@pytest.mark.unit
def test_update_task_status_incomplete_clears_completed_at():
    task = SimpleNamespace(
        id=2,
        status="completed",
        meta={"completed_at": "old"},
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = task

    out = task_service.update_task_status(db, 2, "incomplete")
    assert out is task
    assert task.status == "incomplete"
    assert "completed_at" not in task.meta


@pytest.mark.unit
def test_list_child_tasks_returns_dicts():
    task = SimpleNamespace(
        id=1,
        child_id=3,
        title="t",
        description="d",
        category="emotional",
        xp_reward=10,
        difficulty=1,
        status="pending",
        source="chatbot",
        meta={},
        created_at=datetime.utcnow(),
    )
    m = MagicMock()
    m.join.return_value = m
    m.filter.return_value = m
    m.order_by.return_value = m
    lim = MagicMock()
    lim.all.return_value = [(task, "ChildName")]
    m.limit.return_value = lim
    db = MagicMock()
    db.query.return_value = m

    rows = task_service.list_child_tasks(db, child_id=3, status="pending", limit=10)
    assert len(rows) == 1
    assert rows[0]["child_name"] == "ChildName"


@pytest.mark.unit
def test_generate_tasks_from_scores_no_low_categories(monkeypatch):
    db = MagicMock()
    monkeypatch.setattr(task_service, "_get_low_score_categories", lambda *a, **k: [])
    out = task_service.generate_tasks_from_scores(db, child_id=1, days=3)
    assert out["count"] == 0
