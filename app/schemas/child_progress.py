"""Pydantic schemas for child progress dashboard."""

from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime


class ChildInfo(BaseModel):
    """Basic child information."""
    id: int
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    school: Optional[str] = None
    class_name: Optional[str] = None
    temperament: Optional[str] = None
    created_at: Optional[str] = None


class BehaviorSummary(BaseModel):
    """Child behavior tracking summary."""
    stats: Dict[str, Any]
    last_check_in: Optional[str] = None
    hours_since_last_check_in: Optional[float] = None
    needs_check_in: bool
    recent_responses_count: int
    total_responses_period: int


class GamePerformance(BaseModel):
    """Game performance metrics for a specific game type."""
    total_sessions: int
    avg_scores: Dict[str, float]
    recent_scores: List[Dict[str, Any]]
    improvement_trend: Optional[str] = None


class GamesSummary(BaseModel):
    """Overall games performance summary."""
    total_sessions: int
    games_played: List[str]
    performance_by_game: Dict[str, GamePerformance]
    category_averages: Dict[str, float]
    strongest_category: Optional[str] = None
    weakest_category: Optional[str] = None
    last_game_date: Optional[str] = None


class TaskCategory(BaseModel):
    """Task completion metrics by category."""
    total: int
    completed: int
    completion_rate: float


class RecentTask(BaseModel):
    """Recent task information."""
    id: int
    title: str
    category: Optional[str] = None
    status: str
    created_at: str
    completed_at: Optional[str] = None


class TasksSummary(BaseModel):
    """Tasks completion summary."""
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    completion_rate: float
    categories: Dict[str, TaskCategory]
    recent_tasks: List[RecentTask]


class ProgressInsight(BaseModel):
    """Individual progress insight."""
    type: str  # attention, concern, improvement, tasks
    message: str
    action: str


class Recommendation(BaseModel):
    """Progress recommendation."""
    category: str
    title: str
    description: str


class ProgressInsights(BaseModel):
    """Overall progress insights and recommendations."""
    overall_engagement_score: float
    insights: List[ProgressInsight]
    recommendations: List[Recommendation]


class ActivityTimelineItem(BaseModel):
    """Recent activity timeline item."""
    type: str  # behavior, game, task
    date: str
    title: str
    description: str
    score: Optional[float] = None


class ChildProgressDashboard(BaseModel):
    """Complete child progress dashboard response."""
    child_info: ChildInfo
    period_days: int
    behavior_summary: BehaviorSummary
    games_summary: GamesSummary
    tasks_summary: TasksSummary
    progress_insights: ProgressInsights
    recent_activity: List[ActivityTimelineItem]


class ChildOverviewItem(BaseModel):
    """Individual child overview for parent dashboard."""
    id: int
    name: str
    age: Optional[int] = None
    recent_activities: Dict[str, int]
    engagement_score: float
    needs_attention: bool
    last_activity: Optional[str] = None


class OverviewSummary(BaseModel):
    """Summary statistics for all children."""
    total_activities: int
    children_needing_attention: int
    overall_engagement: float
    period_days: int


class AllChildrenOverview(BaseModel):
    """Overview of all children for parent dashboard."""
    total_children: int
    children: List[ChildOverviewItem]
    summary: OverviewSummary