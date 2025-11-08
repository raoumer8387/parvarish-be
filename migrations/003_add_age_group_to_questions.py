"""
Migration: Add age_group column to questions table

This migration adds an age_group VARCHAR column to the questions table
to enable age-aware question selection (e.g., "6-8", "9-11", "12-14").

Run with: python migrations/003_add_age_group_to_questions.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from app.db.session import engine


def column_exists(table_name, column_name):
    """Check if a column exists in a table."""
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return False
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def run_migration():
    """Run the migration."""
    print("Starting migration: Add age_group to questions table...")
    
    with engine.connect() as conn:
        if not column_exists('questions', 'age_group'):
            print("  ✓ Adding 'age_group' column to questions table...")
            conn.execute(text("""
                ALTER TABLE questions 
                ADD COLUMN age_group VARCHAR(20)
            """))
            conn.commit()
            print("    Added age_group column")
        else:
            print("  ✓ Column 'age_group' already exists in questions table")
    
    print("\n✅ Migration completed successfully!")
    
    # Verify column
    inspector = inspect(engine)
    if 'questions' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('questions')]
        print(f"Questions table columns: {', '.join(columns)}")


if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
