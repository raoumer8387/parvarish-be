"""Message CRUD operations (placeholders).

Define functions to create and list messages for conversations.
"""

from sqlalchemy.orm import Session

def create_message(db: Session, *args, **kwargs):
    """Insert a new message (placeholder)."""
    raise NotImplementedError

def list_messages_for_user(db: Session, user_id: int):
    """List messages for a user (placeholder)."""
    raise NotImplementedError
