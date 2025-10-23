"""SQLAlchemy session and engine configuration.

Creates the database engine from environment configuration and provides
session factory utilities.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.utils.config import get_database_url


DATABASE_URL = get_database_url()

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency that provides a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
