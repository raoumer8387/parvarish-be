import pytest

from app.utils.language_detector import detect_language


@pytest.mark.unit
@pytest.mark.parametrize(
    "text,expected",
    [
        ("Hello world", "en"),
        ("kaise ho", "rm"),
        ("آپ کیسے ہیں", "ur"),
    ],
)
def test_detect_language(text, expected):
    assert detect_language(text) == expected
