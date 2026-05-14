from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.db.models.behavior_models import Question
from app.db.models.child import Child
from app.schemas.behavior_schemas import BehaviorResponseItem
from app.services import behavior_service


@pytest.mark.unit
def test_get_child_behavior_stats_empty():
    db = MagicMock()
    chain = MagicMock()
    chain.join.return_value = chain
    chain.filter.return_value = chain
    chain.all.return_value = []
    db.query.return_value = chain

    stats = behavior_service.get_child_behavior_stats(db, child_id=1, days=None)
    assert stats["total_responses"] == 0
    assert stats["behavior_level"] == 0.0


@pytest.mark.unit
def test_get_child_behavior_stats_with_rows():
    ts = datetime(2024, 1, 1)
    resp = SimpleNamespace(score=10, timestamp=ts)
    question = SimpleNamespace(category="emotional", weight=2)
    db = MagicMock()
    chain = MagicMock()
    chain.join.return_value = chain
    chain.filter.return_value = chain
    chain.all.return_value = [(resp, question)]
    db.query.return_value = chain

    stats = behavior_service.get_child_behavior_stats(db, child_id=1, days=None)
    assert stats["total_responses"] == 1
    assert stats["behavior_level"] > 0


@pytest.mark.unit
def test_save_behavior_responses_persists_one():
    q = SimpleNamespace(
        id=1,
        question_text_template="How is {child_name}?",
        options=["Yes"],
        weight=2,
        category="emotional",
    )
    child = SimpleNamespace(id=2, name="Ali")

    def query_side_effect(model):
        m = MagicMock()
        if model is Question:
            m.filter.return_value.first.return_value = q
        elif model is Child:
            m.filter.return_value.first.return_value = child
        return m

    db = MagicMock()
    db.query.side_effect = query_side_effect

    items = [BehaviorResponseItem(child_id=2, question_id=1, answer="Yes")]
    count = behavior_service.save_behavior_responses(db, items)
    assert count == 1


@pytest.mark.unit
def test_get_personalized_questions_for_parent():
    db = MagicMock()
    child = SimpleNamespace(id=1, name="Ali")
    question = SimpleNamespace(
        id=10,
        question_text_template="Hi {child_name}",
        options=["Yes"],
        category="emotional",
    )

    def query_side_effect(model):
        m = MagicMock()
        if model is Child:
            m.filter.return_value.all.return_value = [child]
        elif model is Question:
            m.order_by.return_value.limit.return_value.all.return_value = [question]
        return m

    db.query.side_effect = query_side_effect
    out = behavior_service.get_personalized_questions(db, parent_id=1, total_questions=1)
    assert len(out) == 1
    assert "Ali" in out[0].question_text


@pytest.mark.unit
def test_submit_child_responses_no_child():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    out = behavior_service.submit_child_responses(db, 9, [{"question_id": 1, "answer": "Yes"}])
    assert out == {"total_score": 0, "total_questions": 0}
