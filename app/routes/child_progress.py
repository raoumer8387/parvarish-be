"""Child Progress Dashboard API routes.

Comprehensive endpoint for tracking child progress across all activities:
- Behavior tracking and daily check-ins
- Game performance and analysis
- Task completion and generation
- Overall progress metrics and insights
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone
import logging

from app.db.session import get_db
from app.core.security import get_current_user
from app.db.models.user import User
from app.db.models.child import Child
from app.db.models.behavior_models import ChildBehaviorResponse
from app.db.models.game_results import ChildGameResult
from app.db.models.child_task import ChildTask
from app.services.behavior_service import get_child_behavior_stats
from app.schemas.child_progress import ChildProgressDashboard, AllChildrenOverview

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/child-progress", tags=["child-progress"])


def _ensure_timezone_aware(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware, assuming UTC if naive."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _assert_parent_owns_child(db: Session, user: User, child_id: int) -> Child:
    """Ensure the authenticated parent owns the child."""
    if user.user_type != "parent":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only parents can access child progress"
        )
    
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Child not found"
        )
    
    if child.parent_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You do not have access to this child"
        )
    
    return child


@router.get("/{child_id}/dashboard", response_model=ChildProgressDashboard)
def get_child_progress_dashboard(
    child_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive progress dashboard for a specific child.
    
    Returns:
    - Child basic info
    - Behavior tracking summary
    - Game performance metrics
    - Task completion status
    - Overall progress insights
    - Recent activity timeline
    """
    child = _assert_parent_owns_child(db, current_user, child_id)
    
    # Calculate date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # === CHILD BASIC INFO ===
    child_info = {
        "id": child.id,
        "name": child.name,
        "age": child.age,
        "gender": child.gender,
        "school": child.school,
        "class_name": child.class_name,
        "temperament": child.temperament,
        "created_at": _ensure_timezone_aware(child.created_at).isoformat() if hasattr(child, 'created_at') and child.created_at else None
    }
    
    # === BEHAVIOR TRACKING SUMMARY ===
    behavior_stats = get_child_behavior_stats(db, child_id, days=days)
    
    # Get recent behavior responses
    recent_responses = (
        db.query(ChildBehaviorResponse)
        .filter(
            ChildBehaviorResponse.child_id == child_id,
            ChildBehaviorResponse.timestamp >= start_date
        )
        .order_by(desc(ChildBehaviorResponse.timestamp))
        .limit(10)
        .all()
    )
    
    # Check-in status
    last_response = (
        db.query(ChildBehaviorResponse)
        .filter(ChildBehaviorResponse.child_id == child_id)
        .order_by(desc(ChildBehaviorResponse.timestamp))
        .first()
    )
    
    hours_since_checkin = None
    needs_checkin = True
    if last_response and last_response.timestamp:
        last_ts = _ensure_timezone_aware(last_response.timestamp)
        hours_since_checkin = (end_date - last_ts).total_seconds() / 3600
        needs_checkin = hours_since_checkin >= 24
    
    behavior_summary = {
        "stats": behavior_stats,
        "last_check_in": _ensure_timezone_aware(last_response.timestamp).isoformat() if last_response and last_response.timestamp else None,
        "hours_since_last_check_in": round(hours_since_checkin, 1) if hours_since_checkin else None,
        "needs_check_in": needs_checkin,
        "recent_responses_count": len(recent_responses),
        "total_responses_period": len(recent_responses)
    }
    
    # === GAME PERFORMANCE METRICS ===
    game_results = (
        db.query(ChildGameResult)
        .filter(
            ChildGameResult.child_id == child_id,
            ChildGameResult.created_at >= start_date
        )
        .order_by(desc(ChildGameResult.created_at))
        .all()
    )
    
    # Aggregate game performance by type
    game_performance = {}
    game_categories = {}
    
    for result in game_results:
        game_type = result.game_type
        if game_type not in game_performance:
            game_performance[game_type] = {
                "total_sessions": 0,
                "avg_scores": {},
                "recent_scores": [],
                "improvement_trend": None
            }
        
        game_performance[game_type]["total_sessions"] += 1
        
        # Process analysis scores
        if result.analysis_score:
            for category, score in result.analysis_score.items():
                try:
                    score_val = float(score)
                    if category not in game_performance[game_type]["avg_scores"]:
                        game_performance[game_type]["avg_scores"][category] = []
                    game_performance[game_type]["avg_scores"][category].append(score_val)
                    
                    # Track for overall category performance
                    if category not in game_categories:
                        game_categories[category] = []
                    game_categories[category].append(score_val)
                except (ValueError, TypeError):
                    continue
        
        # Keep recent scores for trend analysis
        if len(game_performance[game_type]["recent_scores"]) < 5:
            total_score = sum(float(v) for v in result.analysis_score.values() if isinstance(v, (int, float))) if result.analysis_score else 0
            game_performance[game_type]["recent_scores"].append({
                "date": _ensure_timezone_aware(result.created_at).isoformat(),
                "total_score": total_score
            })
    
    # Calculate averages and trends
    for game_type in game_performance:
        for category in game_performance[game_type]["avg_scores"]:
            scores = game_performance[game_type]["avg_scores"][category]
            if len(scores) > 0:
                game_performance[game_type]["avg_scores"][category] = round(sum(scores) / len(scores), 1)
        
        # Simple trend calculation (comparing first half vs second half of recent scores)
        recent = game_performance[game_type]["recent_scores"]
        if len(recent) >= 4:
            mid = len(recent) // 2
            first_half_sum = sum(s["total_score"] for s in recent[:mid])
            second_half_sum = sum(s["total_score"] for s in recent[mid:])
            
            # Avoid division by zero
            if mid > 0 and (len(recent) - mid) > 0:
                first_half_avg = first_half_sum / mid
                second_half_avg = second_half_sum / (len(recent) - mid)
                
                if second_half_avg > first_half_avg * 1.1:
                    game_performance[game_type]["improvement_trend"] = "improving"
                elif second_half_avg < first_half_avg * 0.9:
                    game_performance[game_type]["improvement_trend"] = "declining"
                else:
                    game_performance[game_type]["improvement_trend"] = "stable"
            else:
                game_performance[game_type]["improvement_trend"] = "stable"
        else:
            game_performance[game_type]["improvement_trend"] = "stable"
    
    # Overall category strengths and weaknesses
    category_averages = {}
    for category, scores in game_categories.items():
        if scores:
            category_averages[category] = round(sum(scores) / len(scores), 1)
    
    strongest_category = max(category_averages.items(), key=lambda x: x[1])[0] if category_averages else None
    weakest_category = min(category_averages.items(), key=lambda x: x[1])[0] if category_averages else None
    
    games_summary = {
        "total_sessions": len(game_results),
        "games_played": list(game_performance.keys()),
        "performance_by_game": game_performance,
        "category_averages": category_averages,
        "strongest_category": strongest_category,
        "weakest_category": weakest_category,
        "last_game_date": _ensure_timezone_aware(game_results[0].created_at).isoformat() if game_results else None
    }
    
    # === TASK COMPLETION STATUS ===
    tasks = (
        db.query(ChildTask)
        .filter(
            ChildTask.child_id == child_id,
            ChildTask.created_at >= start_date
        )
        .order_by(desc(ChildTask.created_at))
        .all()
    )
    
    completed_tasks = [t for t in tasks if t.status == "completed"]
    pending_tasks = [t for t in tasks if t.status == "pending"]
    
    # Task categories analysis
    task_categories = {}
    for task in tasks:
        category = task.category or "general"
        if category not in task_categories:
            task_categories[category] = {"total": 0, "completed": 0}
        task_categories[category]["total"] += 1
        if task.status == "completed":
            task_categories[category]["completed"] += 1
    
    # Calculate completion rates
    for category in task_categories:
        total = task_categories[category]["total"]
        completed = task_categories[category]["completed"]
        task_categories[category]["completion_rate"] = round((completed / total) * 100, 1) if total > 0 else 0
    
    tasks_summary = {
        "total_tasks": len(tasks),
        "completed_tasks": len(completed_tasks),
        "pending_tasks": len(pending_tasks),
        "completion_rate": round((len(completed_tasks) / len(tasks)) * 100, 1) if tasks else 0,
        "categories": task_categories,
        "recent_tasks": [
            {
                "id": t.id,
                "title": t.title,
                "category": t.category,
                "status": t.status,
                "created_at": _ensure_timezone_aware(t.created_at).isoformat(),
                "completed_at": t.meta.get("completed_at") if t.meta else None
            }
            for t in tasks[:5]
        ]
    }
    
    # === OVERALL PROGRESS INSIGHTS ===
    # Calculate overall engagement score
    engagement_factors = []
    
    # Behavior engagement (responses in last 7 days)
    recent_behavior = (
        db.query(ChildBehaviorResponse)
        .filter(
            ChildBehaviorResponse.child_id == child_id,
            ChildBehaviorResponse.timestamp >= end_date - timedelta(days=7)
        )
        .count()
    )
    engagement_factors.append(min(recent_behavior * 20, 100))  # Max 5 responses = 100%
    
    # Game engagement (sessions in last 7 days)
    recent_games = (
        db.query(ChildGameResult)
        .filter(
            ChildGameResult.child_id == child_id,
            ChildGameResult.created_at >= end_date - timedelta(days=7)
        )
        .count()
    )
    engagement_factors.append(min(recent_games * 25, 100))  # Max 4 sessions = 100%
    
    # Task completion rate
    if tasks:
        engagement_factors.append((len(completed_tasks) / len(tasks)) * 100)
    
    overall_engagement = round(sum(engagement_factors) / len(engagement_factors), 1) if engagement_factors else 0
    
    # Progress insights
    insights = []
    
    if needs_checkin:
        insights.append({
            "type": "attention",
            "message": f"{child.name} needs a daily behavior check-in",
            "action": "behavior_checkin"
        })
    
    if overall_engagement < 50:
        insights.append({
            "type": "concern",
            "message": f"{child.name}'s engagement is low this week",
            "action": "increase_engagement"
        })
    
    if weakest_category and category_averages.get(weakest_category, 0) < 60:
        insights.append({
            "type": "improvement",
            "message": f"Focus on {weakest_category} development through targeted activities",
            "action": "targeted_tasks"
        })
    
    if len(pending_tasks) > 5:
        insights.append({
            "type": "tasks",
            "message": f"{len(pending_tasks)} pending tasks - consider reviewing difficulty",
            "action": "review_tasks"
        })
    
    progress_insights = {
        "overall_engagement_score": overall_engagement,
        "insights": insights,
        "recommendations": _generate_recommendations(child, behavior_stats, games_summary, tasks_summary)
    }
    
    # === RECENT ACTIVITY TIMELINE ===
    timeline = []
    
    # Add recent behavior responses
    for response in recent_responses[:3]:
        timeline.append({
            "type": "behavior",
            "date": _ensure_timezone_aware(response.timestamp).isoformat(),
            "title": "Behavior Check-in",
            "description": f"Answered: {response.question_text[:50]}...",
            "score": response.score
        })
    
    # Add recent games
    for game in game_results[:3]:
        total_score = sum(float(v) for v in game.analysis_score.values() if isinstance(v, (int, float))) if game.analysis_score else 0
        timeline.append({
            "type": "game",
            "date": _ensure_timezone_aware(game.created_at).isoformat(),
            "title": f"{game.game_type.replace('_', ' ').title()} Game",
            "description": f"Completed {game.game_type} session",
            "score": round(total_score, 1)
        })
    
    # Add recent completed tasks
    for task in completed_tasks[:3]:
        task_date = task.meta.get("completed_at") if task.meta else None
        if task_date and isinstance(task_date, str):
            # If it's already a string, use it directly
            date_str = task_date
        else:
            # If it's a datetime object, ensure timezone awareness
            date_obj = task_date if task_date else task.created_at
            date_str = _ensure_timezone_aware(date_obj).isoformat()
        
        timeline.append({
            "type": "task",
            "date": date_str,
            "title": f"Task Completed: {task.title}",
            "description": task.category or "General task",
            "score": None
        })
    
    # Sort timeline by date
    timeline.sort(key=lambda x: x["date"], reverse=True)
    
    return {
        "child_info": child_info,
        "period_days": days,
        "behavior_summary": behavior_summary,
        "games_summary": games_summary,
        "tasks_summary": tasks_summary,
        "progress_insights": progress_insights,
        "recent_activity": timeline[:10]
    }


def _generate_recommendations(child: Child, behavior_stats: Dict, games_summary: Dict, tasks_summary: Dict) -> List[Dict[str, str]]:
    """Generate personalized recommendations based on child's progress."""
    recommendations = []
    
    # Behavior-based recommendations
    if behavior_stats.get("avg_score", 0) < 60:
        recommendations.append({
            "category": "behavior",
            "title": "Focus on Daily Check-ins",
            "description": "Regular behavior tracking will help identify patterns and areas for improvement"
        })
    
    # Game-based recommendations
    if games_summary["total_sessions"] < 5:
        recommendations.append({
            "category": "games",
            "title": "Increase Game Activity",
            "description": "Educational games help develop cognitive and social skills in a fun way"
        })
    
    weakest = games_summary.get("weakest_category")
    if weakest:
        game_suggestions = {
            "cognitive": "memory and puzzle games",
            "social": "scenario-based games",
            "emotional": "mood and empathy games",
            "spiritual": "Islamic quiz games"
        }
        if weakest in game_suggestions:
            recommendations.append({
                "category": "games",
                "title": f"Strengthen {weakest.title()} Skills",
                "description": f"Try more {game_suggestions[weakest]} to improve in this area"
            })
    
    # Task-based recommendations
    if tasks_summary["completion_rate"] < 70:
        recommendations.append({
            "category": "tasks",
            "title": "Review Task Difficulty",
            "description": "Consider adjusting task complexity to match child's current level"
        })
    
    # Age-specific recommendations
    age = child.age or 8
    if age <= 8:
        recommendations.append({
            "category": "development",
            "title": "Focus on Basic Skills",
            "description": "Emphasize fundamental social and emotional development through play"
        })
    elif age <= 11:
        recommendations.append({
            "category": "development",
            "title": "Build Independence",
            "description": "Encourage self-directed learning and responsibility through structured tasks"
        })
    else:
        recommendations.append({
            "category": "development",
            "title": "Develop Critical Thinking",
            "description": "Challenge with complex scenarios and moral reasoning exercises"
        })
    
    return recommendations[:4]  # Limit to 4 recommendations


@router.get("/overview", response_model=AllChildrenOverview)
def get_all_children_overview(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get overview of all children's progress for the parent dashboard.
    
    Returns summary metrics for each child including:
    - Basic info
    - Recent activity counts
    - Engagement status
    - Alerts/notifications
    """
    if current_user.user_type != "parent":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can access children overview"
        )
    
    children = db.query(Child).filter(Child.parent_id == current_user.id).all()
    
    if not children:
        return {
            "total_children": 0,
            "children": [],
            "summary": {
                "total_activities": 0,
                "children_needing_attention": 0,
                "overall_engagement": 0
            }
        }
    
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    children_overview = []
    total_activities = 0
    children_needing_attention = 0
    engagement_scores = []
    
    for child in children:
        # Count recent activities
        behavior_count = (
            db.query(ChildBehaviorResponse)
            .filter(
                ChildBehaviorResponse.child_id == child.id,
                ChildBehaviorResponse.timestamp >= start_date
            )
            .count()
        )
        
        game_count = (
            db.query(ChildGameResult)
            .filter(
                ChildGameResult.child_id == child.id,
                ChildGameResult.created_at >= start_date
            )
            .count()
        )
        
        task_count = (
            db.query(ChildTask)
            .filter(
                ChildTask.child_id == child.id,
                ChildTask.created_at >= start_date
            )
            .count()
        )
        
        completed_tasks = (
            db.query(ChildTask)
            .filter(
                ChildTask.child_id == child.id,
                ChildTask.created_at >= start_date,
                ChildTask.status == "completed"
            )
            .count()
        )
        
        # Check if needs attention
        last_behavior = (
            db.query(ChildBehaviorResponse)
            .filter(ChildBehaviorResponse.child_id == child.id)
            .order_by(desc(ChildBehaviorResponse.timestamp))
            .first()
        )
        
        needs_checkin = True
        if last_behavior and last_behavior.timestamp:
            last_ts = _ensure_timezone_aware(last_behavior.timestamp)
            hours_since = (end_date - last_ts).total_seconds() / 3600
            needs_checkin = hours_since >= 24
        
        if needs_checkin:
            children_needing_attention += 1
        
        # Calculate engagement score
        activity_score = min((behavior_count + game_count + task_count) * 10, 100)
        completion_rate = (completed_tasks / task_count * 100) if task_count > 0 else 100
        engagement_score = (activity_score + completion_rate) / 2
        engagement_scores.append(engagement_score)
        
        total_activities += behavior_count + game_count + task_count
        
        children_overview.append({
            "id": child.id,
            "name": child.name,
            "age": child.age,
            "recent_activities": {
                "behavior_responses": behavior_count,
                "games_played": game_count,
                "tasks_assigned": task_count,
                "tasks_completed": completed_tasks
            },
            "engagement_score": round(engagement_score, 1),
            "needs_attention": needs_checkin,
            "last_activity": _ensure_timezone_aware(last_behavior.timestamp).isoformat() if last_behavior and last_behavior.timestamp else None
        })
    
    overall_engagement = round(sum(engagement_scores) / len(engagement_scores), 1) if engagement_scores else 0
    
    return {
        "total_children": len(children),
        "children": children_overview,
        "summary": {
            "total_activities": total_activities,
            "children_needing_attention": children_needing_attention,
            "overall_engagement": overall_engagement,
            "period_days": days
        }
    }