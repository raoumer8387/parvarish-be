import pytest

from app.games import game_config as gc


@pytest.mark.unit
def test_get_completion_message_tiers():
    assert "Outstanding" in gc.get_completion_message(90) or "🌟" in gc.get_completion_message(90)
    assert gc.get_completion_message(70, language="ur")  # branch
    assert gc.get_completion_message(50)
    assert gc.get_completion_message(20)


@pytest.mark.unit
def test_calculate_game_score_all_types():
    mem = gc.calculate_game_score(
        "memory",
        {"correct_matches": 5, "total_flips": 12, "time_taken_seconds": 60},
    )
    assert "percentage" in mem

    mood = gc.calculate_game_score(
        "mood",
        {"responses": [{"selected_mood": "Forgive"} for _ in range(3)]},
    )
    assert mood["percentage"] >= 0

    scen = gc.calculate_game_score(
        "scenario",
        {"responses": [{"score": 15}, {"score": 10}]},
    )
    assert scen["max_score"] > 0

    quiz = gc.calculate_game_score(
        "islamic_quiz",
        {
            "responses": [
                {"is_correct": True, "time_taken": 10},
                {"is_correct": False, "time_taken": 40},
            ]
        },
    )
    assert quiz["breakdown"]["correct_answers"] == 1


@pytest.mark.unit
def test_calculate_game_score_unknown_type():
    with pytest.raises(ValueError):
        gc.calculate_game_score("unknown", {})


@pytest.mark.unit
def test_validate_game_completion_memory_and_mood():
    ok = gc.validate_game_completion(
        "memory",
        {"total_flips": 1, "correct_matches": 1, "wrong_matches": 0, "time_taken_seconds": 5},
    )
    assert ok["valid"] is True

    bad = gc.validate_game_completion("memory", {})
    assert bad["valid"] is False

    mood = gc.validate_game_completion("mood", {"responses": [{}] * 5})
    assert mood["valid"] is True
