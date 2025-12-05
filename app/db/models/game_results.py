"""Models for child game results and analysis scores."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class ChildGameResult(Base):
    """Stores game outcomes linked to a child, with raw and analyzed scores.

    Table: child_game_results
    - id: UUID primary key
    - child_id: FK to children.id
    - game_type: one of [memory, mood, scenario, islamic_quiz]
    - raw_result: JSON payload from the game submission
    - analysis_score: JSON mapping behavior categories to numeric scores
    - created_at: timestamp (UTC)
    """

    __tablename__ = "child_game_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False, index=True)
    game_type = Column(String, nullable=False, index=True)
    # Use JSONB if available (PostgreSQL); otherwise JSONB falls back to JSON
    raw_result = Column(JSONB, nullable=False)
    analysis_score = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
