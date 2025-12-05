"""Service logic for Scenario game (What Would You Do?)."""

from sqlalchemy.orm import Session
from typing import Dict

from app.db.models.game_results import ChildGameResult
from app.db.models.game_questions import ScenarioQuestion


def analyze_scenario(db: Session, scenario_id: int, selected_option: str) -> Dict:
    """Analyze scenario choice based on DB question weights."""
    question = db.query(ScenarioQuestion).filter(ScenarioQuestion.id == scenario_id).first()
    if not question or not question.options:
        # Fallback to default weights
        default_opts = {
            "Hit": {"moral": -10, "emotional": -5, "social": -5},
            "Forgive": {"moral": +10, "emotional": +5, "social": +3},
            "Tell teacher": {"moral": +5, "emotional": +2, "social": +4},
        }
        weights = default_opts.get(selected_option, {"moral": 0, "emotional": 0, "social": 0})
    else:
        # Find the matching option in DB
        weights = {"moral": 0, "emotional": 0, "social": 0}
        for opt in question.options:
            if opt.get("option") == selected_option:
                weights = {
                    "moral": opt.get("moral", 0),
                    "emotional": opt.get("emotional", 0),
                    "social": opt.get("social", 0),
                }
                break
    
    # Normalize to 0-100 with baseline 50
    def to_pct(val: int) -> int:
        return max(0, min(100, 50 + val * 5))

    return {
        "moral": to_pct(weights.get("moral", 0)),
        "emotional": to_pct(weights.get("emotional", 0)),
        "social": to_pct(weights.get("social", 0)),
    }


def save_scenario_result(
    db: Session,
    child_id: int,
    scenario_id: int,
    selected_option: str,
) -> ChildGameResult:
    raw = {"scenario_id": scenario_id, "selected_option": selected_option}
    analysis = analyze_scenario(db, scenario_id, selected_option)
    result = ChildGameResult(
        child_id=child_id,
        game_type="scenario",
        raw_result=raw,
        analysis_score=analysis,
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result
