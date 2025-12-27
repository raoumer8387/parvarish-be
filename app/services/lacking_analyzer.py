"""Service for analyzing child's lacking areas based on game performance.

This module identifies specific lacking areas in children based on their game results:
- Memory Game → Presence of Mind
- Mood Picker → Mood Identification
- Islamic Quiz → Learning Capability
- Scenario Game → Behavior Identification

The analysis generates notifications for parents and triggers chatbot interactions
to provide Islamic-oriented guidance and task generation.
"""

from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
import logging

from app.db.models.game_results import ChildGameResult
from app.db.models.child import Child
from app.db.models.child_task import ChildTask

logger = logging.getLogger(__name__)

# Thresholds for identifying lacking areas (0-100 scale)
LACKING_THRESHOLDS = {
    "presence_of_mind": 60,      # Memory game
    "mood_identification": 60,    # Mood picker
    "learning_capability": 65,    # Islamic quiz
    "behavior_identification": 60 # Scenario game
}

# Minimum games required for analysis
MIN_GAMES_FOR_ANALYSIS = {
    "memory": 2,
    "mood": 3,
    "scenario": 3,
    "islamic_quiz": 3
}

# Score adjustments based on task completion
TASK_COMPLETION_BONUS = {
    "completed": 5,      # +5 points per completed task
    "incomplete": -2,    # -2 points per incomplete task
    "max_adjustment": 20  # Maximum total adjustment
}


def get_task_completion_adjustment(db: Session, child_id: int, lacking_area: str, days: int = 30) -> float:
    """Calculate score adjustment based on task completions for a lacking area.
    
    Args:
        db: Database session
        child_id: Child's ID
        lacking_area: The lacking area to check
        days: Look back period for tasks (default 30 days)
    
    Returns:
        Score adjustment (-20 to +20)
    """
    since_time = datetime.utcnow() - timedelta(days=days)
    
    # Get all tasks for this lacking area
    tasks = (
        db.query(ChildTask)
        .filter(
            and_(
                ChildTask.child_id == child_id,
                ChildTask.source == "lacking_analysis",
                ChildTask.created_at >= since_time
            )
        )
        .all()
    )
    
    # Filter by lacking area and count by status
    completed_count = 0
    incomplete_count = 0
    
    for task in tasks:
        if task.meta and task.meta.get("lacking_area") == lacking_area:
            if task.status == "completed":
                completed_count += 1
            elif task.status == "incomplete":
                incomplete_count += 1
    
    # Calculate adjustment
    adjustment = (
        (completed_count * TASK_COMPLETION_BONUS["completed"]) +
        (incomplete_count * TASK_COMPLETION_BONUS["incomplete"])
    )
    
    # Cap the adjustment
    max_adj = TASK_COMPLETION_BONUS["max_adjustment"]
    adjustment = max(-max_adj, min(max_adj, adjustment))
    
    logger.info(
        f"Task adjustment for child {child_id}, area {lacking_area}: "
        f"{adjustment:.1f} (completed={completed_count}, incomplete={incomplete_count})"
    )
    
    return adjustment


def analyze_presence_of_mind(game_results: List[ChildGameResult]) -> Dict[str, Any]:
    """Analyze presence of mind from memory game results.
    
    Metrics:
    - Actual game score (matches found, time taken)
    - Consistency across sessions
    """
    if not game_results:
        return {"score": None, "status": "insufficient_data"}
    
    game_scores = []
    
    for result in game_results:
        raw = result.raw_result or {}
        
        # Use actual game performance: matches found, score, or success rate
        if "score" in raw:
            game_scores.append(float(raw["score"]))
        elif "matches" in raw and "total_pairs" in raw:
            # Calculate percentage of matches found
            match_rate = (raw["matches"] / raw["total_pairs"]) * 100
            game_scores.append(match_rate)
    
    if not game_scores:
        return {"score": None, "status": "insufficient_data"}
    
    avg_score = sum(game_scores) / len(game_scores)
    
    return {
        "score": round(avg_score, 2),
        "status": "lacking" if avg_score < LACKING_THRESHOLDS["presence_of_mind"] else "good",
        "games_analyzed": len(game_results),
        "details": {
            "recent_scores": game_scores[-3:] if len(game_scores) >= 3 else game_scores
        }
    }


def analyze_mood_identification(game_results: List[ChildGameResult]) -> Dict[str, Any]:
    """Analyze mood identification from mood picker game results.
    
    Metrics:
    - Correct mood identification
    - Pattern in mood selections
    """
    if not game_results:
        return {"score": None, "status": "insufficient_data"}
    
    correct_identifications = 0
    total_attempts = 0
    mood_choices = []
    
    for result in game_results:
        raw = result.raw_result or {}
        
        # Check if mood was correctly identified
        if "is_correct" in raw:
            total_attempts += 1
            if raw["is_correct"]:
                correct_identifications += 1
        elif "score" in raw:
            # Use direct score if available
            total_attempts += 1
            correct_identifications += (raw["score"] / 100)
        
        if "selected_mood" in raw:
            mood_choices.append(raw["selected_mood"])
    
    if total_attempts == 0:
        return {"score": None, "status": "insufficient_data"}
    
    # Score is based on correct identifications
    accuracy = (correct_identifications / total_attempts) * 100
    
    # Analyze mood pattern
    mood_distribution = {}
    for mood in mood_choices:
        mood_distribution[mood] = mood_distribution.get(mood, 0) + 1
    
    return {
        "score": round(accuracy, 2),
        "status": "lacking" if accuracy < LACKING_THRESHOLDS["mood_identification"] else "good",
        "games_analyzed": len(game_results),
        "mood_pattern": mood_distribution,
        "details": {
            "correct_identifications": correct_identifications,
            "total_attempts": total_attempts,
            "dominant_mood": max(mood_distribution.items(), key=lambda x: x[1])[0] if mood_distribution else None
        }
    }


def analyze_learning_capability(game_results: List[ChildGameResult]) -> Dict[str, Any]:
    """Analyze learning capability from Islamic quiz results.
    
    Metrics:
    - Correct answer rate (100% of score for knowledge tests)
    - Improvement trend over time
    """
    if not game_results:
        return {"score": None, "status": "insufficient_data"}
    
    correct_answers = 0
    total_questions = 0
    accuracy_by_game = []
    
    for result in game_results:
        raw = result.raw_result or {}
        
        if "is_correct" in raw:
            total_questions += 1
            if raw["is_correct"]:
                correct_answers += 1
            # Track per-game accuracy for trend analysis
            accuracy_by_game.append(100 if raw["is_correct"] else 0)
    
    if total_questions == 0:
        return {"score": None, "status": "insufficient_data"}
    
    # Score is purely based on accuracy (correct answers)
    accuracy = (correct_answers / total_questions * 100)
    final_score = accuracy
    
    # Check improvement trend (comparing first half vs second half)
    improvement_trend = "stable"
    if len(accuracy_by_game) >= 4:
        mid = len(accuracy_by_game) // 2
        first_half_avg = sum(accuracy_by_game[:mid]) / mid
        second_half_avg = sum(accuracy_by_game[mid:]) / (len(accuracy_by_game) - mid)
        if second_half_avg > first_half_avg + 10:
            improvement_trend = "improving"
        elif second_half_avg < first_half_avg - 10:
            improvement_trend = "declining"
    
    return {
        "score": round(final_score, 2),
        "status": "lacking" if final_score < LACKING_THRESHOLDS["learning_capability"] else "good",
        "games_analyzed": len(game_results),
        "accuracy_rate": round(accuracy, 2),
        "improvement_trend": improvement_trend,
        "details": {
            "correct_answers": correct_answers,
            "total_questions": total_questions
        }
    }


def analyze_behavior_identification(game_results: List[ChildGameResult]) -> Dict[str, Any]:
    """Analyze behavior identification from scenario game results.
    
    Metrics:
    - Correct moral/behavioral choices
    - Decision-making quality
    """
    if not game_results:
        return {"score": None, "status": "insufficient_data"}
    
    correct_choices = 0
    total_scenarios = 0
    choices_made = []
    
    for result in game_results:
        raw = result.raw_result or {}
        
        # Check if choice was correct/appropriate
        if "is_correct" in raw:
            total_scenarios += 1
            if raw["is_correct"]:
                correct_choices += 1
        elif "choice_quality" in raw:
            # Use choice quality score if available (0-100)
            total_scenarios += 1
            correct_choices += (raw["choice_quality"] / 100)
        elif "score" in raw:
            # Use direct score
            total_scenarios += 1
            correct_choices += (raw["score"] / 100)
        
        if "selected_option" in raw:
            choices_made.append(raw["selected_option"])
    
    if total_scenarios == 0:
        return {"score": None, "status": "insufficient_data"}
    
    # Score based on correct behavioral choices
    accuracy = (correct_choices / total_scenarios) * 100
    
    return {
        "score": round(accuracy, 2),
        "status": "lacking" if accuracy < LACKING_THRESHOLDS["behavior_identification"] else "good",
        "games_analyzed": len(game_results),
        "details": {
            "correct_choices": round(correct_choices, 2),
            "total_scenarios": total_scenarios,
            "choices_pattern": choices_made[-5:] if len(choices_made) >= 5 else choices_made
        }
    }


def get_child_lacking_analysis(
    db: Session,
    child_id: int,
    days: int = 7,
    include_task_adjustments: bool = True
) -> Dict[str, Any]:
    """Comprehensive lacking analysis for a child based on recent game performance.
    
    Args:
        db: Database session
        child_id: Child's ID
        days: Number of days to analyze (default: 7)
        include_task_adjustments: Whether to adjust scores based on task completion (default True)
    
    Returns:
        Dictionary with lacking areas, scores, and recommendations
    """
    # Fetch child info
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise ValueError(f"Child with ID {child_id} not found")
    
    # Get recent game results
    since_date = datetime.utcnow() - timedelta(days=days)
    results = (
        db.query(ChildGameResult)
        .filter(
            and_(
                ChildGameResult.child_id == child_id,
                ChildGameResult.created_at >= since_date
            )
        )
        .order_by(ChildGameResult.created_at.desc())
        .all()
    )
    
    # Group results by game type
    game_groups = {
        "memory": [],
        "mood": [],
        "scenario": [],
        "islamic_quiz": []
    }
    
    for result in results:
        game_type = result.game_type
        if game_type in game_groups:
            game_groups[game_type].append(result)
    
    # Analyze each area
    presence_analysis = analyze_presence_of_mind(game_groups["memory"])
    mood_analysis = analyze_mood_identification(game_groups["mood"])
    learning_analysis = analyze_learning_capability(game_groups["islamic_quiz"])
    behavior_analysis = analyze_behavior_identification(game_groups["scenario"])
    
    # Apply task completion adjustments to scores if enabled
    if include_task_adjustments:
        for area_key in ["presence_of_mind", "mood_identification", "learning_capability", "behavior_identification"]:
            adjustment = get_task_completion_adjustment(db, child_id, area_key, days=30)
            
            # Apply adjustment to each analysis
            if area_key == "presence_of_mind" and presence_analysis["score"] is not None:
                original_score = presence_analysis["score"]
                presence_analysis["score"] = min(100, max(0, presence_analysis["score"] + adjustment))
                presence_analysis["task_adjustment"] = adjustment
                presence_analysis["original_score"] = original_score
                presence_analysis["status"] = "lacking" if presence_analysis["score"] < LACKING_THRESHOLDS["presence_of_mind"] else "good"
            elif area_key == "mood_identification" and mood_analysis["score"] is not None:
                original_score = mood_analysis["score"]
                mood_analysis["score"] = min(100, max(0, mood_analysis["score"] + adjustment))
                mood_analysis["task_adjustment"] = adjustment
                mood_analysis["original_score"] = original_score
                mood_analysis["status"] = "lacking" if mood_analysis["score"] < LACKING_THRESHOLDS["mood_identification"] else "good"
            elif area_key == "learning_capability" and learning_analysis["score"] is not None:
                original_score = learning_analysis["score"]
                learning_analysis["score"] = min(100, max(0, learning_analysis["score"] + adjustment))
                learning_analysis["task_adjustment"] = adjustment
                learning_analysis["original_score"] = original_score
                learning_analysis["status"] = "lacking" if learning_analysis["score"] < LACKING_THRESHOLDS["learning_capability"] else "good"
            elif area_key == "behavior_identification" and behavior_analysis["score"] is not None:
                original_score = behavior_analysis["score"]
                behavior_analysis["score"] = min(100, max(0, behavior_analysis["score"] + adjustment))
                behavior_analysis["task_adjustment"] = adjustment
                behavior_analysis["original_score"] = original_score
                behavior_analysis["status"] = "lacking" if behavior_analysis["score"] < LACKING_THRESHOLDS["behavior_identification"] else "good"
    
    # Identify lacking areas
    lacking_areas = []
    
    if presence_analysis["status"] == "lacking":
        lacking_areas.append({
            "area": "presence_of_mind",
            "label": "Presence of Mind",
            "score": presence_analysis["score"],
            "priority": "high" if presence_analysis["score"] < 50 else "medium",
            "game_type": "memory",
            "task_adjustment": presence_analysis.get("task_adjustment", 0)
        })
    
    if mood_analysis["status"] == "lacking":
        lacking_areas.append({
            "area": "mood_identification",
            "label": "Mood Identification",
            "score": mood_analysis["score"],
            "priority": "high" if mood_analysis["score"] < 50 else "medium",
            "game_type": "mood",
            "task_adjustment": mood_analysis.get("task_adjustment", 0)
        })
    
    if learning_analysis["status"] == "lacking":
        lacking_areas.append({
            "area": "learning_capability",
            "label": "Learning Capability",
            "score": learning_analysis["score"],
            "priority": "high" if learning_analysis["score"] < 55 else "medium",
            "game_type": "islamic_quiz",
            "task_adjustment": learning_analysis.get("task_adjustment", 0)
        })
    
    if behavior_analysis["status"] == "lacking":
        lacking_areas.append({
            "area": "behavior_identification",
            "label": "Behavior Identification",
            "score": behavior_analysis["score"],
            "priority": "high" if behavior_analysis["score"] < 50 else "medium",
            "game_type": "scenario",
            "task_adjustment": behavior_analysis.get("task_adjustment", 0)
        })
    
    # Sort by priority and score
    lacking_areas.sort(key=lambda x: (0 if x["priority"] == "high" else 1, x["score"]))
    
    return {
        "child_id": child_id,
        "child_name": child.name,
        "analysis_period_days": days,
        "total_games_played": len(results),
        "games_by_type": {k: len(v) for k, v in game_groups.items()},
        "lacking_areas": lacking_areas,
        "detailed_analysis": {
            "presence_of_mind": presence_analysis,
            "mood_identification": mood_analysis,
            "learning_capability": learning_analysis,
            "behavior_identification": behavior_analysis
        },
        "requires_attention": len(lacking_areas) > 0,
        "analyzed_at": datetime.utcnow().isoformat()
    }


def should_generate_ticker(
    db: Session,
    child_id: int,
    lacking_area: str,
    hours_since_last: int = 24
) -> bool:
    """Check if a ticker notification should be generated for a lacking area.
    
    Prevents spam by checking if a similar notification was already generated recently.
    """
    since_time = datetime.utcnow() - timedelta(hours=hours_since_last)
    
    # Check if there's already a pending task for this lacking area
    # Query all recent pending tasks and filter in Python to avoid .astext compatibility issues
    recent_tasks = (
        db.query(ChildTask)
        .filter(
            and_(
                ChildTask.child_id == child_id,
                ChildTask.source == "lacking_analysis",
                ChildTask.created_at >= since_time,
                ChildTask.status == "pending"
            )
        )
        .all()
    )
    
    # Check if any task matches the lacking area
    for task in recent_tasks:
        if task.meta and task.meta.get("lacking_area") == lacking_area:
            return False
    
    return True
