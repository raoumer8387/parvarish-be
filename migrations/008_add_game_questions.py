"""Migration to add game question tables: mood_scenarios, scenario_questions, islamic_quiz_questions."""

from sqlalchemy import Table, Column, Integer, String, Text, MetaData, create_engine
from sqlalchemy.dialects.postgresql import JSONB
import os
import sys
from pathlib import Path

# Attempt to import app settings; fallback to env var
SETTINGS_DB_URL = None
try:
    from app.core.config import settings  # type: ignore
    SETTINGS_DB_URL = getattr(settings, "SQLALCHEMY_DATABASE_URI", None) or getattr(settings, "DATABASE_URL", None)
except Exception:
    project_root = Path(__file__).resolve().parents[1]
    sys.path.append(str(project_root))
    try:
        from app.core.config import settings  # type: ignore
        SETTINGS_DB_URL = getattr(settings, "SQLALCHEMY_DATABASE_URI", None) or getattr(settings, "DATABASE_URL", None)
    except Exception:
        SETTINGS_DB_URL = None


def upgrade(engine):
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    # MoodScenario table
    if "mood_scenarios" not in metadata.tables:
        mood_scenarios = Table(
            "mood_scenarios",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("age_group", String, nullable=False),
            Column("scenario_text_en", Text, nullable=False),
            Column("scenario_text_ur", Text, nullable=True),
            Column("category", String, nullable=False),
            Column("mood_weights", JSONB, nullable=False),
            Column("tags", JSONB, default=[]),
        )
        mood_scenarios.create(bind=engine, checkfirst=True)
    
    # ScenarioQuestion table
    if "scenario_questions" not in metadata.tables:
        scenario_questions = Table(
            "scenario_questions",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("age_group", String, nullable=False),
            Column("question_text_en", Text, nullable=False),
            Column("question_text_ur", Text, nullable=True),
            Column("category", String, nullable=False),
            Column("options", JSONB, nullable=False),
            Column("tags", JSONB, default=[]),
        )
        scenario_questions.create(bind=engine, checkfirst=True)
    
    # IslamicQuizQuestion table
    if "islamic_quiz_questions" not in metadata.tables:
        islamic_quiz = Table(
            "islamic_quiz_questions",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("age_group", String, nullable=False),
            Column("question_text_en", Text, nullable=False),
            Column("question_text_ur", Text, nullable=True),
            Column("category", String, nullable=False),
            Column("options", JSONB, nullable=False),
            Column("correct_answer", String, nullable=False),
            Column("explanation_en", Text, nullable=True),
            Column("explanation_ur", Text, nullable=True),
            Column("difficulty", Integer, default=1),
            Column("tags", JSONB, default=[]),
        )
        islamic_quiz.create(bind=engine, checkfirst=True)


def downgrade(engine):
    metadata = MetaData()
    metadata.reflect(bind=engine)
    for tbl in ["islamic_quiz_questions", "scenario_questions", "mood_scenarios"]:
        if tbl in metadata.tables:
            metadata.tables[tbl].drop(bind=engine)


if __name__ == "__main__":
    db_url = SETTINGS_DB_URL or os.environ.get("DATABASE_URL") or os.environ.get("SQLALCHEMY_DATABASE_URI")
    if not db_url:
        raise SystemExit("DATABASE_URL or SQLALCHEMY_DATABASE_URI environment variable not set.")
    engine = create_engine(db_url)
    print(f"Running migration 008_add_game_questions against: {db_url}")
    upgrade(engine)
    print("Migration completed: game question tables ensured.")
