"""Tests for unified behavior analysis service."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.services import unified_behavior as ub


def test_merge_category_scores_weighted_average():
    checkin = {"emotional": 80.0, "cognitive": 40.0}
    games = {"emotional": 60.0, "cognitive": 70.0}
    tasks = {"emotional": 100.0}
    merged = ub._merge_category_scores(checkin, games, tasks)
    assert merged["emotional"] == round((80 * 0.35 + 60 * 0.35 + 100 * 0.30) / 1.0, 1)
    assert merged["cognitive"] == round((40 * 0.35 + 70 * 0.35) / 0.7, 1)


def test_detect_changes_upgrade_downgrade_stable():
    current = {"emotional": 75.0, "social": 40.0, "moral": 60.0}
    previous = {"emotional": 65.0, "social": 55.0}
    changes = ub._detect_changes(current, previous)
    assert changes["emotional"] == "upgraded"
    assert changes["social"] == "downgraded"
    assert changes["moral"] == "new"


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("behavioral", "habitual"),
        ("religious", "moral"),
        ("emotional", "emotional"),
    ],
)
def test_normalize_checkin_category(raw, expected):
    assert ub._normalize_checkin_category(raw) == expected


def test_refresh_and_notify_dashboard_no_child():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    assert ub.refresh_and_notify_dashboard(db, 99, "game") == {}


@patch("app.services.unified_behavior.schedule_parent_realtime_message")
@patch("app.services.unified_behavior.get_unified_behavior_analysis")
def test_refresh_and_notify_dashboard_pushes_ws(mock_analysis, mock_schedule):
    child = MagicMock()
    child.id = 1
    child.name = "Ali"
    child.parent_id = 10

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = child

    mock_analysis.return_value = {
        "overall_score": 72,
        "upgraded_categories": ["social"],
        "downgraded_categories": [],
    }

    result = ub.refresh_and_notify_dashboard(db, 1, "daily_checkin")
    assert result["overall_score"] == 72
    mock_schedule.assert_called_once()
    msg = mock_schedule.call_args[0][1]
    assert msg["type"] == "dashboard_update"
    assert msg["data"]["trigger"] == "daily_checkin"
    assert msg["data"]["child_id"] == 1
