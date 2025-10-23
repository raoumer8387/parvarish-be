"""User CRUD operations (placeholders).

Define functions to create, retrieve, update, and delete users.
"""

from sqlalchemy.orm import Session

# from app.db import models

def create_user(db: Session, *args, **kwargs):
    """Create a new user in the database (placeholder)."""
    raise NotImplementedError

def get_user_by_email(db: Session, email: str):
    """Fetch a user by email (placeholder)."""
    raise NotImplementedError
