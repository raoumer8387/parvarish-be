from unittest.mock import MagicMock

import pytest

from app.games.memory_game import service as mem_svc


@pytest.mark.unit
def test_analyze_memory_game():
    out = mem_svc.analyze_memory_game(total_flips=10, correct_matches=4, wrong_matches=6, time_taken_seconds=20)
    assert "cognitive" in out and "focus" in out


@pytest.mark.unit
def test_save_memory_game_result():
    db = MagicMock()
    res = mem_svc.save_memory_game_result(db, child_id=1, total_flips=4, correct_matches=2, wrong_matches=2, time_taken_seconds=10)
    db.add.assert_called_once()
    db.commit.assert_called_once()
    assert res.game_type == "memory"
