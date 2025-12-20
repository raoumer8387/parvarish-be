"""LLM API client for Parvarish AI using OpenRouter via OpenAI SDK.

Expose a simple `generate_response(messages)` function compatible with
chat-like interactions. Messages is a list of dicts with keys: role, content.

Environment variables:
- OPENROUTER_API_KEY: required
- OPENROUTER_MODEL: optional (default: meta-llama/llama-3.1-8b-instruct:free)
- OPENROUTER_MAX_TOKENS: optional (default: 512)
- OPENROUTER_BASE_URL: optional (default: https://openrouter.ai/api/v1)
- OPENROUTER_REFERER: optional (site URL for rankings)
- OPENROUTER_TITLE: optional (site title for rankings)
"""

from typing import List
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from a .env file if present
load_dotenv()

_API_KEY = os.getenv("OPENROUTER_API_KEY", "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")
_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
_MAX_TOKENS = int(os.getenv("OPENROUTER_MAX_TOKENS", "800"))  # Increased for multilingual responses
_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
_REFERER = os.getenv("OPENROUTER_REFERER", "http://localhost:8000")
_TITLE = os.getenv("OPENROUTER_TITLE", "Parvarish-AI")


def _ensure_api_key() -> str:
    if not _API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY not set in environment")
    return _API_KEY


def generate_response(messages: List[dict]) -> str:
    """Return an assistant message given a list of messages using OpenRouter API.

    Args:
        messages: [{role: system|user|assistant, content: str}]
    Returns:
        str: Assistant text response
    """
    api_key = _ensure_api_key()
    
    client = OpenAI(base_url=_BASE_URL, api_key=api_key)

    # Optional ranking headers
    extra_headers = {}
    if _REFERER:
        extra_headers["HTTP-Referer"] = _REFERER
    if _TITLE:
        extra_headers["X-Title"] = _TITLE

    try:
        completion = client.chat.completions.create(
            model=_MODEL,
            messages=messages,
            max_tokens=_MAX_TOKENS,
            extra_headers=extra_headers or None,
        )
        if not completion.choices:
            return "I apologize, but I received an empty response. Please try rephrasing your question."

        content = completion.choices[0].message.content or ""
        return content.strip() or "I couldn't generate a response. Please try again."

    except Exception as e:
        raise RuntimeError(f"OpenRouter error: {e}")