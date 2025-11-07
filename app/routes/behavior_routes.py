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
    QuestionRead
)
from app.services.behavior_service import (
    get_personalized_questions,
    save_behavior_responses,
    get_child_behavior_history
)
from app.core.security import get_current_user
from app.db.models.behavior_models import Question

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
    if not hasattr(current_user, "parent_profile") or current_user.user_type != "parent":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can access personalized questions."
        )
    parent = current_user.parent_profile
    if not parent:
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


@router.post("/submit-responses", response_model=BehaviorResponseResult)
def submit_behavior_responses(
    request: BehaviorResponseRequest,
    db: Session = Depends(get_db)
):
    """
    Submit parent's answers about child behavior.
    
    Args:
        request: Contains list of responses with child_id, question_id, and answer
        
    Returns:
        Success message with count of saved responses
    """
    if not request.responses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No responses provided"
        )
    
    # Save responses
    saved_count = save_behavior_responses(db, request.responses)
    
    logger.info(f"Saved {saved_count} behavior responses")
    
    return BehaviorResponseResult(
        message="Responses saved successfully",
        saved_count=saved_count
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
