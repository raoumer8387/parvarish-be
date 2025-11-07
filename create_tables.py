"""Script to create database tables."""

from app.db.base import Base
from app.db.session import engine
from app.db.models.user import User
from app.db.models.message import Message

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("✓ Tables created successfully!")
print("✓ users table is ready for Google OAuth")
