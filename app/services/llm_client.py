"""LLM API client for Parvarish AI with fallback support.

Expose a simple `generate_response(messages)` function compatible with
chat-like interactions. Messages is a list of dicts with keys: role, content.

Environment variables:
- OPENROUTER_API_KEY: optional (if not provided, uses free fallback)
- OPENROUTER_MODEL: optional (default: google/gemini-2.5-flash)
- OPENROUTER_MAX_TOKENS: optional (default: 800)
- HF_TOKEN: optional (Hugging Face token for better rate limits)
"""

from typing import List
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()

_API_KEY = os.getenv("OPENROUTER_API_KEY")
_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
_MAX_TOKENS = int(os.getenv("OPENROUTER_MAX_TOKENS", "800"))
_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
_REFERER = os.getenv("OPENROUTER_REFERER", "http://localhost:8000")
_TITLE = os.getenv("OPENROUTER_TITLE", "Parvarish-AI")
_HF_TOKEN = os.getenv("HF_TOKEN")


def _use_simple_fallback(messages: List[dict]) -> str:
    """Simple rule-based fallback for Islamic parenting context."""
    user_message = ""
    for msg in messages:
        if msg["role"] == "user":
            user_message = msg["content"].lower()
            break
    
    if any(word in user_message for word in ["salaam", "salam", "hello", "hi", "assalam"]):
        return "Assalamu Alaikum! I'm here to help you with Islamic parenting guidance. How can I assist you today?"
    elif any(word in user_message for word in ["prayer", "salah", "namaz"]):
        return "Teaching children about prayer is very important in Islam. Start with making it fun and age-appropriate. Would you like specific tips for your child's age?"
    elif any(word in user_message for word in ["quran", "qur'an", "recitation"]):
        return "The Quran is the best guide for raising children. Teaching them to recite and understand its meanings from an early age builds strong Islamic character."
    elif any(word in user_message for word in ["behavior", "discipline", "manners"]):
        return "Islamic parenting emphasizes gentle guidance and positive reinforcement. The Prophet (PBUH) taught us to be patient and kind with children while teaching them good values."
    elif any(word in user_message for word in ["dua", "supplication"]):
        return "Teaching children to make dua is a beautiful way to connect them with Allah. Start with simple duas for daily activities like eating, sleeping, and studying."
    else:
        return "I'm here to help with Islamic parenting guidance. Please feel free to ask about raising children according to Islamic values, teaching prayers, Quran recitation, or building good character."


def _ensure_api_key() -> str:
    if not _API_KEY or _API_KEY == "sk-or-v1-your-openrouter-api-key-here":
        return None  # Will trigger fallback
    return _API_KEY


def generate_response(messages: List[dict]) -> str:
    """Return an assistant message given a list of messages using OpenRouter API or fallback.

    Args:
        messages: [{role: system|user|assistant, content: str}]
    Returns:
        str: Assistant text response
    """
    api_key = _ensure_api_key()
    
    # If no valid API key, use fallback
    if not api_key:
        return _use_simple_fallback(messages)
    
    # Try OpenRouter first
    try:
        from openai import OpenAI
        client = OpenAI(base_url=_BASE_URL, api_key=api_key)

        # Optional ranking headers
        extra_headers = {}
        if _REFERER:
            extra_headers["HTTP-Referer"] = _REFERER
        if _TITLE:
            extra_headers["X-Title"] = _TITLE

        completion = client.chat.completions.create(
            model=_MODEL,
            messages=messages,
            max_tokens=_MAX_TOKENS,
            extra_headers=extra_headers or None,
        )
        if not completion.choices:
            return _use_simple_fallback(messages)

        content = completion.choices[0].message.content or ""
        return content.strip() or _use_simple_fallback(messages)

    except Exception as e:
        print(f"OpenRouter failed, using fallback: {e}")
        return _use_simple_fallback(messages)