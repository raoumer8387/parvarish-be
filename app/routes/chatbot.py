"""Chatbot routes for Parvarish AI.

Expose endpoints for sending user messages and retrieving bot responses using RAG.
"""

import base64
import os
import random
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, File, Form, UploadFile
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Tuple
from sqlalchemy.orm import Session
from app.rag.data_loader import DataLoader
from app.rag.embedder import Embedder, VectorStoreConfig
from app.rag.retriever import Retriever
from app.services.llm_client import generate_response, get_attachment_model
from app.db.crud.message import create_message, list_messages_for_user
from app.schemas.chat import ChatHistoryResponse, ChatMessage
from app.db.session import get_db
from app.db.models.child import Child
from app.services.behavior_service import get_child_behavior_stats
from app.core.security import get_current_user
from app.db.models.user import User
from app.services.speech_to_text import transcribe_audio_bytes
from app.utils.language_detector import detect_language  # Import the detector

router = APIRouter(tags=["chatbot"])

# Initialize RAG components (singleton pattern)
_retriever = None
MAX_AUDIO_BYTES = 10 * 1024 * 1024
SUPPORTED_AUDIO_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/mp4",
    "audio/m4a",
    "audio/x-m4a",
    "audio/wav",
    "audio/x-wav",
    "audio/webm",
    "audio/ogg",
    "audio/oga",
}
SUPPORTED_AUDIO_EXTENSIONS = {
    ".mp3",
    ".mp4",
    ".m4a",
    ".wav",
    ".webm",
    ".ogg",
    ".oga",
}

# Chat attachments (images + PDF) for OpenRouter multimodal
MAX_ATTACHMENT_BYTES = 15 * 1024 * 1024  # 15 MB per file
MAX_CHAT_ATTACHMENTS = 5
SUPPORTED_IMAGE_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "image/gif",
}
SUPPORTED_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
PDF_MIME_TYPES = {"application/pdf"}
PDF_EXT = {".pdf"}
_DEFAULT_ATTACHMENT_PROMPT = (
    "Please review the attached file(s) and provide Islamic parenting guidance where relevant."
)

def get_retriever() -> Retriever:
    """Get or initialize the RAG retriever."""
    global _retriever
    if _retriever is None:
        loader = DataLoader()
        docs = loader.load()
        store = Embedder(VectorStoreConfig())
        
        # Check if index needs building
        try:
            if store.collection.count() == 0:
                store.build_index(docs, reset=False)
        except Exception:
            store.build_index(docs, reset=False)
        
        _retriever = Retriever(store.as_retriever())
    return _retriever


def _markdown_link_label(text: str) -> str:
    """Escape characters that would break [label](url) markdown link text."""
    return text.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def _get_random_video_suggestions(lang: Literal["en", "ur", "rm"], count: int = 2) -> str:
    """Append random playlist videos; titles use markdown links so URLs are clickable in markdown-capable clients."""
    root = Path(__file__).resolve().parents[2]
    playlist_path = root / "data" / "parvarish_playlist_tagged.json"
    headers = {
        "en": "Recommended videos",
        "ur": "تجویز کردہ ویڈیوز",
        "rm": "Mashwara videos",
    }
    try:
        with open(playlist_path, encoding="utf-8") as f:
            playlist = json.load(f)

        if not playlist:
            return ""

        suggestions = random.sample(playlist, min(count, len(playlist)))
        if not suggestions:
            return ""

        header = headers.get(lang, headers["en"])
        lines = ["\n\n", header, "\n\n"]
        for n, video in enumerate(suggestions, start=1):
            title = str(video.get("Title") or "Video").strip() or "Video"
            url = (video.get("URL") or "").strip() or "#"
            safe = _markdown_link_label(title)
            lines.append(f"{n}. [{safe}]({url})\n")
        return "".join(lines)
    except (OSError, json.JSONDecodeError, ValueError) as e:
        print(f"Could not generate video suggestions: {e}")
        return ""


class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "anonymous"
    child_id: Optional[int] = None  # Optional: specific child context


class ChatResponse(BaseModel):
    response: str
    user_id: str


class VoiceChatResponse(ChatResponse):
    transcription: str
    filename: Optional[str] = None


class ChatWithAttachmentsResponse(ChatResponse):
    """Same as ChatResponse plus filenames of processed attachments."""

    attachment_names: List[str] = Field(default_factory=list)


SYSTEM_PROMPT = (
    "You are Parvarish AI – an Islamic parenting companion. "
    "Your role is to guide parents with wisdom and compassion based on authentic Islamic teachings. "
    "Use the provided Quranic verses, Hadith, Prophet (PBUH) stories, AND Islamic Scholar References (from classical books like Ihya Ulum ad-Din, Tafsir Ibn Kathir, Adab al-Mufrad, etc.) to offer advice about raising children, behavior, and moral development. "
    "LANGUAGE: You MUST write the entire reply in exactly ONE language — the language named in RESPONSE INSTRUCTIONS below "
    "(English, Urdu in Arabic script, or Roman Urdu using Latin letters). "
    "Do not repeat the answer in other languages; do not add EN/UR/RM sections unless the user explicitly asks for multiple languages. "
    "CITATION REQUIREMENT: When referencing Islamic scholars, ALWAYS include the book title and author name like: [Book Title – Author]. "
    "Example: 'As mentioned in Ihya Ulum ad-Din by Imam Al-Ghazali...' "
    "Speak gently and respectfully, maintaining an educational and empathetic tone. "
    "If no relevant reference is found in the given data, respond politely that you currently do not have Islamic guidance on that specific topic. Do not speculate or invent information. "
    "Provide SHORT, concise answers (1-2 paragraphs maximum). Focus on actionable advice. Be brief and direct."
)


def _get_child_context(db: Session, current_user: User, child_id: Optional[int]) -> str:
    """Build optional child context after ownership validation."""
    if not child_id:
        return ""

    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    if current_user.user_type == "parent" and child.parent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to this child's data")

    stats = get_child_behavior_stats(db, child_id, days=30)
    return f"""
CHILD PROFILE:
- Name: {child.name}
- Age: {child.age} years old
- Gender: {child.gender or 'Not specified'}
- School: {child.school or 'Not specified'}
- Class: {child.class_name or 'Not specified'}
- Temperament: {child.temperament or 'Not specified'}

RECENT BEHAVIOR DATA (Last 30 days):
- Behavior Level: {stats['behavior_level']:.1f}%
- Islamic Knowledge: {stats['islamic_knowledge']:.1f}%
- Total Responses: {stats['total_responses']}
- Last Assessment: {stats['last_response_at'] or 'Never'}
- Category Breakdown: {', '.join([f'{k}: {v:.0f}%' for k, v in stats['categories'].items()])}

Use this context to provide PERSONALIZED advice for {child.name}. Reference their age, temperament, and current behavior patterns when relevant.
"""


def _build_prompt(message: str, child_context: str, child_id: Optional[int], db: Session) -> Tuple[str, Literal["en", "ur", "rm"]]:
    """Construct the full prompt for the LLM, tailored to the detected language."""
    retriever = get_retriever()
    chunks = retriever.query(message, k=8)
    context = Retriever.format_context(chunks) if chunks else "No specific references found in the database."

    max_context_length = 2000
    if len(context) > max_context_length:
        context = context[:max_context_length] + "\n[Context truncated...]"

    lang: Literal["en", "ur", "rm"] = detect_language(message)

    lang_instructions: dict[str, str] = {
        "en": "Write your entire answer in English only.",
        "ur": "اپنا پورا جواب صرف اردو میں لکھیں (عربی رسم الخط میں)۔ انگریزی یا رومن اردو میں مت لکھیں۔",
        "rm": "Apna poora jawab sirf Roman Urdu mein likhein (Latin letters). English ya Urdu script mein mat likhein.",
    }

    prompt = f"""{SYSTEM_PROMPT}
{child_context}

Here are relevant Islamic references to help answer the question:
{context}

Question: {message}

**RESPONSE INSTRUCTIONS:**
- {lang_instructions.get(lang, lang_instructions["en"])}
- Keep the answer concise (2-3 paragraphs).
- Do not add a "Recommended Videos" list yourself; video links will be appended separately after your reply.

---
**CRITICAL: CITATION REQUIREMENTS**
You MUST cite your sources. Follow these rules exactly:
- For Quran: "As Allah says in the Quran (Surah Al-Isra, 17:23)..."
- For Hadith: "The Prophet (PBUH) said..." and then cite the reference, like "(Sahih al-Bukhari, 5997)".
- For any other text, use the source information provided in the context, for example: "(Source: Ihya Ulum ad-Din by Imam Al-Ghazali)".
- If the context provides a `[Source X: ...]` header, you MUST use it to cite the information. For example, if you use text from `[Source 1: Quran, 17:23]`, you must cite it as `(Quran, 17:23)`.
- Aim to use at least one reference in your answer if relevant sources are provided in the context.
---
"""
    return prompt, lang


def _generate_chat_response(
    *,
    message: str,
    user_id: str,
    child_id: Optional[int],
    db: Session,
    current_user: User,
) -> ChatResponse:
    """Generate and persist a chatbot response from a text message."""
    if not message or not message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    child_context = _get_child_context(db, current_user, child_id)
    full_prompt, reply_lang = _build_prompt(message, child_context, child_id, db)
    answer = generate_response([{"role": "user", "content": full_prompt}])
    answer = answer.rstrip() + _get_random_video_suggestions(reply_lang, count=2)

    try:
        create_message(db, user_id=current_user.id, role="user", content=message, child_id=child_id)
        create_message(db, user_id=current_user.id, role="assistant", content=answer, child_id=child_id)
    except Exception as db_err:
        print(f"WARNING: Failed to persist chat messages: {db_err}")

    return ChatResponse(response=answer, user_id=user_id)


def _normalize_user_message_for_attachments(message: Optional[str]) -> str:
    text = (message or "").strip()
    return text if text else _DEFAULT_ATTACHMENT_PROMPT


def _mime_from_image_upload(filename: str, content_type: Optional[str]) -> str:
    normalized = (content_type or "").split(";", 1)[0].strip().lower()
    if normalized in SUPPORTED_IMAGE_TYPES:
        if normalized == "image/jpg":
            return "image/jpeg"
        return normalized
    ext = Path(filename or "").suffix.lower()
    if ext == ".jpg":
        return "image/jpeg"
    if ext == ".png":
        return "image/png"
    if ext == ".webp":
        return "image/webp"
    if ext == ".gif":
        return "image/gif"
    return "image/jpeg"


def _classify_chat_attachment(filename: str, content_type: Optional[str]) -> Optional[Literal["image", "pdf"]]:
    ext = Path(filename or "").suffix.lower()
    normalized = (content_type or "").split(";", 1)[0].strip().lower()
    if normalized in PDF_MIME_TYPES or ext in PDF_EXT:
        return "pdf"
    if normalized in SUPPORTED_IMAGE_TYPES or (
        normalized == "application/octet-stream" and ext in SUPPORTED_IMAGE_EXT
    ):
        return "image"
    if ext in SUPPORTED_IMAGE_EXT:
        return "image"
    if ext in PDF_EXT:
        return "pdf"
    return None


def _validate_chat_attachment_file(
    upload: UploadFile,
    raw: bytes,
    *,
    index: int,
) -> Tuple[Literal["image", "pdf"], str, bytes, Optional[str]]:
    if not raw:
        raise HTTPException(status_code=400, detail=f"Attachment {index + 1} is empty")
    if len(raw) > MAX_ATTACHMENT_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Attachment {index + 1} exceeds maximum size of {MAX_ATTACHMENT_BYTES // (1024 * 1024)} MB",
        )
    name = upload.filename or f"file_{index + 1}"
    kind = _classify_chat_attachment(name, upload.content_type)
    if not kind:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported attachment type for '{name}'. Use PNG, JPEG, WebP, GIF, or PDF.",
        )
    return kind, name, raw, upload.content_type


def _build_multimodal_user_content(
    full_prompt: str,
    parts: List[Tuple[Literal["image", "pdf"], str, bytes, Optional[str]]],
) -> list:
    """OpenRouter multimodal user message: text first, then images, then PDFs."""
    content: list = [{"type": "text", "text": full_prompt}]
    image_parts: list = []
    pdf_parts: list = []
    for kind, filename, raw, declared_type in parts:
        if kind == "image":
            mime = _mime_from_image_upload(filename, declared_type)
            b64 = base64.b64encode(raw).decode("ascii")
            data_url = f"data:{mime};base64,{b64}"
            image_parts.append({"type": "image_url", "image_url": {"url": data_url}})
        else:
            b64 = base64.b64encode(raw).decode("ascii")
            data_url = f"data:application/pdf;base64,{b64}"
            safe_name = filename if filename.lower().endswith(".pdf") else f"{filename}.pdf"
            pdf_parts.append(
                {
                    "type": "file",
                    "file": {"filename": safe_name, "file_data": data_url},
                }
            )
    content.extend(image_parts)
    content.extend(pdf_parts)
    return content


def _generate_chat_response_with_attachments(
    *,
    message: Optional[str],
    parsed_files: List[Tuple[Literal["image", "pdf"], str, bytes, Optional[str]]],
    user_id: str,
    child_id: Optional[int],
    db: Session,
    current_user: User,
) -> ChatWithAttachmentsResponse:
    user_text = _normalize_user_message_for_attachments(message)
    child_context = _get_child_context(db, current_user, child_id)
    full_prompt, reply_lang = _build_prompt(user_text, child_context, child_id, db)
    user_message = {"role": "user", "content": _build_multimodal_user_content(full_prompt, parsed_files)}

    has_pdf = any(k == "pdf" for k, _, _, _ in parsed_files)
    plugins = None
    if has_pdf:
        engine = os.getenv("OPENROUTER_PDF_ENGINE", "cloudflare-ai")
        plugins = [{"id": "file-parser", "pdf": {"engine": engine}}]

    answer = generate_response(
        [user_message],
        plugins=plugins,
        model=get_attachment_model(),
    )
    answer = answer.rstrip() + _get_random_video_suggestions(reply_lang, count=2)

    names = [name for _, name, _, _ in parsed_files]
    persist_user = user_text
    if names:
        persist_user = f"{user_text}\n[Attachments: {', '.join(names)}]"

    try:
        create_message(db, user_id=current_user.id, role="user", content=persist_user, child_id=child_id)
        create_message(db, user_id=current_user.id, role="assistant", content=answer, child_id=child_id)
    except Exception as db_err:
        print(f"WARNING: Failed to persist chat messages: {db_err}")

    return ChatWithAttachmentsResponse(response=answer, user_id=user_id, attachment_names=names)


def _validate_audio_upload(audio: UploadFile, audio_bytes: bytes) -> None:
    """Validate uploaded audio file metadata and size."""
    if not audio.filename:
        raise HTTPException(status_code=400, detail="Audio filename is required")
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Audio file is empty")
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Audio file is too large. Maximum size is 10 MB")
    normalized_content_type = (audio.content_type or "").split(";", 1)[0].strip().lower()
    file_extension = Path(audio.filename).suffix.lower()

    is_supported_mime = normalized_content_type in SUPPORTED_AUDIO_TYPES
    is_octet_stream = normalized_content_type == "application/octet-stream"
    is_supported_extension = file_extension in SUPPORTED_AUDIO_EXTENSIONS

    if normalized_content_type and not is_supported_mime:
        # Some clients/browsers send generic octet-stream; accept if extension is valid audio.
        if not (is_octet_stream and is_supported_extension):
            raise HTTPException(
                status_code=415,
                detail="Unsupported audio format. Use mp3, m4a, wav, webm, or ogg.",
            )

    # If content-type is missing, fallback to extension validation.
    if not normalized_content_type and not is_supported_extension:
        raise HTTPException(
            status_code=415,
            detail="Unsupported audio format. Use mp3, m4a, wav, webm, or ogg.",
        )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Accept a user message and return chatbot response using RAG with optional child context."""
    try:
        return _generate_chat_response(
            message=request.message,
            user_id=request.user_id or "anonymous",
            child_id=request.child_id,
            db=db,
            current_user=current_user,
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in chat endpoint: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@router.post("/chat/with-attachments", response_model=ChatWithAttachmentsResponse)
async def chat_with_attachments(
    files: List[UploadFile] = File(..., description="One or more images (PNG, JPEG, WebP, GIF) or PDFs"),
    message: str = Form("", description="User question; optional if you only want the model to review files"),
    user_id: Optional[str] = Form("anonymous"),
    child_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Chat with RAG + optional child context, sending images/PDFs to OpenRouter (multimodal)."""
    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required")
    if len(files) > MAX_CHAT_ATTACHMENTS:
        raise HTTPException(
            status_code=400,
            detail=f"Too many attachments. Maximum is {MAX_CHAT_ATTACHMENTS} files per request.",
        )

    try:
        parsed: List[Tuple[Literal["image", "pdf"], str, bytes, Optional[str]]] = []
        for i, upload in enumerate(files):
            raw = await upload.read()
            parsed.append(_validate_chat_attachment_file(upload, raw, index=i))

        return _generate_chat_response_with_attachments(
            message=message or None,
            parsed_files=parsed,
            user_id=user_id or "anonymous",
            child_id=child_id,
            db=db,
            current_user=current_user,
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        print(f"ERROR in chat with attachments: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}") from e


@router.post("/chat/voice", response_model=VoiceChatResponse)
async def chat_with_voice(
    audio: UploadFile = File(...),
    user_id: Optional[str] = Form("anonymous"),
    child_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accept an audio question, transcribe it, and run it through the chatbot flow."""
    try:
        audio_bytes = await audio.read()
        _validate_audio_upload(audio, audio_bytes)

        transcription = transcribe_audio_bytes(audio.filename, audio_bytes)
        chat_response = _generate_chat_response(
            message=transcription,
            user_id=user_id or "anonymous",
            child_id=child_id,
            db=db,
            current_user=current_user,
        )
        return VoiceChatResponse(
            response=chat_response.response,
            user_id=chat_response.user_id,
            transcription=transcription,
            filename=audio.filename,
        )
    except HTTPException:
        raise
    except RuntimeError as exc:
        import traceback
        tb = traceback.format_exc()
        print(f"ERROR in voice chat endpoint (runtime): {tb}")
        # Return a concise representation of the error to the client for debugging
        detail = str(exc)
        raise HTTPException(status_code=503, detail=(detail if len(detail) < 1000 else detail[:1000])) from exc
    except Exception as exc:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in voice chat endpoint: {error_details}")
        # Send a short error repr to client to help debug
        raise HTTPException(status_code=500, detail=repr(exc)) from exc

@router.get("/chat/history", response_model=ChatHistoryResponse)
async def chat_history(
    child_id: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return chat history for the current user.

    If child_id is provided, verify parent owns the child. Otherwise return general advice messages.
    """
    # Child ownership check (if requested)
    if child_id is not None:
        child = db.query(Child).filter(Child.id == child_id).first()
        if not child:
            raise HTTPException(status_code=404, detail="Child not found")
        if current_user.user_type == "parent" and child.parent_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied to this child's data")

    messages = list_messages_for_user(db, user_id=current_user.id, child_id=child_id, limit=limit)
    # Map ORM to schema
    schema_messages = [
        ChatMessage(role=m.role, content=m.content, created_at=m.created_at, child_id=m.child_id)
        for m in messages
    ]
    return ChatHistoryResponse(messages=schema_messages)

