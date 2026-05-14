from unittest.mock import MagicMock

import pytest

from app.services import lacking_analyzer


@pytest.mark.unit
def test_analyze_presence_of_mind_insufficient_data():
    result = lacking_analyzer.analyze_presence_of_mind([])
    assert result["status"] == "insufficient_data"
    assert result["score"] is None


@pytest.mark.unit
def test_should_generate_ticker_returns_true_when_no_recent_matching_task():
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = []
    allowed = lacking_analyzer.should_generate_ticker(db, child_id=1, lacking_area="mood_identification")
    assert allowed is True
