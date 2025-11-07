"""User ORM model for authentication and profile management."""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)  # Nullable for child users
    username = Column(String, unique=True, index=True, nullable=True)  # For child users
    hashed_password = Column(String, nullable=True)  # Nullable for Google OAuth users
    
    # User type: 'parent' or 'child'
    user_type = Column(String, nullable=True)
    
    # Google OAuth fields
    google_id = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, nullable=True)
    picture = Column(String, nullable=True)  # Profile picture URL from Google
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
