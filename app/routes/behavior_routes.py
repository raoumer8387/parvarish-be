"""API routes for child behavior tracking."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.parent import Parent
from app.schemas.behavior_schemas import (
    PersonalizedQuestion,
    BehaviorResponseRequest,
    BehaviorResponseResult,
    QuestionCreate,
    QuestionRead,
    ChildResponsesSubmit,
    SubmitChildResponsesResult,
)
from app.services.behavior_service import (
    get_personalized_questions,
    save_behavior_responses,
    get_child_behavior_history,
    get_child_questions,
    submit_child_responses,
    get_child_behavior_stats,
    get_child_questions_full_coverage,
)
from app.services.task_service import generate_tasks_from_scores
from app.services.unified_behavior import refresh_and_notify_dashboard
from app.core.security import get_current_user
from app.db.models.behavior_models import Question
from app.db.models.child import Child

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/behavior", tags=["behavior"])


@router.get("/questions/personalized", response_model=List[PersonalizedQuestion])
def get_personalized_behavior_questions(
    db: Session = Depends(get_db),
    total_questions: int = 5,
    current_user: User = Depends(get_current_user)
):
    """
    Get personalized behavior questions for all children of the logged-in parent.
    
    Args:
        total_questions: Number of random questions to fetch (default: 5)
        current_user: The currently authenticated user (must be a parent)
    Returns:
        List of personalized questions for each child
    """
    # Ensure the user is a parent
    if current_user.user_type != "parent":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can access personalized questions."
        )
    # Look up parent profile by current user's ID (Parent.id == User.id)
    parent = db.query(Parent).filter(Parent.id == current_user.id).first()
    if parent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent profile not found for the current user."
        )
    parent_id = parent.id
    # Get personalized questions
    questions = get_personalized_questions(db, parent_id, total_questions=total_questions)
    if not questions:
        return []
    logger.info(f"Returning {len(questions)} personalized questions for parent {parent_id}")
    return questions


@router.get("/questions/{child_id}/daily-full", response_model=List[PersonalizedQuestion])
def get_child_behavior_questions_full_coverage(
    child_id: int,
    db: Session = Depends(get_db),
    per_category: int = 1,
    current_user: User = Depends(get_current_user),
):
    """Get daily questions ensuring every behavior aspect is covered.

    Returns at least `per_category` questions per category (age-aware, with fallback).
    """
    if current_user.user_type != "parent":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only parents can access child questions.")

    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Child {child_id} not found")
    if child.parent_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this child")

    questions = get_child_questions_full_coverage(db, child_id, per_category=per_category)
    return questions


@router.get("/questions/{child_id}", response_model=List[PersonalizedQuestion])
def get_child_behavior_questions(
    child_id: int,
    db: Session = Depends(get_db),
    total_questions: int = 5,
    all_aspects: bool = False,
    per_category: int = 1,
    current_user: User = Depends(get_current_user)
):
    """Get behavior questions for a child.

    Modes:
    - Default (all_aspects = false): return `total_questions` random personalized questions.
    - Full coverage (all_aspects = true): return at least `per_category` question per aspect
      across: emotional, social, physical, behavioral, religious.
    """
    if current_user.user_type != "parent":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only parents can access child questions.")

    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Child {child_id} not found")
    if child.parent_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this child")

    if all_aspects:
        questions = get_child_questions_full_coverage(db, child_id, per_category=per_category)
    else:
        questions = get_child_questions(db, child_id, total_questions=total_questions)

    logger.info(
        f"Returning {len(questions)} questions for child {child_id} (all_aspects={all_aspects}, per_category={per_category if all_aspects else 'n/a'})"
    )
    return questions


@router.get("/stats/{child_id}")
def get_child_stats(
    child_id: int,
    db: Session = Depends(get_db),
    days: int | None = None,
    current_user: User = Depends(get_current_user)
):
    """Get computed behavior statistics for a single child.

    Requires the authenticated parent to own the child.
    """
    if current_user.user_type != "parent":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only parents can access stats.")

    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Child {child_id} not found")
    if child.parent_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this child")

    stats = get_child_behavior_stats(db, child_id, days=days)
    return stats


@router.get("/check-in-status")
def get_checkin_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get check-in status for all children of the logged-in parent.
    
    Shows when each child last had responses recorded and whether
    they need a daily check-in (>24 hours since last response).
    """
    from datetime import datetime, timedelta
    from app.db.models.behavior_models import ChildBehaviorResponse
    
    if current_user.user_type != "parent":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only parents can access check-in status.")
    
    children = db.query(Child).filter(Child.parent_id == current_user.id).all()
    
    result = []
    now = datetime.utcnow()
    
    for child in children:
        # Get most recent response
        last_response = (
            db.query(ChildBehaviorResponse)
            .filter(ChildBehaviorResponse.child_id == child.id)
            .order_by(ChildBehaviorResponse.timestamp.desc())
            .first()
        )
        
        if last_response and last_response.timestamp:
            last_ts = last_response.timestamp
            # Handle timezone-aware datetime by removing timezone info for comparison
            if last_ts.tzinfo is not None:
                last_ts_naive = last_ts.replace(tzinfo=None)
            else:
                last_ts_naive = last_ts
            hours_since = (now - last_ts_naive).total_seconds() / 3600
            needs_checkin = hours_since >= 24
        else:
            last_ts = None
            hours_since = None
            needs_checkin = True  # Never answered
        
        result.append({
            "child_id": child.id,
            "child_name": child.name,
            "last_check_in": last_ts.isoformat() if last_ts else None,
            "hours_since_last_check_in": round(hours_since, 1) if hours_since else None,
            "needs_check_in": needs_checkin
        })
    
    return {
        "parent_id": current_user.id,
        "check_in_interval_hours": 24,
        "children": result
    }


@router.post("/submit-responses", response_model=SubmitChildResponsesResult)
def submit_behavior_responses(
    request: ChildResponsesSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit parent's answers about child behavior for a single child.
    
    Args:
        request: Contains child_id and list of responses {question_id, answer}
        
    Returns:
        Aggregated scoring and status
    """
    if not request.responses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No responses provided"
        )

    # Auth: ensure user is a parent and owns the child
    if current_user.user_type != "parent":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only parents can submit responses.")

    child = db.query(Child).filter(Child.id == request.child_id).first()
    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Child {request.child_id} not found")
    if child.parent_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this child")

    # Save responses and compute totals
    result = submit_child_responses(db, request.child_id, [r.model_dump() for r in request.responses])

    # Interlink: low check-in categories → tasks; refresh unified dashboard for parent
    tasks_gen = generate_tasks_from_scores(db, child_id=request.child_id, days=3)
    unified = refresh_and_notify_dashboard(db, request.child_id, trigger_source="daily_checkin")

    logger.info(
        f"Saved {result['total_questions']} responses for child {request.child_id}; "
        f"tasks={tasks_gen.get('count', 0)}; unified_score={unified.get('overall_score')}"
    )

    return SubmitChildResponsesResult(
        message="Responses saved successfully",
        child_id=request.child_id,
        total_score=result["total_score"],
        total_questions=result["total_questions"],
    )


@router.get("/child/{child_id}/history")
def get_child_history(
    child_id: int,
    db: Session = Depends(get_db),
    limit: int = 20
):
    """
    Get behavior response history for a specific child.
    
    Args:
        child_id: Child's user ID
        limit: Maximum number of responses to return
        
    Returns:
        List of behavior responses
    """
    responses = get_child_behavior_history(db, child_id, limit)
    
    return {
        "child_id": child_id,
        "total": len(responses),
        "responses": [
            {
                "id": r.id,
                "question_text": r.question_text,
                "answer": r.answer,
                "score": r.score,
                "timestamp": r.timestamp.isoformat()
            }
            for r in responses
        ]
    }


# Admin endpoints for managing questions

@router.post("/questions", response_model=QuestionRead, status_code=status.HTTP_201_CREATED)
def create_question(
    question: QuestionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new behavior question (admin/seeding endpoint).
    
    Args:
        question: Question data
        
    Returns:
        Created question
    """
    new_question = Question(
        question_text_template=question.question_text_template,
        category=question.category,
        options=question.options,
        weight=question.weight
    )
    
    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    
    logger.info(f"Created new question: {new_question.id}")
    return new_question


@router.get("/questions", response_model=List[QuestionRead])
def list_questions(
    db: Session = Depends(get_db),
    category: str = None,
    limit: int = 50
):
    """
    List all behavior questions.
    
    Args:
        category: Filter by category (optional)
        limit: Maximum number of questions to return
        
    Returns:
        List of questions
    """
    query = db.query(Question)
    
    if category:
        query = query.filter(Question.category == category)
    
    questions = query.limit(limit).all()
    
    return questions


@router.get("/questions/{question_id}", response_model=QuestionRead)
def get_question(
    question_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific question by ID.
    
    Args:
        question_id: Question ID
        
    Returns:
        Question details
    """
    question = db.query(Question).filter(Question.id == question_id).first()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question with ID {question_id} not found"
        )
    
    return question


@router.delete("/questions/{question_id}")
def delete_question(
    question_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a behavior question.
    
    Args:
        question_id: Question ID
        
    Returns:
        Success message
    """
    question = db.query(Question).filter(Question.id == question_id).first()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question with ID {question_id} not found"
        )
    
    db.delete(question)
    db.commit()
    
    logger.info(f"Deleted question: {question_id}")
    
    return {
        "message": "Question deleted successfully",
        "question_id": question_id
    }
