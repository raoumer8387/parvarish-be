from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.db.crud import message as msg_crud


@pytest.mark.unit
def test_create_message_persists():
    db = MagicMock()
    msg_crud.create_message(db, user_id=1, role="user", content="hi", child_id=None)
    db.add.assert_called_once()
    db.commit.assert_called_once()


@pytest.mark.unit
def test_list_messages_for_user_with_limit():
    msgs = [SimpleNamespace(created_at=i) for i in range(10)]
    q = MagicMock()
    q.filter.return_value = q
    q.order_by.return_value = q
    q.all.return_value = msgs
    db = MagicMock()
    db.query.return_value = q

    out = msg_crud.list_messages_for_user(db, user_id=1, child_id=None, limit=3)
    assert len(out) == 3


@pytest.mark.unit
def test_list_recent_messages():
    msgs = [SimpleNamespace(created_at=1)]
    q = MagicMock()
    q.filter.return_value = q
    q.order_by.return_value = q
    q.all.return_value = msgs
    db = MagicMock()
    db.query.return_value = q
    out = msg_crud.list_recent_messages(db, user_id=1, limit=5)
    assert isinstance(out, list)
