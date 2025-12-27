"""Pydantic schemas for lacking analysis and notifications."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class LackingArea(BaseModel):
    """Individual lacking area identified."""
    area: str
    label: str
    score: float
    priority: str  # high, medium, low
    game_type: str


class DetailedAnalysis(BaseModel):
    """Detailed analysis for a specific area."""
    score: Optional[float] = None
    status: str  # lacking, good, insufficient_data
    games_analyzed: int = 0
    details: Dict[str, Any] = {}


class LackingAnalysisResponse(BaseModel):
    """Complete lacking analysis response."""
    child_id: int
    child_name: str
    analysis_period_days: int
    total_games_played: int
    games_by_type: Dict[str, int]
    lacking_areas: List[LackingArea]
    detailed_analysis: Dict[str, DetailedAnalysis]
    requires_attention: bool
    analyzed_at: str


class TickerNotification(BaseModel):
    """Notification ticker for parent dashboard."""
    id: str
    child_id: int
    child_name: str
    lacking_area: str
    lacking_label: str
    score: float
    priority: str
    message: str
    action_required: bool
    created_at: str
    read: bool = False


class LackingGuidanceRequest(BaseModel):
    """Request for Islamic guidance on lacking area."""
    child_id: int
    lacking_area: str


class LackingGuidanceResponse(BaseModel):
    """Response with Islamic guidance."""
    child_id: int
    child_name: str
    lacking_area: str
    lacking_label: str
    score: float
    guidance: str
    islamic_references_used: bool
    generated_at: str


class GenerateTasksRequest(BaseModel):
    """Request to generate Islamic tasks for lacking area."""
    child_id: int
    lacking_area: str
    num_tasks: int = Field(default=3, ge=1, le=5)


class GeneratedTask(BaseModel):
    """A generated task."""
    title: str
    description: str
    category: str
    difficulty: int
    xp_reward: int
    islamic_reference: Optional[str] = None


class GenerateTasksResponse(BaseModel):
    """Response with generated tasks."""
    child_id: int
    child_name: str
    lacking_area: str
    tasks: List[GeneratedTask]
    tasks_saved: bool
    generated_at: str


class NotificationListResponse(BaseModel):
    """List of notifications for parent."""
    notifications: List[TickerNotification]
    total_count: int
    unread_count: int


class ChildLackingSummary(BaseModel):
    """Summary of lacking areas for one child."""
    child_id: int
    child_name: str
    child_age: Optional[int] = None
    total_lackings: int
    lacking_areas: List[LackingArea]
    requires_attention: bool
    last_analyzed: str


class AllChildrenLackingResponse(BaseModel):
    """Response with lacking analysis for all children."""
    total_children: int
    children_with_lackings: int
    children: List[ChildLackingSummary]
    analyzed_at: str


class MarkNotificationReadRequest(BaseModel):
    """Request to mark notification as read."""
    notification_id: str


class TaskEvaluationData(BaseModel):
    """Data from task evaluation to feed back into lacking analysis."""
    task_id: int
    child_id: int
    category: str
    completed: bool
    quality_score: Optional[float] = Field(None, ge=0, le=100)
    completion_time_days: Optional[int] = None
    notes: Optional[str] = None
