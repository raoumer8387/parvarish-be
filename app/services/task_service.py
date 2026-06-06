"""Service logic for generating child tasks from chatbot responses and behavior data."""

from datetime import datetime, timedelta
from typing import List, Dict, Set, Tuple
import logging
import random

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.models.child_task import ChildTask
from app.db.models.behavior_models import ChildBehaviorResponse, Question
from app.services.behavior_service import get_child_behavior_stats
from app.services.task_templates import TASK_TEMPLATES, ALLOWED_CATEGORIES

logger = logging.getLogger(__name__)

# Keyword → category mapping (non-LLM heuristic)
KEYWORD_CATEGORY_MAP: Dict[str, str] = {
    "anger": "emotional",
    "angry": "emotional",
    "sad": "emotional",
    "focus": "cognitive",
    "attention": "cognitive",
    "lying": "moral",
    "truth": "moral",
    "routine": "habitual",
    "schedule": "habitual",
    "sharing": "social",
    "friend": "social",
    "active": "physical",
    "exercise": "physical",
}

LOW_SCORE_THRESHOLD = 50.0  # percentage threshold to consider category needs support
MAX_TASKS_PER_GENERATION = 3
DEDUPLICATION_WINDOW_DAYS = 7

# Map DB question categories to task categories
CATEGORY_ALIAS_MAP: Dict[str, str] = {
    # existing DB categories -> task categories
    "behavioral": "habitual",
    "religious": "moral",
    "islamic": "moral",
    "spiritual": "moral",
}


def _extract_categories_from_text(text: str) -> Tuple[Set[str], Set[str]]:
    """Extract categories from chatbot response using keyword mapping.

    Returns a tuple: (categories_found, keywords_detected)
    """
    detected_categories: Set[str] = set()
    detected_keywords: Set[str] = set()
    lower_text = text.lower()
    for kw, cat in KEYWORD_CATEGORY_MAP.items():
        if kw in lower_text:
            detected_keywords.add(kw)
            if cat in ALLOWED_CATEGORIES:
                detected_categories.add(cat)
    return detected_categories, detected_keywords


def _get_low_score_categories(db: Session, child_id: int, days: int = 3) -> List[str]:
    """Derive low-score categories from unified check-in + game + task analysis."""
    from app.services.unified_behavior import get_unified_behavior_analysis

    analysis = get_unified_behavior_analysis(
        db, child_id, days=days, include_skill_areas=False
    )
    low_categories: List[str] = []
    for cat, pct in (analysis.get("unified_scores") or {}).items():
        if cat in ALLOWED_CATEGORIES and pct < LOW_SCORE_THRESHOLD:
            low_categories.append(cat)

    if low_categories:
        return low_categories

    # Fallback when unified window has no merged data yet
    stats = get_child_behavior_stats(db, child_id, days=days)
    for raw_cat, pct in stats.get("categories", {}).items():
        cat = raw_cat.lower()
        if cat not in ALLOWED_CATEGORIES and cat in CATEGORY_ALIAS_MAP:
            cat = CATEGORY_ALIAS_MAP[cat]
        if cat in ALLOWED_CATEGORIES and pct < LOW_SCORE_THRESHOLD:
            if cat not in low_categories:
                low_categories.append(cat)
    return low_categories


def _recent_task_categories(db: Session, child_id: int) -> Set[str]:
    """Fetch categories already assigned tasks in the dedupe window."""
    window_start = datetime.utcnow() - timedelta(days=DEDUPLICATION_WINDOW_DAYS)
    rows = db.query(ChildTask.category).filter(
        and_(ChildTask.child_id == child_id, ChildTask.created_at >= window_start)
    ).all()
    return {r[0] for r in rows if r and r[0]}


def generate_tasks_from_chat(
    db: Session,
    child_id: int,
    chatbot_response: str,
    chatbot_tags: List[str] | None = None,
) -> Dict:
    """Generate up to MAX_TASKS_PER_GENERATION tasks for a child based on chatbot output and behavior trends.

    Logic:
    1. Use explicit chatbot_tags if provided (validated against allowed categories).
    2. Else extract categories via keyword mapping from chatbot_response.
    3. Add low-score categories from recent behavior stats.
    4. Remove categories that already have a task within the dedupe window.
    5. Select up to MAX_TASKS_PER_GENERATION categories, prioritizing explicit / extracted first then low-score.
    6. For each category, pick a random template task and persist.
    7. Return created tasks and diagnostic metadata.
    """
    explicit: List[str] = []
    if chatbot_tags:
        explicit = [c for c in chatbot_tags if c in ALLOWED_CATEGORIES]
        invalid = [c for c in chatbot_tags if c not in ALLOWED_CATEGORIES]
        if invalid:
            logger.info(f"Ignoring invalid chatbot tags for child {child_id}: {invalid}")

    extracted_categories, detected_keywords = _extract_categories_from_text(chatbot_response)
    low_score_categories = _get_low_score_categories(db, child_id)
    recent_categories = _recent_task_categories(db, child_id)

    # Priority ordering: explicit > extracted > low-score
    ordered: List[str] = []
    for group in (explicit, list(extracted_categories), low_score_categories):
        for cat in group:
            if cat not in ordered:
                ordered.append(cat)

    # Filter out already assigned categories within window
    candidate_categories = [c for c in ordered if c not in recent_categories]

    if not candidate_categories:
        logger.info(f"No new categories eligible for task generation for child {child_id}")
        return {
            "count": 0,
            "tasks": [],
            "categories_considered": ordered,
            "categories_low_score": low_score_categories,
            "keywords_detected": list(detected_keywords),
        }

    # Limit number of tasks
    selected_categories = candidate_categories[:MAX_TASKS_PER_GENERATION]

    created_tasks = []
    for cat in selected_categories:
        templates = TASK_TEMPLATES.get(cat, [])
        if not templates:
            logger.warning(f"No templates found for category '{cat}'")
            continue
        template = random.choice(templates)
        task = ChildTask(
            child_id=child_id,
            title=template["title"],
            description=template["description"],
            category=cat,
            xp_reward=10,
            difficulty=1,
            status="pending",
            source="chatbot",
            meta={
                "chatbot_response": chatbot_response,
                "keywords_detected": list(detected_keywords),
                "source_categories": ordered,
                "low_score_categories": low_score_categories,
            },
        )
        db.add(task)
        created_tasks.append(task)

    db.commit()
    # Refresh to get IDs
    for t in created_tasks:
        db.refresh(t)

    logger.info(f"Generated {len(created_tasks)} tasks for child {child_id} from categories: {selected_categories}")

    return {
        "count": len(created_tasks),
        "tasks": created_tasks,
        "categories_considered": ordered,
        "categories_low_score": low_score_categories,
        "keywords_detected": list(detected_keywords),
    }


def generate_tasks_from_scores(
    db: Session,
    child_id: int,
    days: int = 3,
    max_tasks: int = MAX_TASKS_PER_GENERATION,
):
    """Generate tasks based solely on recent low behavior categories.

    - Looks at recent behavior stats (days window)
    - Maps DB categories to task categories where needed
    - Avoids duplicates within DEDUPLICATION_WINDOW_DAYS
    - Creates up to `max_tasks` tasks
    - Sets source = "daily_question"
    """
    low_score_categories = _get_low_score_categories(db, child_id, days=days)
    if not low_score_categories:
        logger.info(f"No low-score categories for child {child_id} in last {days} days")
        return {"count": 0, "tasks": [], "categories_considered": [], "categories_low_score": [], "keywords_detected": []}

    recent_categories = _recent_task_categories(db, child_id)
    candidate_categories = [c for c in low_score_categories if c not in recent_categories]
    if not candidate_categories:
        logger.info(f"All low-score categories recently assigned for child {child_id}")
        return {"count": 0, "tasks": [], "categories_considered": low_score_categories, "categories_low_score": low_score_categories, "keywords_detected": []}

    selected = candidate_categories[: max(1, min(max_tasks, MAX_TASKS_PER_GENERATION))]
    created_tasks = []
    for cat in selected:
        templates = TASK_TEMPLATES.get(cat, [])
        if not templates:
            continue
        template = random.choice(templates)
        task = ChildTask(
            child_id=child_id,
            title=template["title"],
            description=template["description"],
            category=cat,
            xp_reward=10,
            difficulty=1,
            status="pending",
            source="daily_question",
            meta={
                "generation": "from_scores",
                "days": days,
                "low_score_categories": low_score_categories,
            },
        )
        db.add(task)
        created_tasks.append(task)

    db.commit()
    for t in created_tasks:
        db.refresh(t)

    return {
        "count": len(created_tasks),
        "tasks": created_tasks,
        "categories_considered": selected,
        "categories_low_score": low_score_categories,
        "keywords_detected": [],
    }


def list_child_tasks(
    db: Session,
    child_id: int,
    status: str | None = None,
    limit: int = 50,
):
    """List tasks for a child, optionally filtered by status, ordered by newest."""
    from app.db.models.child import Child
    
    q = db.query(ChildTask, Child.name).join(
        Child, ChildTask.child_id == Child.id
    ).filter(ChildTask.child_id == child_id).order_by(ChildTask.created_at.desc())
    
    if status in {"pending", "completed", "incomplete"}:
        q = q.filter(ChildTask.status == status)
    
    results = q.limit(limit).all()
    
    # Convert to dict with child_name
    tasks_with_names = []
    for task, child_name in results:
        task_dict = {
            "id": task.id,
            "child_id": task.child_id,
            "child_name": child_name,
            "title": task.title,
            "description": task.description,
            "category": task.category,
            "xp_reward": task.xp_reward,
            "difficulty": task.difficulty,
            "status": task.status,
            "source": task.source,
            "meta": task.meta,
            "created_at": task.created_at
        }
        tasks_with_names.append(task_dict)
    
    return tasks_with_names


def mark_task_completed(db: Session, task_id: int) -> ChildTask | None:
    """Mark a task as completed. Returns the updated task or None if not found."""
    task = db.query(ChildTask).filter(ChildTask.id == task_id).first()
    if not task:
        return None
    task.status = "completed"
    # record completion timestamp into meta for traceability
    now_iso = datetime.utcnow().isoformat()
    meta = task.meta or {}
    meta["completed_at"] = now_iso
    task.meta = meta
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task_status(db: Session, task_id: int, new_status: str) -> ChildTask | None:
    """Update task status. Returns the updated task or None if not found."""
    task = db.query(ChildTask).filter(ChildTask.id == task_id).first()
    if not task:
        return None
    
    old_status = task.status
    task.status = new_status
    now_iso = datetime.utcnow().isoformat()
    meta = task.meta or {}
    
    # Track status changes
    if new_status == "completed":
        meta["completed_at"] = now_iso
    elif new_status == "incomplete" and "completed_at" in meta:
        # Remove completion timestamp if marking as incomplete
        del meta["completed_at"]
    
    meta["last_status_change"] = now_iso
    meta["previous_status"] = old_status
    task.meta = meta
    
    db.add(task)
    db.commit()
    db.refresh(task)
    return task
