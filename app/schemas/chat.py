"""Chat-related schemas.

Defines Pydantic models for chat messages and history responses.
"""

from pydantic import BaseModel
from typing import List, Literal, Optional
from datetime import datetime


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str
    created_at: Optional[datetime] = None
    child_id: Optional[int] = None


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


class ChatResponse(BaseModel):
    reply: str


class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessage]
