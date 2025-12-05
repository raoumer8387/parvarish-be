"""
Migration: Add Roman Urdu text fields to game questions

This migration adds Roman Urdu (transliterated Urdu) text fields to all game question tables
to make content more accessible for users who can't read Urdu script.

Tables affected:
- mood_scenarios: Add scenario_text_roman
- scenario_questions: Add question_text_roman
- islamic_quiz_questions: Add question_text_roman and explanation_roman
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.db.session import engine
from sqlalchemy import text


def upgrade():
    """Add Roman Urdu fields to game question tables."""
    with engine.connect() as conn:
        print("🔄 Adding Roman Urdu fields to game question tables...")
        
        # Add scenario_text_roman to mood_scenarios
        print("\n1️⃣ Adding scenario_text_roman to mood_scenarios...")
        conn.execute(text("""
            ALTER TABLE mood_scenarios 
            ADD COLUMN IF NOT EXISTS scenario_text_roman TEXT;
        """))
        conn.commit()
        print("   ✅ Done")
        
        # Add question_text_roman to scenario_questions
        print("\n2️⃣ Adding question_text_roman to scenario_questions...")
        conn.execute(text("""
            ALTER TABLE scenario_questions 
            ADD COLUMN IF NOT EXISTS question_text_roman TEXT;
        """))
        conn.commit()
        print("   ✅ Done")
        
        # Add question_text_roman to islamic_quiz_questions
        print("\n3️⃣ Adding question_text_roman to islamic_quiz_questions...")
        conn.execute(text("""
            ALTER TABLE islamic_quiz_questions 
            ADD COLUMN IF NOT EXISTS question_text_roman TEXT;
        """))
        conn.commit()
        print("   ✅ Done")
        
        # Add explanation_roman to islamic_quiz_questions
        print("\n4️⃣ Adding explanation_roman to islamic_quiz_questions...")
        conn.execute(text("""
            ALTER TABLE islamic_quiz_questions 
            ADD COLUMN IF NOT EXISTS explanation_roman TEXT;
        """))
        conn.commit()
        print("   ✅ Done")
        
        print("\n✨ Migration completed successfully!")
        print("\nSummary:")
        print("  - mood_scenarios: +1 column (scenario_text_roman)")
        print("  - scenario_questions: +1 column (question_text_roman)")
        print("  - islamic_quiz_questions: +2 columns (question_text_roman, explanation_roman)")


def downgrade():
    """Remove Roman Urdu fields from game question tables."""
    with engine.connect() as conn:
        print("🔄 Removing Roman Urdu fields from game question tables...")
        
        print("\n1️⃣ Removing scenario_text_roman from mood_scenarios...")
        conn.execute(text("""
            ALTER TABLE mood_scenarios 
            DROP COLUMN IF EXISTS scenario_text_roman;
        """))
        conn.commit()
        print("   ✅ Done")
        
        print("\n2️⃣ Removing question_text_roman from scenario_questions...")
        conn.execute(text("""
            ALTER TABLE scenario_questions 
            DROP COLUMN IF EXISTS question_text_roman;
        """))
        conn.commit()
        print("   ✅ Done")
        
        print("\n3️⃣ Removing question_text_roman from islamic_quiz_questions...")
        conn.execute(text("""
            ALTER TABLE islamic_quiz_questions 
            DROP COLUMN IF EXISTS question_text_roman;
        """))
        conn.commit()
        print("   ✅ Done")
        
        print("\n4️⃣ Removing explanation_roman from islamic_quiz_questions...")
        conn.execute(text("""
            ALTER TABLE islamic_quiz_questions 
            DROP COLUMN IF EXISTS explanation_roman;
        """))
        conn.commit()
        print("   ✅ Done")
        
        print("\n✨ Downgrade completed successfully!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
