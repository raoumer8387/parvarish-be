from datetime import datetime, timezone

import pytest

from app.routes.child_progress import _ensure_timezone_aware


@pytest.mark.unit
def test_ensure_timezone_aware_naive_and_aware():
    naive = datetime(2024, 1, 1, 12, 0, 0)
    out = _ensure_timezone_aware(naive)
    assert out.tzinfo is timezone.utc

    aware = datetime(2024, 1, 1, tzinfo=timezone.utc)
    assert _ensure_timezone_aware(aware) is aware
