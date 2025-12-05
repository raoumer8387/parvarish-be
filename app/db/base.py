"""SQLAlchemy declarative base.

Defines the Base class for ORM models and ensures models are imported for metadata."""

from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import models to register with metadata (avoid circulars by limiting imports)
# NOTE: Keep lightweight; do not import large modules here.
try:
    # Existing behavior models
    from app.db.models.behavior_models import Question, ChildBehaviorResponse  # noqa: F401
    # Children/Parent
    from app.db.models.child import Child  # noqa: F401
    from app.db.models.parent import Parent  # noqa: F401
    # Tasks
    from app.db.models.child_task import ChildTask  # noqa: F401
    # New: Game results
    from app.db.models.game_results import ChildGameResult  # noqa: F401
    # Game questions
    from app.db.models.game_questions import MoodScenario, ScenarioQuestion, IslamicQuizQuestion  # noqa: F401
except Exception:
    # In some tooling contexts, imports may fail; metadata will still work once app loads.
    pass