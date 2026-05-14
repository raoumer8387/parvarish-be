import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException

from app.routes import chatbot


@pytest.mark.unit
def test_normalize_video_url():
    assert chatbot._normalize_video_url("  https://example.com/x  ") == "https://example.com/x"
    assert chatbot._normalize_video_url("") == ""
    assert chatbot._normalize_video_url("example.com").startswith("https://")


@pytest.mark.unit
def test_classify_attachment_pdf_and_image():
    assert chatbot._classify_chat_attachment("a.pdf", "application/pdf") == "pdf"
    assert chatbot._classify_chat_attachment("p.png", "image/png") == "image"


@pytest.mark.unit
def test_validate_audio_upload_errors():
    upload = MagicMock()
    upload.filename = ""
    with pytest.raises(HTTPException) as e:
        chatbot._validate_audio_upload(upload, b"data")
    assert e.value.status_code == 400

    upload.filename = "a.mp3"
    with pytest.raises(HTTPException) as e:
        chatbot._validate_audio_upload(upload, b"")
    assert e.value.status_code == 400


@pytest.mark.unit
def test_get_response_generator_is_callable():
    fn = chatbot.get_response_generator()
    assert callable(fn)
