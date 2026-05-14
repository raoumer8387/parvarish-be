import pytest

from app.services import llm_client


@pytest.mark.unit
def test_generate_response_fallback_when_no_api_keys(monkeypatch):
    monkeypatch.setattr(llm_client, "_google_key_valid", lambda: None)
    monkeypatch.setattr(llm_client, "_openrouter_key_valid", lambda: None)
    text = llm_client.generate_response([{"role": "user", "content": "salaam parents"}])
    assert len(text) > 0


@pytest.mark.unit
def test_get_attachment_model_returns_string(monkeypatch):
    monkeypatch.setattr(llm_client, "_google_key_valid", lambda: None)
    monkeypatch.setattr(llm_client, "_openrouter_key_valid", lambda: None)
    mid = llm_client.get_attachment_model()
    assert isinstance(mid, str)


@pytest.mark.unit
def test_get_generation_callable():
    fn = llm_client.get_generation_callable()
    assert fn is llm_client.generate_response


@pytest.mark.unit
def test_user_content_as_text_variants():
    assert llm_client._user_content_as_text("Hello") == "hello"
    joined = llm_client._user_content_as_text([{"type": "text", "text": "Beta"}])
    assert "beta" in joined


@pytest.mark.unit
def test_normalize_gemini_model_id_strips_prefix():
    assert llm_client._normalize_gemini_model_id("google/gemini-pro:free") == "gemini-pro"


@pytest.mark.unit
def test_parse_data_url_png():
    raw, mime = llm_client._parse_data_url("data:image/png;base64,Zm9v")
    assert raw == b"foo"
    assert mime == "image/png"
