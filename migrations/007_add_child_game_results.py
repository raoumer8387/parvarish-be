"""Migration to add child_game_results table.

This is a simple SQLAlchemy-agnostic migration script that can be executed via project tooling.
"""

from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey, MetaData, create_engine
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import os
import sys
from pathlib import Path

# Attempt to import app settings; if unavailable (standalone run), use DATABASE_URL env var
SETTINGS_DB_URL = None
try:
    from app.core.config import settings  # type: ignore
    SETTINGS_DB_URL = getattr(settings, "SQLALCHEMY_DATABASE_URI", None)
except Exception:
    # Try to add project root to sys.path and retry
    project_root = Path(__file__).resolve().parents[1]
    sys.path.append(str(project_root))
    try:
        from app.core.config import settings  # type: ignore
        SETTINGS_DB_URL = getattr(settings, "SQLALCHEMY_DATABASE_URI", None)
    except Exception:
        SETTINGS_DB_URL = None


def upgrade(engine):
    # Reflect existing tables so FKs can resolve ('children' must be present)
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    # Check if table already exists
    if "child_game_results" in metadata.tables:
        print("Table child_game_results already exists, skipping creation.")
        return
    
    # Create new table definition
    child_game_results = Table(
        "child_game_results",
        metadata,
        Column("id", UUID(as_uuid=True), primary_key=True),
        Column("child_id", Integer, ForeignKey("children.id"), nullable=False, index=True),
        Column("game_type", String, nullable=False, index=True),
        Column("raw_result", JSONB, nullable=False),
        Column("analysis_score", JSONB, nullable=False),
        Column("created_at", DateTime(timezone=True), server_default=func.now()),
    )
    
    # Create the table
    child_game_results.create(bind=engine, checkfirst=True)


def downgrade(engine):
    metadata = MetaData()
    metadata.reflect(bind=engine)
    table = metadata.tables.get("child_game_results")
    if table is not None:
        table.drop(bind=engine)


if __name__ == "__main__":
    # Create engine from application settings or environment and run upgrade
    db_url = SETTINGS_DB_URL or os.environ.get("DATABASE_URL") or os.environ.get("SQLALCHEMY_DATABASE_URI")
    if not db_url:
        raise SystemExit("DATABASE_URL or SQLALCHEMY_DATABASE_URI environment variable not set, and app settings unavailable.")
    engine = create_engine(db_url)
    print(f"Running migration 007_add_child_game_results against: {db_url}")
    upgrade(engine)
    print("Migration completed: child_game_results table ensured.")
