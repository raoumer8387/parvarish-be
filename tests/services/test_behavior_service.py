from types import SimpleNamespace

import pytest

from app.services import behavior_service


@pytest.mark.unit
def test_calculate_score_variants():
    assert behavior_service.calculate_score("Yes", 4) == 4
    assert behavior_service.calculate_score("No", 4) == 0
    assert behavior_service.calculate_score("Sometimes", 4) == 2
    assert behavior_service.calculate_score("Unknown", 4) == 0


@pytest.mark.unit
def test_get_child_questions_returns_empty_when_child_missing():
    db = SimpleNamespace()
    query = SimpleNamespace()
    query.filter = lambda *_args, **_kwargs: SimpleNamespace(first=lambda: None)
    db.query = lambda *_args, **_kwargs: query

    result = behavior_service.get_child_questions(db, child_id=99, total_questions=5)
    assert result == []
