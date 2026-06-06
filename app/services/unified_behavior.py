"""Unified child behavior analysis across daily check-ins, games, and tasks.

All three data sources feed one canonical category model so the parent
dashboard reflects upgrades/downgrades whenever any source changes.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.db.models.behavior_models import ChildBehaviorResponse, Question
from app.db.models.child import Child
from app.db.models.child_task import ChildTask
from app.db.models.game_results import ChildGameResult
from app.services.lacking_analyzer import get_child_lacking_analysis
from app.services.parent_realtime import schedule_parent_realtime_message

CANONICAL_CATEGORIES = [
    "emotional",
    "social",
    "moral",
    "habitual",
    "cognitive",
    "physical",
    "spiritual",
]

# Daily check-in DB categories → canonical
CHECKIN_CATEGORY_MAP: Dict[str, str] = {
    "behavioral": "habitual",
    "religious": "moral",
    "islamic": "moral",
    "islamic_knowledge": "spiritual",
}

# Game analysis_score keys → canonical
GAME_SCORE_MAP: Dict[str, str] = {
    "emotional": "emotional",
    "emotional_control": "emotional",
    "empathy": "social",
    "social": "social",
    "moral": "moral",
    "cognitive": "cognitive",
    "focus": "cognitive",
    "spiritual": "spiritual",
}

WEIGHTS = {
    "checkin": 0.35,
    "games": 0.35,
    "tasks": 0.30,
}

CHANGE_THRESHOLD = 5.0  # points difference to count as upgrade/downgrade


def _normalize_checkin_category(raw: str) -> str:
    key = (raw or "uncategorized").lower()
    return CHECKIN_CATEGORY_MAP.get(key, key)


def _map_game_key(raw: str) -> Optional[str]:
    return GAME_SCORE_MAP.get((raw or "").lower())


def _window(offset_days: int, span_days: int) -> Tuple[datetime, datetime]:
    end = datetime.utcnow() - timedelta(days=offset_days)
    start = end - timedelta(days=span_days)
    return start, end


def _scores_from_checkins(
    db: Session,
    child_id: int,
    days: int,
    *,
    offset_days: int = 0,
) -> Dict[str, float]:
    start, end = _window(offset_days, days)
    rows = (
        db.query(ChildBehaviorResponse, Question)
        .join(Question, ChildBehaviorResponse.question_id == Question.id)
        .filter(
            and_(
                ChildBehaviorResponse.child_id == child_id,
                ChildBehaviorResponse.timestamp >= start,
                ChildBehaviorResponse.timestamp < end,
            )
        )
        .all()
    )
    if not rows:
        return {}

    by_cat: Dict[str, Dict[str, float]] = {}
    for resp, question in rows:
        weight = max(question.weight or 1, 1)
        canon = _normalize_checkin_category(question.category or "")
        if canon not in CANONICAL_CATEGORIES:
            continue
        slot = by_cat.setdefault(canon, {"score": 0.0, "max": 0.0})
        slot["score"] += resp.score or 0
        slot["max"] += weight

    out: Dict[str, float] = {}
    for cat, vals in by_cat.items():
        if vals["max"] > 0:
            out[cat] = round((vals["score"] / vals["max"]) * 100, 1)
    return out


def _scores_from_games(
    db: Session,
    child_id: int,
    days: int,
    *,
    offset_days: int = 0,
) -> Dict[str, float]:
    start, end = _window(offset_days, days)
    results = (
        db.query(ChildGameResult)
        .filter(
            and_(
                ChildGameResult.child_id == child_id,
                ChildGameResult.created_at >= start,
                ChildGameResult.created_at < end,
            )
        )
        .all()
    )
    buckets: Dict[str, List[float]] = {}
    for row in results:
        for key, val in (row.analysis_score or {}).items():
            canon = _map_game_key(str(key))
            if not canon:
                continue
            try:
                buckets.setdefault(canon, []).append(float(val))
            except (TypeError, ValueError):
                continue
    return {k: round(sum(v) / len(v), 1) for k, v in buckets.items()}


def _scores_from_tasks(
    db: Session,
    child_id: int,
    days: int,
    *,
    offset_days: int = 0,
) -> Dict[str, float]:
    """Task completion rate per category (0–100). No tasks in a category → omitted."""
    start, end = _window(offset_days, days)
    tasks = (
        db.query(ChildTask)
        .filter(
            and_(
                ChildTask.child_id == child_id,
                ChildTask.created_at >= start,
                ChildTask.created_at < end,
            )
        )
        .all()
    )
    by_cat: Dict[str, Dict[str, int]] = {}
    for task in tasks:
        cat = (task.category or "").lower()
        if cat not in CANONICAL_CATEGORIES:
            continue
        slot = by_cat.setdefault(cat, {"total": 0, "completed": 0})
        slot["total"] += 1
        if task.status == "completed":
            slot["completed"] += 1
    out: Dict[str, float] = {}
    for cat, counts in by_cat.items():
        if counts["total"] > 0:
            out[cat] = round((counts["completed"] / counts["total"]) * 100, 1)
    return out


def _merge_category_scores(
    checkin: Dict[str, float],
    games: Dict[str, float],
    tasks: Dict[str, float],
) -> Dict[str, float]:
    unified: Dict[str, float] = {}
    for cat in CANONICAL_CATEGORIES:
        parts: List[Tuple[float, float]] = []
        if cat in checkin:
            parts.append((checkin[cat], WEIGHTS["checkin"]))
        if cat in games:
            parts.append((games[cat], WEIGHTS["games"]))
        if cat in tasks:
            parts.append((tasks[cat], WEIGHTS["tasks"]))
        if not parts:
            continue
        total_w = sum(w for _, w in parts)
        unified[cat] = round(sum(s * w for s, w in parts) / total_w, 1)
    return unified


def _detect_changes(
    current: Dict[str, float],
    previous: Dict[str, float],
) -> Dict[str, str]:
    changes: Dict[str, str] = {}
    all_cats = set(current) | set(previous)
    for cat in all_cats:
        cur = current.get(cat)
        prev = previous.get(cat)
        if cur is None and prev is not None:
            changes[cat] = "downgraded"
        elif cur is not None and prev is None:
            changes[cat] = "new"
        elif cur is None and prev is None:
            continue
        else:
            delta = cur - prev  # type: ignore[operator]
            if delta >= CHANGE_THRESHOLD:
                changes[cat] = "upgraded"
            elif delta <= -CHANGE_THRESHOLD:
                changes[cat] = "downgraded"
            else:
                changes[cat] = "stable"
    return changes


def _last_activity_timestamps(db: Session, child_id: int) -> Dict[str, Optional[str]]:
    last_checkin = (
        db.query(ChildBehaviorResponse)
        .filter(ChildBehaviorResponse.child_id == child_id)
        .order_by(desc(ChildBehaviorResponse.timestamp))
        .first()
    )
    last_game = (
        db.query(ChildGameResult)
        .filter(ChildGameResult.child_id == child_id)
        .order_by(desc(ChildGameResult.created_at))
        .first()
    )
    last_task = (
        db.query(ChildTask)
        .filter(ChildTask.child_id == child_id)
        .order_by(desc(ChildTask.created_at))
        .first()
    )

    def _iso(obj, attr: str) -> Optional[str]:
        if not obj:
            return None
        ts = getattr(obj, attr, None)
        return ts.isoformat() if ts else None

    return {
        "last_check_in": _iso(last_checkin, "timestamp"),
        "last_game": _iso(last_game, "created_at"),
        "last_task": _iso(last_task, "created_at"),
    }


def get_unified_behavior_analysis(
    db: Session,
    child_id: int,
    days: int = 30,
    *,
    include_skill_areas: bool = True,
) -> Dict[str, Any]:
    """Compute interlinked behavior scores from check-ins, games, and tasks."""
    checkin_scores = _scores_from_checkins(db, child_id, days)
    game_scores = _scores_from_games(db, child_id, days)
    task_scores = _scores_from_tasks(db, child_id, days)
    unified_scores = _merge_category_scores(checkin_scores, game_scores, task_scores)

    prev_checkin = _scores_from_checkins(db, child_id, days, offset_days=days)
    prev_games = _scores_from_games(db, child_id, days, offset_days=days)
    prev_tasks = _scores_from_tasks(db, child_id, days, offset_days=days)
    prev_unified = _merge_category_scores(prev_checkin, prev_games, prev_tasks)
    category_changes = _detect_changes(unified_scores, prev_unified)

    overall = round(sum(unified_scores.values()) / len(unified_scores), 1) if unified_scores else 0.0
    strongest = max(unified_scores.items(), key=lambda x: x[1])[0] if unified_scores else None
    weakest = min(unified_scores.items(), key=lambda x: x[1])[0] if unified_scores else None

    upgraded = [c for c, s in category_changes.items() if s == "upgraded"]
    downgraded = [c for c, s in category_changes.items() if s == "downgraded"]

    skill_areas: Dict[str, Any] = {}
    if include_skill_areas:
        try:
            lacking = get_child_lacking_analysis(db, child_id, days=min(days, 14))
            skill_areas = {
                "lacking_areas": lacking.get("lacking_areas", []),
                "all_areas": lacking.get("all_areas", []),
                "requires_attention": lacking.get("requires_attention", False),
            }
        except Exception:
            skill_areas = {"lacking_areas": [], "all_areas": [], "requires_attention": False}

    timestamps = _last_activity_timestamps(db, child_id)

    return {
        "child_id": child_id,
        "period_days": days,
        "overall_score": overall,
        "unified_scores": unified_scores,
        "category_changes": category_changes,
        "upgraded_categories": upgraded,
        "downgraded_categories": downgraded,
        "strongest_category": strongest,
        "weakest_category": weakest,
        "sources": {
            "daily_checkin": checkin_scores,
            "games": game_scores,
            "tasks": task_scores,
        },
        "skill_areas": skill_areas,
        "data_freshness": timestamps,
        "analyzed_at": datetime.utcnow().isoformat(),
    }


def refresh_and_notify_dashboard(
    db: Session,
    child_id: int,
    trigger_source: str,
    *,
    days: int = 30,
) -> Dict[str, Any]:
    """Recompute unified analysis and push a dashboard_update to the parent."""
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        return {}

    analysis = get_unified_behavior_analysis(db, child_id, days=days)

    upgraded = analysis.get("upgraded_categories") or []
    downgraded = analysis.get("downgraded_categories") or []
    overall = analysis.get("overall_score", 0)

    if downgraded:
        change_hint = f"Needs attention: {', '.join(downgraded)}"
    elif upgraded:
        change_hint = f"Improved: {', '.join(upgraded)}"
    else:
        change_hint = f"Overall score {overall:.0f}%"

    trigger_labels = {
        "daily_checkin": "daily check-in",
        "game": "game session",
        "task": "task update",
        "lacking_analysis": "skill analysis",
    }
    source_label = trigger_labels.get(trigger_source, trigger_source)

    message = {
        "type": "dashboard_update",
        "title": f"{child.name}'s progress updated",
        "body": f"Updated after {source_label}. {change_hint}.",
        "data": {
            "child_id": child_id,
            "child_name": child.name,
            "trigger": trigger_source,
            "unified_analysis": analysis,
        },
        "created_at": datetime.utcnow().isoformat(),
    }
    schedule_parent_realtime_message(child.parent_id, message)
    return analysis
