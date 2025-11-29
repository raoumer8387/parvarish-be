"""Chatbot routes for Parvarish AI.

Expose endpoints for sending user messages and retrieving bot responses using RAG.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

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

router = APIRouter(tags=["chatbot"])

# Initialize RAG components (singleton pattern)
_retriever = None

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


SYSTEM_PROMPT = (
    "You are Parvarish AI â€” an Islamic parenting companion. "
    "Your role is to guide parents with wisdom and compassion based on authentic Islamic teachings. "
    "Use only the provided Quranic verses, Hadith, and Prophet (PBUH) stories to offer advice about raising children, behavior, and moral development. "
    "Speak gently and respectfully, maintaining an educational and empathetic tone. "
    "If no relevant reference is found in the given data, respond politely that you currently do not have Islamic guidance on that specific topic. Do not speculate or invent information. "
    "Provide SHORT, concise answers (1-2 paragraphs maximum). Focus on actionable advice. Be brief and direct."
)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Accept a user message and return chatbot response using RAG with optional child context."""
    try:
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Build child context if child_id provided
        child_context = ""
        if request.child_id:
            child = db.query(Child).filter(Child.id == request.child_id).first()
            if child:
                # Verify parent owns this child
                if current_user.user_type == "parent" and child.parent_id != current_user.id:
                    raise HTTPException(status_code=403, detail="Access denied to this child's data")
                
                # Get behavior stats
                stats = get_child_behavior_stats(db, request.child_id, days=30)
                
                child_context = f"""
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
        
        # Get retriever
        retriever = get_retriever()
        
        # Retrieve relevant context
        chunks = retriever.query(request.message, k=2)
        context = Retriever.format_context(chunks) if chunks else "No specific references found in the database."
        
        # Limit context length
        max_context_length = 1200
        if len(context) > max_context_length:
            context = context[:max_context_length] + "\n[Context truncated...]"
        
        # Build prompt with child context
        full_prompt = f"""{SYSTEM_PROMPT}
{child_context}

Here are relevant Islamic references to help answer the question:

{context}

Question: {request.message}

Provide a SHORT answer (3-4 paragraphs max) with:
1. One key Islamic principle from the references
2. Brief practical advice (2-3 actionable tips) {"SPECIFICALLY for " + child.name if request.child_id else ""}

IMPORTANT: When citing sources, include the FULL reference details from the [Source X: ...] headers above.
Examples:
- For Quran: "As Allah says in Quran 17:23..."
- For Hadith: "The Prophet (PBUH) said in Sahih Bukhari, Book 78, Hadith #5997..."
- Always mention the classification [Sahih/Hasan] if provided.

Keep it concise and parent-friendly."""
        
        messages = [
            {"role": "user", "content": full_prompt}
        ]
        # Get response from LLM
        answer = generate_response(messages)
        
        # Persist user message and assistant reply
        try:
            create_message(db, user_id=current_user.id, role="user", content=request.message, child_id=request.child_id)
            create_message(db, user_id=current_user.id, role="assistant", content=answer, child_id=request.child_id)
        except Exception as db_err:
            # Log but don't fail the response generation
            print(f"WARNING: Failed to persist chat messages: {db_err}")

        return ChatResponse(response=answer, user_id=request.user_id)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in chat endpoint: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

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

