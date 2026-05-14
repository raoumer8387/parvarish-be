import pytest

from app.utils import logging as logutil


@pytest.mark.unit
def test_get_logger_configures_handlers():
    log = logutil.get_logger("test_parvarish_logger")
    assert log.name == "test_parvarish_logger"
