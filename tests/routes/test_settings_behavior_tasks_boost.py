"""Additional route tests to raise coverage toward the 70% project target."""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.db.models.child import Child
from app.db.models.child_task import ChildTask
from app.db.models.parent import Parent
from app.db.models.user import User
from app.routes import behavior_routes
from app.routes import settings as settings_routes
from app.routes import tasks as tasks_routes
from tests.conftest import build_client


@pytest.mark.endpoint
def test_settings_get_all_children(fake_db, parent_user):
    child = SimpleNamespace(
        id=2,
        name="Ali",
        age=7,
        gender="M",
        school=None,
        class_name=None,
        temperament=None,
        created_at=None,
    )

    def query_side_effect(model):
        m = MagicMock()
        if model is Child:
            m.filter.return_value.all.return_value = [child]
        elif model is User:
            m.filter.return_value.first.return_value = SimpleNamespace(username="kid1")
        return m

    fake_db.query.side_effect = query_side_effect
    client = build_client(settings_routes, fake_db, user=parent_user)
    r = client.get("/api/v1/settings/children")
    assert r.status_code == 200
    assert r.json()["total"] == 1


@pytest.mark.endpoint
def test_settings_get_child_not_found(fake_db, parent_user):
    fake_db.query.return_value.filter.return_value.first.return_value = None
    client = build_client(settings_routes, fake_db, user=parent_user)
    r = client.get("/api/v1/settings/children/99")
    assert r.status_code == 404


@pytest.mark.endpoint
def test_settings_update_parent_profile_existing(fake_db, parent_user):
    parent = SimpleNamespace(
        id=parent_user.id,
        phone="1",
        country="PK",
        city="Lahore",
        father_age=40,
        mother_age=35,
        married_since=2010,
        is_single_parent=False,
    )
    fake_db.query.return_value.filter.return_value.first.return_value = parent
    client = build_client(settings_routes, fake_db, user=parent_user)
    r = client.put("/api/v1/settings/parent/profile", json={"phone": "999"})
    assert r.status_code == 200
    assert "updated" in r.json()["message"].lower()


@pytest.mark.endpoint
def test_behavior_get_child_stats(monkeypatch, fake_db, parent_user):
    monkeypatch.setattr(
        behavior_routes,
        "get_child_behavior_stats",
        lambda db, child_id, days=None: {"child_id": child_id},
    )
    child = SimpleNamespace(id=2, parent_id=parent_user.id)
    fake_db.query.return_value.filter.return_value.first.return_value = child
    client = build_client(behavior_routes, fake_db, user=parent_user)
    r = client.get("/api/v1/behavior/stats/2")
    assert r.status_code == 200
    assert r.json()["child_id"] == 2


@pytest.mark.endpoint
def test_behavior_checkin_status_empty_children(fake_db, parent_user):
    fake_db.query.return_value.filter.return_value.all.return_value = []
    client = build_client(behavior_routes, fake_db, user=parent_user)
    r = client.get("/api/v1/behavior/check-in-status")
    assert r.status_code == 200
    assert r.json()["children"] == []


@pytest.mark.endpoint
def test_tasks_get_all_parent_tasks(monkeypatch, fake_db, parent_user):
    child = SimpleNamespace(id=2, name="Kid")
    task = SimpleNamespace(
        id=1,
        child_id=2,
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

    def query_side_effect(model):
        m = MagicMock()
        if model is Child:
            m.filter.return_value.all.return_value = [child]
        elif model is ChildTask:
            m.filter.return_value = m
            m.order_by.return_value = m
            m.limit.return_value.all.return_value = [task]
        return m

    fake_db.query.side_effect = query_side_effect
    client = build_client(tasks_routes, fake_db, user=parent_user)
    r = client.get("/api/v1/tasks/all")
    assert r.status_code == 200
    assert r.json()["total"] == 1


@pytest.mark.endpoint
def test_tasks_get_all_forbidden_child_filter(fake_db, parent_user):
    child = SimpleNamespace(id=2, name="Kid")
    fake_db.query.return_value.filter.return_value.all.return_value = [child]
    client = build_client(tasks_routes, fake_db, user=parent_user)
    r = client.get("/api/v1/tasks/all?child_id=99")
    assert r.status_code == 403
