"""Migration: Add child_tasks table for task generation system.

Run with: python migrations/004_add_child_tasks.py

If you see ModuleNotFoundError: No module named 'app', ensure the project root
is on PYTHONPATH or run from repository root.
"""

import sys
import os

# Ensure project root (parent of migrations/) is on sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import inspect
from app.db.session import engine
from app.db.base import Base
from app.db.models.child_task import ChildTask


def run_migration():
    inspector = inspect(engine)
    existing = inspector.get_table_names()
    print("🔍 Existing tables:", existing)
    if "child_tasks" in existing:
        print("✅ child_tasks table already exists. Skipping creation.")
        return
    print("📦 Creating child_tasks table...")
    Base.metadata.create_all(bind=engine, tables=[ChildTask.__table__])
    print("✅ child_tasks table created successfully.")


if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
