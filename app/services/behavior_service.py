"""Business logic for behavior tracking."""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict
import logging

from app.db.models.behavior_models import Question, ChildBehaviorResponse
from app.db.models.child import Child
from app.schemas.behavior_schemas import (
    PersonalizedQuestion,
    BehaviorResponseItem,
)

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


def get_child_questions(
    db: Session,
    child_id: int,
    total_questions: int = 5
) -> List[PersonalizedQuestion]:
    """Fetch random questions personalized for a single child.

    Args:
        db: Database session
        child_id: Child's user ID
        total_questions: Total number of random questions to fetch

    Returns:
        List of personalized questions for the specified child
    """
    # Fetch child record
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        logger.info(f"Child {child_id} not found when fetching questions")
        return []

    # Determine age group based on child's age
    age_group = None
    if child.age:
        if 6 <= child.age <= 8:
            age_group = "6-8"
        elif 9 <= child.age <= 11:
            age_group = "9-11"
        elif 12 <= child.age <= 14:
            age_group = "12-14"

    # Fetch random questions, filtered by age_group if available
    query = db.query(Question)
    if age_group:
        # Match questions where age_group contains the target (handles comma-separated values)
        # e.g., age_group = "6-8,9-11" matches both "6-8" and "9-11"
        age_specific = query.filter(
            Question.age_group.ilike(f'%{age_group}%')
        ).order_by(func.random()).limit(total_questions).all()
        
        if len(age_specific) < total_questions:
            # Fill remaining with any questions
            remaining = total_questions - len(age_specific)
            extra = db.query(Question).order_by(func.random()).limit(remaining).all()
            questions = age_specific + [q for q in extra if q not in age_specific][:remaining]
        else:
            questions = age_specific
    else:
        questions = query.order_by(func.random()).limit(total_questions).all()

    if not questions:
        logger.warning("No questions found in database")
        return []

    # Personalize per child
    result: List[PersonalizedQuestion] = []
    for question in questions:
        personalized_text = question.question_text_template.replace("{child_name}", child.name)
        result.append(
            PersonalizedQuestion(
                child_id=child.id,
                child_name=child.name,
                question_id=question.id,
                question_text=personalized_text,
                options=question.options,
                category=question.category,
            )
        )

    logger.info(f"Generated {len(result)} personalized questions for child {child_id} (age: {child.age}, age_group: {age_group})")
    return result


def get_child_questions_full_coverage(
    db: Session,
    child_id: int,
    per_category: int = 1,
    categories: List[str] | None = None,
) -> List[PersonalizedQuestion]:
    """Fetch personalized questions ensuring coverage across all categories.

    Strategy:
    - Determine child's age_group (same logic as get_child_questions).
    - For each category, attempt to fetch `per_category` random questions matching age_group.
      If insufficient, fill remaining from any age.
    - Personalize with child name.
    """
    # Fetch child record
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        logger.info(f"Child {child_id} not found when fetching full-coverage questions")
        return []

    # Determine age group
    age_group = None
    if child.age:
        if 6 <= child.age <= 8:
            age_group = "6-8"
        elif 9 <= child.age <= 11:
            age_group = "9-11"
        elif 12 <= child.age <= 14:
            age_group = "12-14"

    # Desired ordering of full 9 aspects (extendable later)
    desired_order = [
        "emotional", "social", "physical", "behavioral", "religious",
        "moral", "habitual", "cognitive", "spiritual"
    ]

    if not categories:
        # Fetch distinct existing categories (case-sensitive original values)
        existing_rows = [c[0] for c in db.query(Question.category).distinct().all() if c[0]]
        existing_normalized = {c.lower(): c for c in existing_rows}

        # Auto-seed missing categories so endpoint can always show all aspects
        missing = [cat for cat in desired_order if cat not in existing_normalized]
        if missing:
            logger.info(f"Seeding placeholder questions for missing categories: {missing}")
            for cat in missing:
                # Create a generic placeholder question template; age_group left null for broad applicability
                placeholder = Question(
                    question_text_template=f"Placeholder: How is {{child_name}} doing in {cat} today?",
                    category=cat,
                    options=["Yes", "No", "Sometimes"],
                    weight=1,
                )
                db.add(placeholder)
            db.commit()
            # Refresh existing categories after seeding
            existing_rows = [c[0] for c in db.query(Question.category).distinct().all() if c[0]]
            existing_normalized = {c.lower(): c for c in existing_rows}

        # Order according to desired_order, using original casing if present
        categories = [existing_normalized.get(cat, cat) for cat in desired_order]

    results: List[PersonalizedQuestion] = []

    for cat in categories:
        # First try age-specific
        q = db.query(Question).filter(Question.category == cat)
        age_specific: List[Question] = []
        if age_group:
            age_specific = (
                q.filter(Question.age_group.ilike(f"%{age_group}%"))
                .order_by(func.random())
                .limit(per_category)
                .all()
            )

        selected: List[Question] = list(age_specific)
        if len(selected) < per_category:
            remaining = per_category - len(selected)
            extra = (
                db.query(Question)
                .filter(Question.category == cat)
                .order_by(func.random())
                .limit(remaining)
                .all()
            )
            # Avoid duplicates
            for qx in extra:
                if qx not in selected:
                    selected.append(qx)
                if len(selected) >= per_category:
                    break

        # Personalize
        for question in selected:
            personalized_text = question.question_text_template.replace("{child_name}", child.name)
            results.append(
                PersonalizedQuestion(
                    child_id=child.id,
                    child_name=child.name,
                    question_id=question.id,
                    question_text=personalized_text,
                    options=question.options,
                    category=question.category,
                )
            )

    logger.info(
        f"Generated {len(results)} full-coverage questions for child {child_id} "
        f"(per_category={per_category}, age_group={age_group})"
    )
    return results


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


def submit_child_responses(
    db: Session,
    child_id: int,
    responses: List[Dict]
) -> Dict[str, int]:
    """Store parent's answers for a single child and compute totals.

    Args:
        db: Database session
        child_id: Child's user ID
        responses: List of dicts with keys {question_id, answer}

    Returns:
        Dict with total_score and total_questions saved
    """
    # Fetch child once for name replacement
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        logger.warning(f"Child {child_id} not found; cannot submit responses")
        return {"total_score": 0, "total_questions": 0}

    total_score = 0
    total_questions = 0

    for item in responses:
        qid = item.get("question_id")
        ans = item.get("answer")
        if qid is None or ans is None:
            logger.warning("Invalid response item; missing question_id or answer; skipping")
            continue

        question = db.query(Question).filter(Question.id == qid).first()
        if not question:
            logger.warning(f"Question {qid} not found; skipping")
            continue

        personalized_text = question.question_text_template.replace("{child_name}", child.name)
        score = calculate_score(str(ans), question.weight)

        behavior_response = ChildBehaviorResponse(
            child_id=child_id,
            question_id=qid,
            question_text=personalized_text,
            answer=str(ans),
            score=score,
        )
        db.add(behavior_response)
        total_score += score
        total_questions += 1

    db.commit()
    logger.info(
        f"Saved {total_questions} responses for child {child_id} with total score {total_score}"
    )
    return {"total_score": total_score, "total_questions": total_questions}


def get_child_behavior_stats(
    db: Session,
    child_id: int,
    days: int | None = None,
) -> Dict:
    """Compute behavior stats for a child based on stored responses.

    Stats are calculated as percentage = sum(scores) / sum(max_scores) * 100.
    Category breakdown is computed similarly using Question.category.

    Args:
        db: DB session
        child_id: child's user id
        days: optional time window to include recent responses only

    Returns:
        Dict with overall percentage, category breakdown, counts, last updated
    """
    from datetime import datetime, timedelta

    q = (
        db.query(ChildBehaviorResponse, Question)
        .join(Question, ChildBehaviorResponse.question_id == Question.id)
        .filter(ChildBehaviorResponse.child_id == child_id)
    )
    if days and days > 0:
        since = datetime.utcnow() - timedelta(days=days)
        q = q.filter(ChildBehaviorResponse.timestamp >= since)

    rows = q.all()
    if not rows:
        return {
            "child_id": child_id,
            "total_responses": 0,
            "behavior_level": 0.0,
            "islamic_knowledge": 0.0,
            "categories": {},
            "last_response_at": None,
        }

    total_score = 0
    total_max = 0
    by_cat: Dict[str, Dict[str, float]] = {}
    last_ts = None

    for resp, question in rows:
        weight = max(question.weight or 1, 1)
        total_score += resp.score or 0
        total_max += weight

        cat = (question.category or "uncategorized").lower()
        d = by_cat.setdefault(cat, {"score": 0.0, "max": 0.0})
        d["score"] += resp.score or 0
        d["max"] += weight

        if not last_ts or (resp.timestamp and resp.timestamp > last_ts):
            last_ts = resp.timestamp

    def pct(s: float, m: float) -> float:
        return round((s / m) * 100.0, 2) if m > 0 else 0.0

    categories_pct = {k: pct(v["score"], v["max"]) for k, v in by_cat.items()}
    behavior_level = pct(total_score, total_max)

    # Attempt to map an "Islamic Knowledge" category if present
    isl_keys = [k for k in categories_pct.keys() if k in {"islamic", "knowledge", "islamic_knowledge", "spiritual"}]
    islamic_knowledge = categories_pct.get(isl_keys[0], 0.0) if isl_keys else 0.0

    return {
        "child_id": child_id,
        "total_responses": len(rows),
        "behavior_level": behavior_level,
        "islamic_knowledge": islamic_knowledge,
        "categories": categories_pct,
        "last_response_at": last_ts.isoformat() if last_ts else None,
    }


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
