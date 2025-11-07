"""
Migration: Add parent and child support to database

This migration:
1. Adds username and user_type columns to users table (if missing)
2. Creates parents table (if not exists)
3. Creates children table (if not exists)

Run with: python migrations/001_add_parent_child_support.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from app.db.session import engine
from app.db.base import Base
from app.db.models.user import User
from app.db.models.parent import Parent
from app.db.models.child import Child

def column_exists(table_name, column_name):
    """Check if a column exists in a table."""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def table_exists(table_name):
    """Check if a table exists."""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def run_migration():
    """Run the migration."""
    print("Starting migration: Add parent and child support...")
    
    with engine.connect() as conn:
        # 1. Add username column to users table if it doesn't exist
        if table_exists('users'):
            if not column_exists('users', 'username'):
                print("  ✓ Adding 'username' column to users table...")
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN username VARCHAR(255) UNIQUE
                """))
                conn.commit()
                print("    Added username column")
            else:
                print("  ✓ Column 'username' already exists in users table")
            
            # 2. Add user_type column to users table if it doesn't exist
            if not column_exists('users', 'user_type'):
                print("  ✓ Adding 'user_type' column to users table...")
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN user_type VARCHAR(20)
                """))
                conn.commit()
                print("    Added user_type column")
            else:
                print("  ✓ Column 'user_type' already exists in users table")
        else:
            print("  ⚠ Users table does not exist. Creating all tables...")
    
    # 3. Create all tables (only creates if they don't exist)
    print("  ✓ Creating missing tables...")
    Base.metadata.create_all(bind=engine)
    
    # Verify tables
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print("\n✅ Migration completed successfully!")
    print(f"\nExisting tables: {', '.join(tables)}")
    
    if 'users' in tables:
        user_columns = [col['name'] for col in inspector.get_columns('users')]
        print(f"Users table columns: {', '.join(user_columns)}")
    
    if 'parents' in tables:
        parent_columns = [col['name'] for col in inspector.get_columns('parents')]
        print(f"Parents table columns: {', '.join(parent_columns)}")
    
    if 'children' in tables:
        child_columns = [col['name'] for col in inspector.get_columns('children')]
        print(f"Children table columns: {', '.join(child_columns)}")

if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
