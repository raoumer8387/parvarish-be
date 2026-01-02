"""Schemas for child activity history."""

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any


class GameActivityItem(BaseModel):
    """Individual game activity."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    game_type: str
    raw_result: Dict[str, Any]
    analysis_score: Dict[str, Any]
    created_at: datetime
    activity_type: str = "game"


class TaskActivityItem(BaseModel):
    """Individual task activity."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    description: str
    category: str
    xp_reward: int
    difficulty: int
    status: str
    source: str
    meta: Optional[Dict[str, Any]] = None
    created_at: datetime
    activity_type: str = "task"


class BehaviorActivityItem(BaseModel):
    """Individual behavior response activity."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    question_text: str
    answer: str
    score: int
    timestamp: datetime
    activity_type: str = "behavior"


class ChatActivityItem(BaseModel):
    """Individual chat message activity."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    role: str
    content: str
    created_at: datetime
    activity_type: str = "chat"


class ActivityHistoryResponse(BaseModel):
    """Comprehensive child activity history."""
    
    child_id: int
    child_name: str
    date_from: datetime
    date_to: datetime
    total_activities: int
    
    # Aggregated statistics
    stats: Dict[str, Any]
    
    # Activities grouped by type
    games: List[GameActivityItem]
    tasks: List[TaskActivityItem]
    behavior_responses: List[BehaviorActivityItem]
    chats: List[ChatActivityItem]
    
    # Combined timeline (optional - all activities sorted by date)
    timeline: List[Dict[str, Any]]


class ActivitySummary(BaseModel):
    """Summary of child's activity statistics."""
    
    total_games_played: int
    games_by_type: Dict[str, int]
    total_tasks: int
    tasks_completed: int
    tasks_pending: int
    tasks_by_category: Dict[str, int]
    total_behavior_responses: int
    average_behavior_score: float
    total_chat_messages: int
    most_active_day: Optional[str] = None
    xp_earned: int
