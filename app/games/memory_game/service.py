"""Service logic for Memory Card Match game analysis and persistence."""

from sqlalchemy.orm import Session
from typing import Dict

from app.db.models.game_results import ChildGameResult


def analyze_memory_game(total_flips: int, correct_matches: int, wrong_matches: int, time_taken_seconds: int) -> Dict:
    """Compute analysis metrics for Memory Card game.

    Returns a dict with cognitive and focus scores.
    """
    focus_score = 0.0
    memory_score = 0.0
    try:
        focus_score = (correct_matches / max(total_flips, 1)) * 100.0
    except Exception:
        focus_score = 0.0
    total_attempts = correct_matches + wrong_matches
    try:
        memory_score = (correct_matches / max(total_attempts, 1)) * 100.0
    except Exception:
        memory_score = 0.0

    # Map to behavior categories (cognitive as primary)
    cognitive = round(memory_score)
    focus = round(focus_score)
    return {"cognitive": cognitive, "focus": focus}


def save_memory_game_result(
    db: Session,
    child_id: int,
    total_flips: int,
    correct_matches: int,
    wrong_matches: int,
    time_taken_seconds: int,
) -> ChildGameResult:
    """Persist raw result and analysis for Memory Card game."""
    raw = {
        "total_flips": total_flips,
        "correct": correct_matches,
        "wrong": wrong_matches,
        "time": time_taken_seconds,
    }
    analysis = analyze_memory_game(total_flips, correct_matches, wrong_matches, time_taken_seconds)

    result = ChildGameResult(
        child_id=child_id,
        game_type="memory",
        raw_result=raw,
        analysis_score=analysis,
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result
