"""Chatbot routes for Parvarish AI.

Expose endpoints for sending user messages and retrieving bot responses using RAG.
"""

from fastapi import APIRouter, HTTPException, Depends, File, Form, UploadFile
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from pathlib import Path

from app.rag.data_loader import DataLoader
from app.rag.embedder import Embedder, VectorStoreConfig
from app.rag.retriever import Retriever
from app.services.llm_client import generate_response
from app.db.crud.message import create_message, list_messages_for_user
from app.schemas.chat import ChatHistoryResponse, ChatMessage
from app.db.session import get_db
from app.db.models.child import Child
from app.services.behavior_service import get_child_behavior_stats
from app.core.security import get_current_user
from app.db.models.user import User
from app.services.speech_to_text import transcribe_audio_bytes

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


SYSTEM_PROMPT = (
    "You are Parvarish AI – an Islamic parenting companion. "
    "Your role is to guide parents with wisdom and compassion based on authentic Islamic teachings. "
    "Use the provided Quranic verses, Hadith, Prophet (PBUH) stories, AND Islamic Scholar References (from classical books like Ihya Ulum ad-Din, Tafsir Ibn Kathir, Adab al-Mufrad, etc.) to offer advice about raising children, behavior, and moral development. "
    "MULTILINGUAL REQUIREMENT: Always provide your response in THREE languages: "
    "1. English (EN) "
    "2. Urdu (UR) "
    "3. Roman Urdu (RM) "
    "Format each language section clearly with headers. "
    "CITATION REQUIREMENT: When referencing Islamic scholars, ALWAYS include the book title and author name like: [Book Title – Author]. "
    "Example: 'As mentioned in Ihya Ulum ad-Din by Imam Al-Ghazali...' "
    "Speak gently and respectfully, maintaining an educational and empathetic tone. "
    "If no relevant reference is found in the given data, respond politely that you currently do not have Islamic guidance on that specific topic. Do not speculate or invent information. "
    "Provide SHORT, concise answers (1-2 paragraphs maximum PER LANGUAGE). Focus on actionable advice. Be brief and direct."
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


def _build_prompt(message: str, child_context: str, child_id: Optional[int], db: Session) -> str:
    """Construct the full prompt for the LLM."""
    retriever = get_retriever()
    chunks = retriever.query(message, k=8)
    context = Retriever.format_context(chunks) if chunks else "No specific references found in the database."

    max_context_length = 2000
    if len(context) > max_context_length:
        context = context[:max_context_length] + "\n[Context truncated...]"

    child_name = None
    if child_id:
        child = db.query(Child).filter(Child.id == child_id).first()
        child_name = child.name if child else None

    return f"""{SYSTEM_PROMPT}
{child_context}

Here are relevant Islamic references to help answer the question:

{context}

Question: {message}

Provide your answer in THREE LANGUAGES (English, Urdu, Roman Urdu) with clear section headers:

## English (EN):
[Provide 2-3 paragraphs with key Islamic principle and 2-3 actionable tips {"SPECIFICALLY for " + child_name if child_name else ""}]

## Urdu (UR):
[Same content in Urdu script]

## Roman Urdu (RM):
[Same content in Roman Urdu]

CITATION REQUIREMENTS:
- For Quran: "As Allah says in Quran 17:23..."
- For Hadith: "The Prophet (PBUH) said in Sahih Bukhari, Book 78, Hadith #5997..." (include classification [Sahih/Hasan] if provided)
- For Scholar References: "As mentioned in [Book Title] by [Author]..." or "[Author] writes in [Book Title]..."
- ALWAYS include the FULL reference details from the [Source X: ...] headers above.
- PRIORITY: Try to use AT LEAST ONE reference from each source type (Quran/Hadith, Scholars, Stories) if available in the context above.

Keep each language section concise and parent-friendly."""


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
    full_prompt = _build_prompt(message, child_context, child_id, db)
    answer = generate_response([{"role": "user", "content": full_prompt}])

    try:
        create_message(db, user_id=current_user.id, role="user", content=message, child_id=child_id)
        create_message(db, user_id=current_user.id, role="assistant", content=answer, child_id=child_id)
    except Exception as db_err:
        print(f"WARNING: Failed to persist chat messages: {db_err}")

    return ChatResponse(response=answer, user_id=user_id)


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

