"""Message CRUD operations.

Provides helper functions for creating and listing chat messages. Each message
can optionally be tied to a specific child (personalized advice) or be general
advice (child_id = None).
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import asc

from app.db.models.message import Message


def create_message(
    db: Session,
    user_id: int,
    role: str,
    content: str,
    child_id: Optional[int] = None,
) -> Message:
    """Persist a single chat message.

    Args:
        db: Active SQLAlchemy session
        user_id: Owner user id
        role: "user" | "assistant" | "system"
        content: Message text
        child_id: Optional child context
    Returns:
        The created Message ORM instance
    """
    message = Message(user_id=user_id, role=role, content=content, child_id=child_id)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def list_messages_for_user(
    db: Session,
    user_id: int,
    child_id: Optional[int] = None,
    limit: Optional[int] = None,
) -> List[Message]:
    """Return ordered messages for a user optionally filtered by child.

    Args:
        db: Session
        user_id: User whose chat history to retrieve
        child_id: Optional child context (None => general advice history)
        limit: Optional max number of messages (most recent if provided)
    """
    q = db.query(Message).filter(Message.user_id == user_id)
    if child_id is None:
        q = q.filter(Message.child_id.is_(None))
    else:
        q = q.filter(Message.child_id == child_id)

    q = q.order_by(asc(Message.created_at))
    messages = q.all()
    if limit and len(messages) > limit:
        # Return last `limit` messages preserving order
        messages = messages[-limit:]
    return messages


def list_recent_messages(
    db: Session,
    user_id: int,
    child_id: Optional[int] = None,
    limit: int = 20,
) -> List[Message]:
    """Convenience wrapper to fetch limited recent messages (ascending order)."""
    return list_messages_for_user(db, user_id=user_id, child_id=child_id, limit=limit)
