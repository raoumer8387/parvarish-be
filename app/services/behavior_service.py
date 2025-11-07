"""Business logic for behavior tracking."""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict
import logging

from app.db.models.behavior_models import Question, ChildBehaviorResponse
from app.db.models.child import Child
from app.schemas.behavior_schemas import PersonalizedQuestion, BehaviorResponseItem

logger = logging.getLogger(__name__)


def get_personalized_questions(
    db: Session,
    parent_id: int,
    questions_per_category: int = 3,
    total_questions: int = 5
) -> List[PersonalizedQuestion]:
    """
    Fetch random questions and personalize them for each child.
    
    Args:
        db: Database session
        parent_id: Parent's user ID
        questions_per_category: Number of questions per category (if using category logic)
        total_questions: Total number of random questions to fetch
        
    Returns:
        List of personalized questions for all children
    """
    # Get all children for this parent
    children = db.query(Child).filter(Child.parent_id == parent_id).all()
    
    if not children:
        logger.info(f"No children found for parent {parent_id}")
        return []
    
    # Fetch random questions
    questions = db.query(Question).order_by(func.random()).limit(total_questions).all()
    
    if not questions:
        logger.warning("No questions found in database")
        return []
    
    # Personalize questions for each child
    personalized_questions = []
    
    for child in children:
        for question in questions:
            # Replace {child_name} placeholder with actual child name
            personalized_text = question.question_text_template.replace("{child_name}", child.name)
            
            personalized_questions.append(
                PersonalizedQuestion(
                    child_id=child.id,
                    child_name=child.name,
                    question_id=question.id,
                    question_text=personalized_text,
                    options=question.options,
                    category=question.category
                )
            )
    
    logger.info(f"Generated {len(personalized_questions)} personalized questions for {len(children)} children")
    return personalized_questions


def save_behavior_responses(
    db: Session,
    responses: List[BehaviorResponseItem]
) -> int:
    """
    Save parent's behavior responses for children.
    
    Args:
        db: Database session
        responses: List of behavior responses
        
    Returns:
        Number of responses saved
    """
    saved_count = 0
    
    for response_item in responses:
        # Fetch the question to get weight and template
        question = db.query(Question).filter(Question.id == response_item.question_id).first()
        
        if not question:
            logger.warning(f"Question {response_item.question_id} not found, skipping")
            continue
        
        # Fetch child to get name for personalization
        child = db.query(Child).filter(Child.id == response_item.child_id).first()
        
        if not child:
            logger.warning(f"Child {response_item.child_id} not found, skipping")
            continue
        
        # Personalize question text
        personalized_text = question.question_text_template.replace("{child_name}", child.name)
        
        # Calculate score based on answer
        score = calculate_score(response_item.answer, question.weight)
        
        # Create response record
        behavior_response = ChildBehaviorResponse(
            child_id=response_item.child_id,
            question_id=response_item.question_id,
            question_text=personalized_text,
            answer=response_item.answer,
            score=score
        )
        
        db.add(behavior_response)
        saved_count += 1
    
    db.commit()
    logger.info(f"Saved {saved_count} behavior responses")
    
    return saved_count


def calculate_score(answer: str, weight: int) -> int:
    """
    Calculate score based on answer and question weight.
    
    Args:
        answer: Parent's answer (e.g., "Yes", "No", "Sometimes")
        weight: Question weight
        
    Returns:
        Computed score
    """
    answer_lower = answer.lower()
    
    if answer_lower == "yes":
        return weight
    elif answer_lower == "no":
        return 0
    elif answer_lower == "sometimes":
        return int(weight * 0.5)
    else:
        # Default: treat unknown answers as neutral
        return 0


def get_child_behavior_history(
    db: Session,
    child_id: int,
    limit: int = 20
) -> List[ChildBehaviorResponse]:
    """
    Get behavior response history for a specific child.
    
    Args:
        db: Database session
        child_id: Child's user ID
        limit: Maximum number of responses to return
        
    Returns:
        List of behavior responses
    """
    responses = (
        db.query(ChildBehaviorResponse)
        .filter(ChildBehaviorResponse.child_id == child_id)
        .order_by(ChildBehaviorResponse.timestamp.desc())
        .limit(limit)
        .all()
    )
    
    return responses
