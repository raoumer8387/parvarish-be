from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.games.mood_picker import service as mood_svc
from app.games.scenario_game import service as scen_svc
from app.games.islamic_quiz import service as quiz_svc


@pytest.mark.unit
def test_analyze_mood_uses_db_scenario():
    scenario = SimpleNamespace(mood_weights={"Happy": 3})
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = scenario
    out = mood_svc.analyze_mood(db, scenario_id=1, selected_mood="Happy")
    assert "emotional_control" in out


@pytest.mark.unit
def test_analyze_mood_fallback_no_scenario():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    out = mood_svc.analyze_mood(db, scenario_id=99, selected_mood="Forgive")
    assert out["empathy"] >= 50


@pytest.mark.unit
def test_analyze_scenario_with_question_options():
    q = SimpleNamespace(
        options=[{"option": "A", "moral": 5, "emotional": 1, "social": 0}],
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = q
    out = scen_svc.analyze_scenario(db, 1, "A")
    assert "moral" in out


@pytest.mark.unit
def test_analyze_quiz_correct():
    q = SimpleNamespace(correct_answer="B")
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = q
    ok, analysis = quiz_svc.analyze_quiz(db, 1, "B")
    assert ok is True
    assert "spiritual" in analysis


@pytest.mark.unit
def test_analyze_quiz_missing_question():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    ok, analysis = quiz_svc.analyze_quiz(db, 99, "B")
    assert ok is False
