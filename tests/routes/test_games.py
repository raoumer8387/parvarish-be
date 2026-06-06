import pytest

from app.routes import games
from tests.conftest import build_client


@pytest.mark.unit
def test_get_age_group_from_age():
    assert games.get_age_group_from_age(None) == "6-8"
    assert games.get_age_group_from_age(7) == "6-8"
    assert games.get_age_group_from_age(10) == "9-11"
    assert games.get_age_group_from_age(13) == "12-14"
    assert games.get_age_group_from_age(99) == "12-14"


@pytest.mark.endpoint
def test_submit_memory_game_forbidden_for_child_user(fake_db, child_user):
    client = build_client(games, fake_db, user=child_user)
    response = client.post(
        "/api/v1/games/memory/submit",
        json={
            "child_id": 2,
            "total_flips": 10,
            "correct_matches": 4,
            "wrong_matches": 6,
            "time_taken_seconds": 20,
        },
    )
    assert response.status_code == 403
