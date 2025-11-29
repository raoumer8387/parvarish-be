"""Message ORM model.

Persists individual chat messages. A message may optionally be associated with a
specific child (when parent requests personalized guidance) or be general advice
when ``child_id`` is null.

Columns
-------
id: PK
user_id: FK -> users.id (owner of the conversation)
child_id: Optional FK -> children.id (context child) NULL for general advice
role: "user" | "assistant" | "system"
content: Full text of the message (can be long)
created_at: Timestamp
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func

from app.db.base import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    child_id = Column(Integer, ForeignKey("children.id", ondelete="SET NULL"), nullable=True, index=True)
    role = Column(String, nullable=False)  # e.g., "user" | "assistant" | "system"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
