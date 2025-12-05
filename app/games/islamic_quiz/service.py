"""Service logic for Islamic Quiz game."""

from sqlalchemy.orm import Session
from typing import Dict

from app.db.models.game_results import ChildGameResult
from app.db.models.game_questions import IslamicQuizQuestion


def analyze_quiz(db: Session, question_id: int, selected_answer: str) -> tuple[bool, Dict]:
    """Validate answer against DB and compute behavior scores."""
    question = db.query(IslamicQuizQuestion).filter(IslamicQuizQuestion.id == question_id).first()
    
    if not question:
        # Fallback if question not found
        is_correct = False
    else:
        is_correct = (selected_answer == question.correct_answer)
    
    spiritual_delta = 5 if is_correct else -2
    spiritual_score = max(0, min(100, 50 + spiritual_delta * 10))
    cognitive_score = max(0, min(100, 50 + (5 if is_correct else -3)))
    
    return is_correct, {"spiritual": spiritual_score, "cognitive": cognitive_score}


def save_quiz_result(
    db: Session,
    child_id: int,
    question_id: int,
    selected_answer: str,
) -> ChildGameResult:
    # Fetch correct answer from DB
    question = db.query(IslamicQuizQuestion).filter(IslamicQuizQuestion.id == question_id).first()
    correct_answer = question.correct_answer if question else ""
    
    is_correct, analysis = analyze_quiz(db, question_id, selected_answer)
    raw = {
        "question_id": question_id,
        "selected_answer": selected_answer,
        "correct_answer": correct_answer,
        "is_correct": is_correct,
    }
    result = ChildGameResult(
        child_id=child_id,
        game_type="islamic_quiz",
        raw_result=raw,
        analysis_score=analysis,
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result
