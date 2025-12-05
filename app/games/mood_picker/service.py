"""Service logic for Mood Picker game."""

from sqlalchemy.orm import Session
from typing import Dict

from app.db.models.game_results import ChildGameResult
from app.db.models.game_questions import MoodScenario


def analyze_mood(db: Session, scenario_id: int, selected_mood: str) -> Dict:
    """Map mood to emotional analysis scores based on DB scenario weights."""
    scenario = db.query(MoodScenario).filter(MoodScenario.id == scenario_id).first()
    if not scenario or not scenario.mood_weights:
        # Fallback to default weights if scenario not found
        default_weights = {"Anger": -5, "Forgive": +5, "Happy": +3, "Sad": 0}
        weight = default_weights.get(selected_mood, 0)
    else:
        weight = scenario.mood_weights.get(selected_mood, 0)
    
    # Map weight to percentage scores
    emotional_control = max(0, min(100, 50 + weight * 10))
    empathy = max(0, min(100, 50 + (5 if selected_mood == "Forgive" else 0)))
    return {"emotional_control": emotional_control, "empathy": empathy}


def save_mood_result(
    db: Session,
    child_id: int,
    scenario_id: int,
    selected_mood: str,
) -> ChildGameResult:
    raw = {"scenario_id": scenario_id, "selected_mood": selected_mood}
    analysis = analyze_mood(db, scenario_id, selected_mood)
    result = ChildGameResult(
        child_id=child_id,
        game_type="mood",
        raw_result=raw,
        analysis_score=analysis,
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result
