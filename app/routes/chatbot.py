"""Chatbot routes for Parvarish AI.

Expose endpoints for sending user messages and retrieving bot responses using RAG.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.rag.data_loader import DataLoader
from app.rag.embedder import Embedder, VectorStoreConfig
from app.rag.retriever import Retriever
from app.services.llm_client import generate_response

router = APIRouter(prefix="/api", tags=["chatbot"])

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
async def chat(request: ChatRequest):
    """Accept a user message and return chatbot response using RAG."""
    try:
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Get retriever
        retriever = get_retriever()
        
        # Retrieve relevant context
        chunks = retriever.query(request.message, k=2)
        context = Retriever.format_context(chunks) if chunks else "No specific references found in the database."
        
        # Limit context length
        max_context_length = 1200
        if len(context) > max_context_length:
            context = context[:max_context_length] + "\n[Context truncated...]"
        
        # Build prompt
        full_prompt = f"""{SYSTEM_PROMPT}

Here are relevant Islamic references to help answer the question:

{context}

Question: {request.message}

Provide a SHORT answer (3-4 paragraphs max) with:
1. One key Islamic principle from the references
2. Brief practical advice (2-3 actionable tips)

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
        
        return ChatResponse(
            response=answer,
            user_id=request.user_id
        )
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in chat endpoint: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

