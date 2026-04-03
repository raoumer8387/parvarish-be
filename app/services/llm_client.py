"""LLM API client for Parvarish AI with fallback support.

Expose `generate_response(messages)` for chat-like calls. Message `content` may be a
string or OpenAI-style multimodal parts (text, image_url, file/PDF).

Environment variables (priority: Google Gemini if GOOGLE_API_KEY is set, else OpenRouter):

Google Gemini (direct API — https://aistudio.google.com/apikey):
- GOOGLE_API_KEY or GEMINI_API_KEY: Google AI Studio key (AIza…)
- GEMINI_MODEL: optional (default: gemini-2.5-flash) — text chat
- GEMINI_VISION_MODEL: optional — image/PDF chat; defaults to GEMINI_MODEL
- GEMINI_MAX_OUTPUT_TOKENS: optional (default: 4096) — Gemini completion cap; separate from OpenRouter

OpenRouter (if no valid Google key):
- OPENROUTER_API_KEY: sk-or-v1-…
- OPENROUTER_MODEL, OPENROUTER_VISION_MODEL, OPENROUTER_BASE_URL, etc.

Shared:
- OPENROUTER_MAX_TOKENS: max output tokens for OpenRouter only (default: 976)
- LLM_MAX_OUTPUT_TOKENS: optional alias for GEMINI_MAX_OUTPUT_TOKENS
- OPENROUTER_RATE_LIMIT_RETRIES / OPENROUTER_RATE_LIMIT_DELAY_SEC: retries on 429
- HF_TOKEN: Hugging Face token for embedding models
"""

from __future__ import annotations

import base64
import os
import time
from typing import Any, List, Optional, Tuple

import httpx
from dotenv import load_dotenv

load_dotenv()

_GOOGLE_API_KEY = (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or "").strip()
_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
_GEMINI_VISION_MODEL = os.getenv("GEMINI_VISION_MODEL") or _GEMINI_MODEL

_OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
_OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "qwen/qwen3-30b-a3b-instruct-2507")
_VISION_MODEL = os.getenv("OPENROUTER_VISION_MODEL", "google/gemini-2.5-pro")
_MAX_TOKENS = int(os.getenv("OPENROUTER_MAX_TOKENS", "976"))
_GEMINI_MAX_OUTPUT_TOKENS = int(
    os.getenv("GEMINI_MAX_OUTPUT_TOKENS")
    or os.getenv("LLM_MAX_OUTPUT_TOKENS")
    or "4096"
)
_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
_REFERER = os.getenv("OPENROUTER_REFERER", "http://localhost:8000")
_TITLE = os.getenv("OPENROUTER_TITLE", "Parvarish-AI")
_RATE_LIMIT_RETRIES = int(os.getenv("OPENROUTER_RATE_LIMIT_RETRIES", "3"))
_RATE_LIMIT_DELAY = float(os.getenv("OPENROUTER_RATE_LIMIT_DELAY_SEC", "2"))


def _user_content_as_text(content: Any) -> str:
    if isinstance(content, str):
        return content.lower()
    if isinstance(content, list):
        parts: List[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return " ".join(parts).lower()
    return ""


def _use_simple_fallback(messages: List[dict]) -> str:
    user_message = ""
    for msg in messages:
        if msg.get("role") == "user":
            user_message = _user_content_as_text(msg.get("content"))
            break

    if any(word in user_message for word in ["salaam", "salam", "hello", "hi", "assalam"]):
        return "Assalamu Alaikum! I'm here to help you with Islamic parenting guidance. How can I assist you today?"
    if any(word in user_message for word in ["prayer", "salah", "namaz"]):
        return "Teaching children about prayer is very important in Islam. Start with making it fun and age-appropriate. Would you like specific tips for your child's age?"
    if any(word in user_message for word in ["quran", "qur'an", "recitation"]):
        return "The Quran is the best guide for raising children. Teaching them to recite and understand its meanings from an early age builds strong Islamic character."
    if any(word in user_message for word in ["behavior", "discipline", "manners"]):
        return "Islamic parenting emphasizes gentle guidance and positive reinforcement. The Prophet (PBUH) taught us to be patient and kind with children while teaching them good values."
    if any(word in user_message for word in ["dua", "supplication"]):
        return "Teaching children to make dua is a beautiful way to connect them with Allah. Start with simple duas for daily activities like eating, sleeping, and studying."
    return "I'm here to help with Islamic parenting guidance. Please feel free to ask about raising children according to Islamic values, teaching prayers, Quran recitation, or building good character."


def _google_key_valid() -> Optional[str]:
    if not _GOOGLE_API_KEY or _GOOGLE_API_KEY in ("your-google-ai-api-key", "paste-your-key-here"):
        return None
    return _GOOGLE_API_KEY


def _openrouter_key_valid() -> Optional[str]:
    if not _OPENROUTER_API_KEY or _OPENROUTER_API_KEY == "sk-or-v1-your-openrouter-api-key-here":
        return None
    return _OPENROUTER_API_KEY


def _normalize_gemini_model_id(model: Optional[str]) -> str:
    if not model:
        return _GEMINI_MODEL
    m = model.strip()
    if m.startswith("google/"):
        m = m[7:]
    if m.endswith(":free"):
        m = m[:-5]
    return m or _GEMINI_MODEL


def _parse_data_url(url: str) -> Tuple[Optional[bytes], str]:
    if not url or not isinstance(url, str):
        return None, "application/octet-stream"
    if not url.startswith("data:"):
        return None, ""
    try:
        head, b64part = url.split(",", 1)
        mime = head.split(";")[0].split(":", 1)[1]
        raw = base64.b64decode(b64part, validate=False)
        return raw, mime
    except Exception:
        return None, "application/octet-stream"


def _openai_blocks_to_gemini_parts(content: Any) -> List[Any]:
    from google.genai import types

    if isinstance(content, str):
        return [types.Part(text=content)]
    if not isinstance(content, list):
        return [types.Part(text=str(content))]

    parts: List[Any] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        t = block.get("type")
        if t == "text":
            parts.append(types.Part(text=str(block.get("text", ""))))
        elif t == "image_url":
            iu = block.get("image_url") or {}
            url = iu.get("url") if isinstance(iu, dict) else iu
            if not url:
                continue
            raw, mime = _parse_data_url(url)
            if raw:
                parts.append(types.Part.from_bytes(data=raw, mime_type=mime))
            elif url.startswith("http"):
                try:
                    r = httpx.get(url, timeout=60.0, follow_redirects=True)
                    r.raise_for_status()
                    ct = (r.headers.get("content-type") or "image/jpeg").split(";")[0].strip()
                    parts.append(types.Part.from_bytes(data=r.content, mime_type=ct))
                except Exception as ex:
                    print(f"Gemini: failed to fetch image URL: {ex}")
        elif t == "file":
            f = block.get("file") or {}
            fd = f.get("file_data") or f.get("fileData")
            raw, mime = _parse_data_url(fd or "")
            if raw:
                parts.append(types.Part.from_bytes(data=raw, mime_type=mime or "application/pdf"))

    return parts if parts else [types.Part(text="")]


def _messages_to_gemini_contents(messages: List[dict]) -> Tuple[Optional[str], List[Any]]:
    from google.genai import types

    system_chunks: List[str] = []
    contents: List[Any] = []
    for msg in messages:
        role = msg.get("role")
        c = msg.get("content")
        if role == "system":
            system_chunks.append(c if isinstance(c, str) else str(c))
            continue
        if role == "user":
            parts = _openai_blocks_to_gemini_parts(c)
            contents.append(types.Content(role="user", parts=parts))
        elif role == "assistant":
            text = c if isinstance(c, str) else (str(c) if c is not None else "")
            contents.append(types.Content(role="model", parts=[types.Part(text=text)]))

    si = "\n".join(system_chunks).strip() if system_chunks else None
    return (si or None), contents


def _generate_with_gemini(
    messages: List[dict],
    *,
    model: Optional[str],
    plugins: Optional[List[dict]],
) -> str:
    if plugins:
        pass  # OpenRouter-only; Gemini ingests PDF bytes natively via file parts

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("Gemini: install google-genai (pip install google-genai). Falling back.")
        return _use_simple_fallback(messages)

    api_key = _google_key_valid()
    if not api_key:
        return _use_simple_fallback(messages)

    system_instruction, contents = _messages_to_gemini_contents(messages)
    if not contents:
        return _use_simple_fallback(messages)

    model_id = _normalize_gemini_model_id(model)
    client = genai.Client(api_key=api_key)
    cfg_kwargs: dict = {"max_output_tokens": _GEMINI_MAX_OUTPUT_TOKENS}
    if system_instruction:
        cfg_kwargs["system_instruction"] = system_instruction
    config = types.GenerateContentConfig(**cfg_kwargs)

    last_exc: Optional[BaseException] = None
    for attempt in range(_RATE_LIMIT_RETRIES + 1):
        try:
            resp = client.models.generate_content(
                model=model_id,
                contents=contents,
                config=config,
            )
            text = (getattr(resp, "text", None) or "").strip()
            if not text and resp.candidates:
                c0 = resp.candidates[0]
                if getattr(c0, "content", None) and c0.content.parts:
                    text = "".join(
                        getattr(p, "text", "") or "" for p in c0.content.parts
                    ).strip()
            fr = None
            if resp.candidates:
                fr = getattr(resp.candidates[0], "finish_reason", None)
            if fr and ("MAX_TOKENS" in str(fr).upper()):
                print(
                    "Gemini: reply may be truncated (max output tokens). "
                    "Increase GEMINI_MAX_OUTPUT_TOKENS (or LLM_MAX_OUTPUT_TOKENS) in .env if needed."
                )
            return text or _use_simple_fallback(messages)
        except Exception as e:
            last_exc = e
            err = str(e).lower()
            if ("429" in str(e) or "resource exhausted" in err or "quota" in err) and attempt < _RATE_LIMIT_RETRIES:
                wait = _RATE_LIMIT_DELAY * (2**attempt)
                print(f"Gemini 429/quota; retrying in {wait:.1f}s ({attempt + 1}/{_RATE_LIMIT_RETRIES})...")
                time.sleep(wait)
                continue
            break

    print(f"Gemini failed, using fallback: {last_exc}")
    return _use_simple_fallback(messages)


def _generate_with_openrouter(
    messages: List[dict],
    *,
    plugins: Optional[List[dict]],
    model: Optional[str],
) -> str:
    try:
        from openai import OpenAI

        client = OpenAI(base_url=_BASE_URL, api_key=_openrouter_key_valid())

        extra_headers = {}
        if _REFERER:
            extra_headers["HTTP-Referer"] = _REFERER
        if _TITLE:
            extra_headers["X-Title"] = _TITLE

        kwargs = dict(
            model=model if model is not None else _OPENROUTER_MODEL,
            messages=messages,
            max_tokens=_MAX_TOKENS,
            extra_headers=extra_headers or None,
        )
        if plugins:
            kwargs["extra_body"] = {"plugins": plugins}

        last_exc: Optional[BaseException] = None
        for attempt in range(_RATE_LIMIT_RETRIES + 1):
            try:
                completion = client.chat.completions.create(**kwargs)
                if not completion.choices:
                    return _use_simple_fallback(messages)
                choice = completion.choices[0]
                content = choice.message.content or ""
                if getattr(choice, "finish_reason", None) == "length":
                    print(
                        "OpenRouter: reply hit max_tokens limit (finish_reason=length). "
                        "Increase OPENROUTER_MAX_TOKENS if answers are cut off."
                    )
                return content.strip() or _use_simple_fallback(messages)
            except Exception as e:
                last_exc = e
                code = getattr(e, "status_code", None)
                if code == 429 and attempt < _RATE_LIMIT_RETRIES:
                    wait = _RATE_LIMIT_DELAY * (2**attempt)
                    print(
                        f"OpenRouter 429 rate limit; retrying in {wait:.1f}s "
                        f"(attempt {attempt + 1}/{_RATE_LIMIT_RETRIES})..."
                    )
                    time.sleep(wait)
                    continue
                break
        raise last_exc

    except Exception as e:
        status = getattr(e, "status_code", None)
        err_text = str(e).lower()
        if status == 402 or "402" in str(e) or "credits" in err_text:
            print(
                "OpenRouter: insufficient credits (402). Add credits at "
                "https://openrouter.ai/settings/credits — or lower OPENROUTER_MAX_TOKENS in .env. "
                f"Detail: {e}"
            )
        elif status == 404 or "image input" in err_text or "no endpoints found" in err_text:
            print(
                "OpenRouter: model does not support this input (often 404 for images with a text-only model). "
                "Set OPENROUTER_VISION_MODEL to a vision-capable model for /chat/with-attachments. "
                f"Detail: {e}"
            )
        elif status == 429 or "429" in str(e) or "rate" in err_text:
            print(
                "OpenRouter: rate limited (429). "
                f"Detail: {e}"
            )
        else:
            print(f"OpenRouter failed, using fallback: {e}")
        return _use_simple_fallback(messages)


def get_attachment_model() -> str:
    """Model id passed into generate_response for multimodal chat."""
    if _google_key_valid():
        return _GEMINI_VISION_MODEL
    return _VISION_MODEL


def generate_response(
    messages: List[dict],
    *,
    plugins: Optional[List[dict]] = None,
    model: Optional[str] = None,
) -> str:
    """Return assistant text using Gemini (if GOOGLE_API_KEY), else OpenRouter, else rule-based fallback."""
    if _google_key_valid():
        mid = model if model is not None else _GEMINI_MODEL
        return _generate_with_gemini(messages, model=mid, plugins=plugins)

    if _openrouter_key_valid():
        return _generate_with_openrouter(messages, plugins=plugins, model=model)

    return _use_simple_fallback(messages)
