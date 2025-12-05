"""
Migration: Add child context support to chat messages.

Adds optional child_id column to messages table for personalized conversations
and ensures content column can store long assistant replies (TEXT).

Run with: python migrations/006_add_chat_child_context.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text
from app.db.session import engine


def column_exists(table_name: str, column_name: str) -> bool:
    inspector = inspect(engine)
    return column_name in [c['name'] for c in inspector.get_columns(table_name)]


def run_migration():
    print("Starting migration: Add child_id to messages table ...")
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    if 'messages' not in tables:
        print("  ❌ messages table does not exist. Create base tables first.")
        return

    with engine.connect() as conn:
        # 1. Add child_id column if missing
        if not column_exists('messages', 'child_id'):
            print("  ✓ Adding child_id column ...")
            conn.execute(text("""
                ALTER TABLE messages
                ADD COLUMN child_id INTEGER NULL REFERENCES children(id) ON DELETE SET NULL
            """))
            conn.commit()
        else:
            print("  ✓ child_id column already exists; skipping")

        # 2. Ensure content column is TEXT (for longer responses)
        # Simple heuristic: attempt ALTER; if fails ignore.
        try:
            print("  ✓ Ensuring content column is TEXT ...")
            conn.execute(text("""
                ALTER TABLE messages
                ALTER COLUMN content TYPE TEXT
            """))
            conn.commit()
        except Exception as e:
            print(f"    ⚠ Could not alter content column to TEXT (may already be TEXT or dialect unsupported): {e}")

    # Show final columns
    final_cols = [c['name'] for c in inspector.get_columns('messages')]
    print(f"\n✅ Migration complete. messages columns: {', '.join(final_cols)}")


if __name__ == '__main__':
    try:
        run_migration()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
