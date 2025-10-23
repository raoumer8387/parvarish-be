"""Configuration utilities using environment variables.

Loads environment variables and provides accessors for common settings.
"""

import os
from dotenv import load_dotenv

# Load variables from a .env file if present
load_dotenv()


def get_database_url() -> str:
    """Return DATABASE_URL from environment (placeholder)."""
    return os.getenv("DATABASE_URL", "postgresql+psycopg2://user:password@localhost:5432/parvarish")
