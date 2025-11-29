"""Model for child tasks generated from chatbot responses or behavior analysis."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.db.base import Base


class ChildTask(Base):
    """Represents an actionable task for a child.

    Tasks can be generated from chatbot interactions or daily behavior questions.
    Categories must align with behavior tracking categories to enable unified analysis.
    Duplicate tasks for the same (child, category) are avoided within a 7 day window by service logic.
    Note: attribute name `metadata` is reserved by SQLAlchemy; using `meta` for JSON payload.
    """
    __tablename__ = "child_tasks"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)  # emotional, social, moral, habitual, cognitive, physical
    xp_reward = Column(Integer, nullable=False, default=10)
    difficulty = Column(Integer, nullable=False, default=1)  # 1=easy .. higher = harder
    status = Column(String(20), nullable=False, default="pending")  # pending | completed
    source = Column(String(30), nullable=False)  # chatbot | daily_question
    meta = Column(JSON, nullable=True)  # arbitrary auxiliary info (chatbot_response, question_id, etc.)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
