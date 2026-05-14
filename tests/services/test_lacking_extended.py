from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services import lacking_analyzer


@pytest.mark.unit
def test_get_child_lacking_analysis_raises_when_child_missing():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(ValueError, match="not found"):
        lacking_analyzer.get_child_lacking_analysis(db, child_id=999)


@pytest.mark.unit
def test_analyze_presence_of_mind_from_scores():
    r = SimpleNamespace(raw_result={"score": 40})
    out = lacking_analyzer.analyze_presence_of_mind([r])
    assert out["score"] == 40.0
    assert out["status"] == "lacking"


@pytest.mark.unit
def test_analyze_mood_identification_accuracy():
    r = SimpleNamespace(raw_result={"is_correct": True})
    r2 = SimpleNamespace(raw_result={"is_correct": False})
    out = lacking_analyzer.analyze_mood_identification([r, r2])
    assert out["score"] == 50.0


@pytest.mark.unit
def test_analyze_learning_capability_full_accuracy():
    rows = [SimpleNamespace(raw_result={"is_correct": True}) for _ in range(3)]
    out = lacking_analyzer.analyze_learning_capability(rows)
    assert out["score"] == 100.0
    assert out["status"] == "good"


@pytest.mark.unit
def test_analyze_behavior_identification_from_choice_quality():
    r = SimpleNamespace(raw_result={"choice_quality": 80})
    out = lacking_analyzer.analyze_behavior_identification([r])
    assert out["score"] == 80.0


@pytest.mark.unit
def test_get_task_completion_adjustment_filters_by_meta():
    db = MagicMock()
    t1 = SimpleNamespace(
        id=1,
        status="completed",
        meta={"lacking_area": "presence_of_mind"},
    )
    t2 = SimpleNamespace(id=2, status="pending", meta={"lacking_area": "other"})
    db.query.return_value.filter.return_value.all.return_value = [t1, t2]

    adj = lacking_analyzer.get_task_completion_adjustment(db, child_id=1, lacking_area="presence_of_mind")
    assert isinstance(adj, (int, float))
    assert adj == 10
