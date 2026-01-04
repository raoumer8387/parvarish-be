"""Child Activity History API routes.

Provides comprehensive activity tracking for the last 30 days including:
- Games played
- Tasks assigned and completed
- Behavior responses
- Chat interactions
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from typing import Optional
from datetime import datetime, timedelta, timezone
import logging

from app.db.session import get_db
from app.core.security import get_current_user
from app.db.models.user import User
from app.db.models.child import Child
from app.db.models.behavior_models import ChildBehaviorResponse
from app.db.models.game_results import ChildGameResult
from app.db.models.child_task import ChildTask
from app.db.models.message import Message
from app.schemas.activity_history import (
    ActivityHistoryResponse,
    ActivitySummary,
    GameActivityItem,
    TaskActivityItem,
    BehaviorActivityItem,
    ChatActivityItem,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/activity-history", tags=["activity-history"])


def _ensure_timezone_aware(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware, assuming UTC if naive."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _verify_child_access(db: Session, user: User, child_id: int) -> Child:
    """Verify that the user has access to the child's data.
    
    Parents can access their own children.
    Children can access their own data.
    """
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found"
        )
    
    # Parent accessing their child
    if user.user_type == "parent":
        if child.parent_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this child's data"
            )
    # Child accessing their own data
    elif user.user_type == "child":
        if child.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own activity history"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid user type"
        )
    
    return child


@router.get("/{child_id}", response_model=ActivityHistoryResponse)
def get_child_activity_history(
    child_id: int,
    days: int = Query(default=30, ge=1, le=90, description="Number of days to fetch history (1-90)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get comprehensive activity history for a child for the specified number of days.
    
    Accessible by:
    - Parents: Can view their children's activity
    - Children: Can view their own activity
    """
    # Verify access
    child = _verify_child_access(db, current_user, child_id)
    
    # Calculate date range
    now = datetime.now(timezone.utc)
    date_from = now - timedelta(days=days)
    
    # Fetch games played
    games = db.query(ChildGameResult).filter(
        and_(
            ChildGameResult.child_id == child_id,
            ChildGameResult.created_at >= date_from
        )
    ).order_by(desc(ChildGameResult.created_at)).all()
    
    # Fetch tasks
    tasks = db.query(ChildTask).filter(
        and_(
            ChildTask.child_id == child_id,
            ChildTask.created_at >= date_from
        )
    ).order_by(desc(ChildTask.created_at)).all()
    
    # Fetch behavior responses
    behavior_responses = db.query(ChildBehaviorResponse).filter(
        and_(
            ChildBehaviorResponse.child_id == child_id,
            ChildBehaviorResponse.timestamp >= date_from
        )
    ).order_by(desc(ChildBehaviorResponse.timestamp)).all()
    
    # Fetch chat messages (only child's messages or messages related to the child)
    chats = db.query(Message).filter(
        and_(
            Message.child_id == child_id,
            Message.created_at >= date_from
        )
    ).order_by(desc(Message.created_at)).all()
    
    # Convert to response models
    game_items = [
        GameActivityItem(
            id=str(g.id),
            game_type=g.game_type,
            raw_result=g.raw_result,
            analysis_score=g.analysis_score,
            created_at=_ensure_timezone_aware(g.created_at),
        )
        for g in games
    ]
    
    task_items = [
        TaskActivityItem(
            id=t.id,
            title=t.title,
            description=t.description,
            category=t.category,
            xp_reward=t.xp_reward,
            difficulty=t.difficulty,
            status=t.status,
            source=t.source,
            meta=t.meta,
            created_at=_ensure_timezone_aware(t.created_at),
        )
        for t in tasks
    ]
    
    behavior_items = [
        BehaviorActivityItem(
            id=b.id,
            question_text=b.question_text,
            answer=b.answer,
            score=b.score,
            timestamp=_ensure_timezone_aware(b.timestamp),
        )
        for b in behavior_responses
    ]
    
    chat_items = [
        ChatActivityItem(
            id=c.id,
            role=c.role,
            content=c.content,
            created_at=_ensure_timezone_aware(c.created_at),
        )
        for c in chats
    ]
    
    # Calculate statistics
    total_games = len(games)
    games_by_type = {}
    for game in games:
        game_type = game.game_type
        games_by_type[game_type] = games_by_type.get(game_type, 0) + 1
    
    total_tasks = len(tasks)
    tasks_completed = sum(1 for t in tasks if t.status == "completed")
    tasks_pending = total_tasks - tasks_completed
    tasks_by_category = {}
    xp_earned = 0
    for task in tasks:
        tasks_by_category[task.category] = tasks_by_category.get(task.category, 0) + 1
        if task.status == "completed":
            xp_earned += task.xp_reward
    
    total_behavior_responses = len(behavior_responses)
    avg_behavior_score = (
        sum(b.score for b in behavior_responses) / total_behavior_responses
        if total_behavior_responses > 0
        else 0.0
    )
    
    total_chat_messages = len(chats)
    
    # Find most active day
    activity_by_day = {}
    for game in games:
        day = _ensure_timezone_aware(game.created_at).date().isoformat()
        activity_by_day[day] = activity_by_day.get(day, 0) + 1
    for task in tasks:
        day = _ensure_timezone_aware(task.created_at).date().isoformat()
        activity_by_day[day] = activity_by_day.get(day, 0) + 1
    for behavior in behavior_responses:
        day = _ensure_timezone_aware(behavior.timestamp).date().isoformat()
        activity_by_day[day] = activity_by_day.get(day, 0) + 1
    for chat in chats:
        day = _ensure_timezone_aware(chat.created_at).date().isoformat()
        activity_by_day[day] = activity_by_day.get(day, 0) + 1
    
    most_active_day = max(activity_by_day.items(), key=lambda x: x[1])[0] if activity_by_day else None
    
    # Build combined timeline
    timeline = []
    
    for game in game_items:
        timeline.append({
            "timestamp": game.created_at,
            "type": "game",
            "data": game.model_dump(),
        })
    
    for task in task_items:
        timeline.append({
            "timestamp": task.created_at,
            "type": "task",
            "data": task.model_dump(),
        })
    
    for behavior in behavior_items:
        timeline.append({
            "timestamp": behavior.timestamp,
            "type": "behavior",
            "data": behavior.model_dump(),
        })
    
    for chat in chat_items:
        timeline.append({
            "timestamp": chat.created_at,
            "type": "chat",
            "data": chat.model_dump(),
        })
    
    # Sort timeline by timestamp (most recent first)
    timeline.sort(key=lambda x: x["timestamp"], reverse=True)
    
    total_activities = len(timeline)
    
    # Build statistics object
    stats = ActivitySummary(
        total_games_played=total_games,
        games_by_type=games_by_type,
        total_tasks=total_tasks,
        tasks_completed=tasks_completed,
        tasks_pending=tasks_pending,
        tasks_by_category=tasks_by_category,
        total_behavior_responses=total_behavior_responses,
        average_behavior_score=round(avg_behavior_score, 2),
        total_chat_messages=total_chat_messages,
        most_active_day=most_active_day,
        xp_earned=xp_earned,
    ).model_dump()
    
    return ActivityHistoryResponse(
        child_id=child_id,
        child_name=child.name,
        date_from=date_from,
        date_to=now,
        total_activities=total_activities,
        stats=stats,
        games=game_items,
        tasks=task_items,
        behavior_responses=behavior_items,
        chats=chat_items,
        timeline=timeline,
    )


@router.get("/{child_id}/summary", response_model=ActivitySummary)
def get_child_activity_summary(
    child_id: int,
    days: int = Query(default=30, ge=1, le=90, description="Number of days for summary (1-90)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a summary of child's activity statistics for the specified period.
    
    Lighter endpoint that returns only aggregated statistics without full activity details.
    """
    # Verify access
    child = _verify_child_access(db, current_user, child_id)
    
    # Calculate date range
    now = datetime.now(timezone.utc)
    date_from = now - timedelta(days=days)
    
    # Aggregate games
    games = db.query(ChildGameResult).filter(
        and_(
            ChildGameResult.child_id == child_id,
            ChildGameResult.created_at >= date_from
        )
    ).all()
    
    total_games = len(games)
    games_by_type = {}
    for game in games:
        game_type = game.game_type
        games_by_type[game_type] = games_by_type.get(game_type, 0) + 1
    
    # Aggregate tasks
    tasks = db.query(ChildTask).filter(
        and_(
            ChildTask.child_id == child_id,
            ChildTask.created_at >= date_from
        )
    ).all()
    
    total_tasks = len(tasks)
    tasks_completed = sum(1 for t in tasks if t.status == "completed")
    tasks_pending = total_tasks - tasks_completed
    tasks_by_category = {}
    xp_earned = 0
    for task in tasks:
        tasks_by_category[task.category] = tasks_by_category.get(task.category, 0) + 1
        if task.status == "completed":
            xp_earned += task.xp_reward
    
    # Aggregate behavior responses
    behavior_responses = db.query(ChildBehaviorResponse).filter(
        and_(
            ChildBehaviorResponse.child_id == child_id,
            ChildBehaviorResponse.timestamp >= date_from
        )
    ).all()
    
    total_behavior_responses = len(behavior_responses)
    avg_behavior_score = (
        sum(b.score for b in behavior_responses) / total_behavior_responses
        if total_behavior_responses > 0
        else 0.0
    )
    
    # Count chat messages
    total_chat_messages = db.query(func.count(Message.id)).filter(
        and_(
            Message.child_id == child_id,
            Message.created_at >= date_from
        )
    ).scalar()
    
    # Find most active day
    activity_by_day = {}
    for game in games:
        day = _ensure_timezone_aware(game.created_at).date().isoformat()
        activity_by_day[day] = activity_by_day.get(day, 0) + 1
    for task in tasks:
        day = _ensure_timezone_aware(task.created_at).date().isoformat()
        activity_by_day[day] = activity_by_day.get(day, 0) + 1
    for behavior in behavior_responses:
        day = _ensure_timezone_aware(behavior.timestamp).date().isoformat()
        activity_by_day[day] = activity_by_day.get(day, 0) + 1
    
    most_active_day = max(activity_by_day.items(), key=lambda x: x[1])[0] if activity_by_day else None
    
    return ActivitySummary(
        total_games_played=total_games,
        games_by_type=games_by_type,
        total_tasks=total_tasks,
        tasks_completed=tasks_completed,
        tasks_pending=tasks_pending,
        tasks_by_category=tasks_by_category,
        total_behavior_responses=total_behavior_responses,
        average_behavior_score=round(avg_behavior_score, 2),
        total_chat_messages=total_chat_messages,
        most_active_day=most_active_day,
        xp_earned=xp_earned,
    )
