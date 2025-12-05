"""Pydantic schemas for child task generation and responses."""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime


AllowedTaskStatus = Literal["pending", "completed"]
AllowedTaskSource = Literal["chatbot", "daily_question"]


class TaskFromChatRequest(BaseModel):
    """Input payload for generating tasks from a chatbot interaction."""
    child_id: int
    chatbot_response: str = Field(..., description="Full textual response produced by chatbot.")
    chatbot_tags: Optional[List[str]] = Field(None, description="Optional explicit categories derived by chatbot (override keyword extraction).")


class TaskFromScoresRequest(BaseModel):
    """Input for generating tasks purely from recent behavior scores."""
    child_id: int
    days: int = 3
    max_tasks: int = 3


class ChildTaskOut(BaseModel):
    """Outgoing schema representing a created child task."""
    id: int
    child_id: int
    title: str
    description: str
    category: str
    xp_reward: int
    difficulty: int
    status: AllowedTaskStatus
    source: AllowedTaskSource
    meta: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TasksFromChatResponse(BaseModel):
    """Response returned after generating tasks from chat input."""
    count: int
    tasks: List[ChildTaskOut]
    categories_considered: List[str]
    categories_low_score: List[str]
    keywords_detected: List[str]


class ChildTaskListResponse(BaseModel):
    """List tasks for a child (for dashboard)."""
    child_id: int
    total: int
    tasks: List[ChildTaskOut]


class TaskCompleteResponse(BaseModel):
    """Return status after marking a task as completed."""
    task_id: int
    status: AllowedTaskStatus
    completed_at: datetime | None = None
