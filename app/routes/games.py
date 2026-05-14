"""Games API routes for child activities.

Endpoints:
- POST /games/memory/submit
- POST /games/mood/submit
- POST /games/scenario/submit
- POST /games/islamic-quiz/submit
- GET /games/{child_id}/analysis
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any

from app.core.security import get_current_user
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.child import Child
from app.db.models.game_results import ChildGameResult
from app.db.models.game_questions import MoodScenario, ScenarioQuestion, IslamicQuizQuestion

from app.games.memory_game.service import save_memory_game_result
from app.games.mood_picker.service import save_mood_result
from app.games.scenario_game.service import save_scenario_result
from app.games.islamic_quiz.service import save_quiz_result
from app.services.task_service import generate_tasks_from_scores
from app.services.parent_realtime import notify_parent_child_game_completed
from app.games.game_config import (
    calculate_game_score,
    get_completion_message,
    validate_game_completion,
    GAME_TIME_LIMITS,
    QUESTIONS_PER_GAME
)


router = APIRouter(prefix="/games", tags=["games"])


def get_age_group_from_age(age: int | None) -> str:
    """Convert child's age to age group string for game questions."""
    if age is None:
        return "6-8"  # Default to youngest group if age not set
    
    if age <= 8:
        return "6-8"
    elif age <= 11:
        return "9-11"
    else:
        return "12-14"


# ==================== BATCH GAME SUBMISSION (Complete Sessions) ====================

@router.post("/session/mood/complete")
def complete_mood_session(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Submit complete mood game session with all responses.
    
    Expected payload:
    {
        "child_id": 1,
        "total_time_seconds": 245,
        "responses": [
            {"scenario_id": 1, "selected_mood": "Forgive", "time_taken": 45},
            {"scenario_id": 3, "selected_mood": "Happy", "time_taken": 52},
            ...
        ]
    }
    """
    required = ["child_id", "total_time_seconds", "responses"]
    for k in required:
        if k not in payload:
            raise HTTPException(status_code=422, detail=f"Missing field: {k}")
    
    child_id = int(payload["child_id"])
    _assert_child_is_self(db, user, child_id)
    
    responses = payload["responses"]
    total_time = int(payload["total_time_seconds"])
    
    # Validate completion
    validation = validate_game_completion("mood", {"responses": responses})
    if not validation["valid"]:
        raise HTTPException(status_code=422, detail=validation["message"])
    
    # Check time limit
    if total_time > GAME_TIME_LIMITS["mood"]:
        raise HTTPException(status_code=422, detail=f"Time limit exceeded. Max: {GAME_TIME_LIMITS['mood']}s")
    
    # Save all responses as batch
    all_results = []
    for resp in responses:
        result = save_mood_result(
            db,
            child_id,
            int(resp["scenario_id"]),
            str(resp["selected_mood"]),
        )
        all_results.append(result)
    
    # Calculate final score
    score_data = calculate_game_score("mood", {"responses": responses})
    completion_msg = get_completion_message(score_data["percentage"])
    
    # Generate tasks based on performance
    gen = generate_tasks_from_scores(db, child_id=child_id, days=3)

    notify_parent_child_game_completed(db, child_id, "mood", score_data)

    return {
        "success": True,
        "game_type": "mood",
        "score": score_data,
        "completion_message": completion_msg,
        "tasks_generated": gen.get("count", 0),
        "time_taken": total_time,
        "time_limit": GAME_TIME_LIMITS["mood"],
        "results_saved": len(all_results)
    }


@router.post("/session/scenario/complete")
def complete_scenario_session(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Submit complete scenario game session.
    
    Expected payload:
    {
        "child_id": 1,
        "total_time_seconds": 280,
        "responses": [
            {"scenario_id": 5, "selected_option": "Help them study", "time_taken": 55},
            ...
        ]
    }
    """
    required = ["child_id", "total_time_seconds", "responses"]
    for k in required:
        if k not in payload:
            raise HTTPException(status_code=422, detail=f"Missing field: {k}")
    
    child_id = int(payload["child_id"])
    _assert_child_is_self(db, user, child_id)
    
    responses = payload["responses"]
    total_time = int(payload["total_time_seconds"])
    
    # Validate completion
    validation = validate_game_completion("scenario", {"responses": responses})
    if not validation["valid"]:
        raise HTTPException(status_code=422, detail=validation["message"])
    
    # Check time limit
    if total_time > GAME_TIME_LIMITS["scenario"]:
        raise HTTPException(status_code=422, detail=f"Time limit exceeded. Max: {GAME_TIME_LIMITS['scenario']}s")
    
    # Save all responses and collect scores
    all_results = []
    response_scores = []
    for resp in responses:
        result = save_scenario_result(
            db,
            child_id,
            int(resp["scenario_id"]),
            str(resp["selected_option"]),
        )
        all_results.append(result)
        
        # Extract score from analysis
        score = sum(result.analysis_score.values()) if result.analysis_score else 0
        response_scores.append({"score": score})
    
    # Calculate final score
    score_data = calculate_game_score("scenario", {"responses": response_scores})
    completion_msg = get_completion_message(score_data["percentage"])
    
    # Generate tasks
    gen = generate_tasks_from_scores(db, child_id=child_id, days=3)

    notify_parent_child_game_completed(db, child_id, "scenario", score_data)

    return {
        "success": True,
        "game_type": "scenario",
        "score": score_data,
        "completion_message": completion_msg,
        "tasks_generated": gen.get("count", 0),
        "time_taken": total_time,
        "time_limit": GAME_TIME_LIMITS["scenario"],
        "results_saved": len(all_results)
    }


@router.post("/session/islamic-quiz/complete")
def complete_quiz_session(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Submit complete Islamic quiz session.
    
    Expected payload:
    {
        "child_id": 1,
        "total_time_seconds": 210,
        "responses": [
            {"question_id": 2, "selected_answer": "B", "time_taken": 18},
            ...
        ]
    }
    """
    required = ["child_id", "total_time_seconds", "responses"]
    for k in required:
        if k not in payload:
            raise HTTPException(status_code=422, detail=f"Missing field: {k}")
    
    child_id = int(payload["child_id"])
    _assert_child_is_self(db, user, child_id)
    
    responses = payload["responses"]
    total_time = int(payload["total_time_seconds"])
    
    # Validate completion
    validation = validate_game_completion("islamic_quiz", {"responses": responses})
    if not validation["valid"]:
        raise HTTPException(status_code=422, detail=validation["message"])
    
    # Check time limit
    if total_time > GAME_TIME_LIMITS["islamic_quiz"]:
        raise HTTPException(status_code=422, detail=f"Time limit exceeded. Max: {GAME_TIME_LIMITS['islamic_quiz']}s")
    
    # Save all responses and check correctness
    all_results = []
    response_data = []
    for resp in responses:
        result = save_quiz_result(
            db,
            child_id,
            int(resp["question_id"]),
            str(resp["selected_answer"]),
        )
        all_results.append(result)
        
        # Check if answer was correct
        is_correct = result.analysis_score.get("spiritual", 0) > 50  # Correct answers get high spiritual score
        response_data.append({
            "is_correct": is_correct,
            "time_taken": resp.get("time_taken", 24)
        })
    
    # Calculate final score
    score_data = calculate_game_score("islamic_quiz", {"responses": response_data})
    completion_msg = get_completion_message(score_data["percentage"])
    
    # Generate tasks
    gen = generate_tasks_from_scores(db, child_id=child_id, days=3)

    notify_parent_child_game_completed(db, child_id, "islamic_quiz", score_data)

    return {
        "success": True,
        "game_type": "islamic_quiz",
        "score": score_data,
        "completion_message": completion_msg,
        "tasks_generated": gen.get("count", 0),
        "time_taken": total_time,
        "time_limit": GAME_TIME_LIMITS["islamic_quiz"],
        "results_saved": len(all_results),
        "correct_answers": score_data["breakdown"]["correct_answers"]
    }


@router.post("/session/memory/complete")
def complete_memory_session(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Submit complete memory game session.
    
    Expected payload:
    {
        "child_id": 1,
        "total_flips": 24,
        "correct_matches": 10,
        "wrong_matches": 4,
        "time_taken_seconds": 95
    }
    """
    required = ["child_id", "total_flips", "correct_matches", "wrong_matches", "time_taken_seconds"]
    for k in required:
        if k not in payload:
            raise HTTPException(status_code=422, detail=f"Missing field: {k}")
    
    child_id = int(payload["child_id"])
    _assert_child_is_self(db, user, child_id)
    
    time_taken = int(payload["time_taken_seconds"])
    
    # Validate completion
    validation = validate_game_completion("memory", payload)
    if not validation["valid"]:
        raise HTTPException(status_code=422, detail=validation["message"])
    
    # Check time limit
    if time_taken > GAME_TIME_LIMITS["memory"]:
        raise HTTPException(status_code=422, detail=f"Time limit exceeded. Max: {GAME_TIME_LIMITS['memory']}s")
    
    # Save result
    result = save_memory_game_result(
        db,
        child_id,
        int(payload["total_flips"]),
        int(payload["correct_matches"]),
        int(payload["wrong_matches"]),
        time_taken,
    )
    
    # Calculate final score
    score_data = calculate_game_score("memory", {
        "total_flips": payload["total_flips"],
        "correct_matches": payload["correct_matches"],
        "time_taken_seconds": time_taken
    })
    completion_msg = get_completion_message(score_data["percentage"])
    
    # Generate tasks
    gen = generate_tasks_from_scores(db, child_id=child_id, days=3)

    notify_parent_child_game_completed(db, child_id, "memory", score_data)

    return {
        "success": True,
        "game_type": "memory",
        "score": score_data,
        "completion_message": completion_msg,
        "tasks_generated": gen.get("count", 0),
        "time_taken": time_taken,
        "time_limit": GAME_TIME_LIMITS["memory"],
        "result_id": str(result.id)
    }


# ==================== SINGLE SUBMISSION ENDPOINTS (Legacy/Individual) ====================


def _assert_parent_owns_child(db: Session, user: User, child_id: int) -> Child:
    """Ensure the authenticated parent owns the child."""
    from app.db.models.parent import Parent
    
    # Query parent directly instead of using backref
    parent = db.query(Parent).filter(Parent.id == user.id).first()
    if not parent:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only parents can view game results")
    
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child not found")
    
    if child.parent_id != parent.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Child does not belong to this parent")
    
    return child


def _assert_child_is_self(db: Session, user: User, child_id: int) -> Child:
    """Ensure the authenticated child is submitting for themselves."""
    # Query child directly instead of using backref to avoid InstrumentedList issue
    child_profile = db.query(Child).filter(Child.id == user.id).first()
    if not child_profile:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only child accounts can submit game results")
    
    if child_profile.id != child_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only submit results for yourself")
    
    return child_profile


@router.post("/memory/submit")
def submit_memory_game(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Submit Memory Card game result.

    Expected payload keys: child_id, total_flips, correct_matches, wrong_matches, time_taken_seconds
    """
    required = ["child_id", "total_flips", "correct_matches", "wrong_matches", "time_taken_seconds"]
    for k in required:
        if k not in payload:
            raise HTTPException(status_code=422, detail=f"Missing field: {k}")
    child_id = int(payload["child_id"])
    # Only child users can submit/play
    _assert_child_is_self(db, user, child_id)

    result = save_memory_game_result(
        db,
        child_id,
        int(payload["total_flips"]),
        int(payload["correct_matches"]),
        int(payload["wrong_matches"]),
        int(payload["time_taken_seconds"]),
    )

    # Trigger task generation based on recent scores
    gen = generate_tasks_from_scores(db, child_id=child_id, days=3)

    score_data = calculate_game_score("memory", {
        "total_flips": payload["total_flips"],
        "correct_matches": payload["correct_matches"],
        "time_taken_seconds": int(payload["time_taken_seconds"]),
    })
    notify_parent_child_game_completed(db, child_id, "memory", score_data)

    return {"result_id": str(result.id), "analysis": result.analysis_score, "tasks_generated": gen.get("count", 0)}


@router.post("/mood/submit")
def submit_mood(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    required = ["child_id", "scenario_id", "selected_mood"]
    for k in required:
        if k not in payload:
            raise HTTPException(status_code=422, detail=f"Missing field: {k}")
    child_id = int(payload["child_id"])
    _assert_child_is_self(db, user, child_id)

    result = save_mood_result(
        db,
        child_id,
        int(payload["scenario_id"]),
        str(payload["selected_mood"]),
    )
    gen = generate_tasks_from_scores(db, child_id=child_id, days=3)
    return {"result_id": str(result.id), "analysis": result.analysis_score, "tasks_generated": gen.get("count", 0)}


@router.post("/scenario/submit")
def submit_scenario(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    required = ["child_id", "scenario_id", "selected_option"]
    for k in required:
        if k not in payload:
            raise HTTPException(status_code=422, detail=f"Missing field: {k}")
    child_id = int(payload["child_id"])
    _assert_child_is_self(db, user, child_id)

    result = save_scenario_result(
        db,
        child_id,
        int(payload["scenario_id"]),
        str(payload["selected_option"]),
    )
    gen = generate_tasks_from_scores(db, child_id=child_id, days=3)
    return {"result_id": str(result.id), "analysis": result.analysis_score, "tasks_generated": gen.get("count", 0)}


@router.post("/islamic-quiz/submit")
def submit_islamic_quiz(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    required = ["child_id", "question_id", "selected_answer"]
    for k in required:
        if k not in payload:
            raise HTTPException(status_code=422, detail=f"Missing field: {k}")
    child_id = int(payload["child_id"])
    _assert_child_is_self(db, user, child_id)

    # No longer need to pass correct_answer from client; service fetches it from DB
    result = save_quiz_result(
        db,
        child_id,
        int(payload["question_id"]),
        str(payload["selected_answer"]),
    )
    gen = generate_tasks_from_scores(db, child_id=child_id, days=3)
    return {"result_id": str(result.id), "analysis": result.analysis_score, "tasks_generated": gen.get("count", 0)}


@router.get("/{child_id}/analysis")
def get_child_analysis(
    child_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Aggregate recent game analyses to derive dominant strength and needs improvement.

    Returns a summary including suggested task category.
    """
    # Only parents can view dashboard analysis for a child
    _assert_parent_owns_child(db, user, child_id)
    # Aggregate last 10 game results
    results = (
        db.query(ChildGameResult)
        .filter(ChildGameResult.child_id == child_id)
        .order_by(ChildGameResult.created_at.desc())
        .limit(10)
        .all()
    )
    if not results:
        return {"message": "No game data yet", "dominant_strength": None, "needs_improvement": None, "suggested_task": None}

    # Sum category scores across results
    totals: Dict[str, float] = {}
    counts: Dict[str, int] = {}
    for r in results:
        for k, v in (r.analysis_score or {}).items():
            try:
                vnum = float(v)
            except Exception:
                vnum = 0.0
            totals[k] = totals.get(k, 0.0) + vnum
            counts[k] = counts.get(k, 0) + 1
    # Compute averages
    averages = {k: round(totals[k] / max(counts.get(k, 1), 1)) for k in totals.keys()}
    # Map to canonical categories
    canonical_keys = {
        "emotional": ["emotional", "emotional_control", "empathy"],
        "moral": ["moral"],
        "social": ["social"],
        "cognitive": ["cognitive", "focus"],
        "spiritual": ["spiritual"],
    }
    category_scores: Dict[str, float] = {}
    for cat, keys in canonical_keys.items():
        vals = [averages[k] for k in keys if k in averages]
        if vals:
            category_scores[cat] = round(sum(vals) / len(vals))
    if not category_scores:
        return {"message": "No analyzable scores", "dominant_strength": None, "needs_improvement": None, "suggested_task": None}

    dominant = max(category_scores.items(), key=lambda x: x[1])[0]
    weakest = min(category_scores.items(), key=lambda x: x[1])[0]

    # Suggest simple example tasks
    suggestions = {
        "emotional": "Kindness challenge",
        "moral": "Honesty task",
        "cognitive": "Memory training",
        "spiritual": "Dua/Salah task",
        "social": "Share and help a friend",
    }
    suggested_task = suggestions.get(weakest)

    return {
        "dominant_strength": dominant.capitalize(),
        "needs_improvement": weakest.capitalize(),
        "suggested_task": suggested_task,
        "category_scores": category_scores,
    }


# ==================== GET GAME QUESTIONS ====================

@router.get("/mood/questions")
def get_mood_questions(
    age_group: str | None = None,
    limit: int = 5,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get random mood picker scenarios. Child-only access.
    
    Questions are automatically filtered by child's age if age_group not specified.
    """
    child_profile = getattr(user, "child_profile", None)
    if not child_profile:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only children can access game questions")
    
    # If age_group not specified, use child's age
    if not age_group:
        age_group = get_age_group_from_age(child_profile.age)
    
    query = db.query(MoodScenario)
    query = query.filter(MoodScenario.age_group == age_group)
    
    scenarios = query.order_by(func.random()).limit(limit).all()
    return {
        "scenarios": [
            {
                "id": s.id,
                "scenario_en": s.scenario_text_en,
                "scenario_ur": s.scenario_text_ur,
                "scenario_roman": s.scenario_text_roman,
                "category": s.category,
                "mood_options": list(s.mood_weights.keys()) if s.mood_weights else []
            }
            for s in scenarios
        ]
    }


@router.get("/scenario/questions")
def get_scenario_questions(
    age_group: str | None = None,
    limit: int = 5,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get random scenario questions. Child-only access.
    
    Questions are automatically filtered by child's age if age_group not specified.
    """
    child_profile = getattr(user, "child_profile", None)
    if not child_profile:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only children can access game questions")
    
    # If age_group not specified, use child's age
    if not age_group:
        age_group = get_age_group_from_age(child_profile.age)
    
    query = db.query(ScenarioQuestion)
    query = query.filter(ScenarioQuestion.age_group == age_group)
    
    questions = query.order_by(func.random()).limit(limit).all()
    return {
        "questions": [
            {
                "id": q.id,
                "question_en": q.question_text_en,
                "question_ur": q.question_text_ur,
                "question_roman": q.question_text_roman,
                "category": q.category,
                "options": [opt["option"] for opt in q.options] if q.options else []
            }
            for q in questions
        ]
    }


@router.get("/islamic-quiz/questions")
def get_quiz_questions(
    age_group: str | None = None,
    difficulty: int | None = None,
    limit: int = 6,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get random Islamic quiz questions. Child-only access.
    
    Questions are automatically filtered by child's age if age_group not specified.
    """
    child_profile = getattr(user, "child_profile", None)
    if not child_profile:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only children can access game questions")
    
    # If age_group not specified, use child's age
    if not age_group:
        age_group = get_age_group_from_age(child_profile.age)
    
    query = db.query(IslamicQuizQuestion)
    query = query.filter(IslamicQuizQuestion.age_group == age_group)
    if difficulty:
        query = query.filter(IslamicQuizQuestion.difficulty == difficulty)
    
    questions = query.order_by(func.random()).limit(limit).all()
    return {
        "questions": [
            {
                "id": q.id,
                "question_en": q.question_text_en,
                "question_ur": q.question_text_ur,
                "question_roman": q.question_text_roman,
                "category": q.category,
                "options": q.options,
                "difficulty": q.difficulty
                # Note: correct_answer is NOT returned to prevent cheating
            }
            for q in questions
        ]
    }

