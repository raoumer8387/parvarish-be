"""Quick script to check if game tables exist in database."""

from app.db.session import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text(
        "SELECT tablename FROM pg_tables "
        "WHERE schemaname = 'public' "
        "ORDER BY tablename"
    ))
    all_tables = [row[0] for row in result]
    
    print("All tables in database:")
    for table in all_tables:
        print(f"  - {table}")
    
    print("\nGame-related tables:")
    game_tables = [t for t in all_tables if 'game' in t.lower()]
    if game_tables:
        for table in game_tables:
            print(f"  ✓ {table}")
    else:
        print("  ✗ No game tables found!")
