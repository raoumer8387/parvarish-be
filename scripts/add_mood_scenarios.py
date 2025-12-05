"""Script to add mood scenarios to the database."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models.game_questions import MoodScenario


def add_mood_scenarios():
    """Add mood scenarios for all age groups."""
    db = SessionLocal()
    
    try:
        scenarios = [
            # Age 6-8: Broken toy
            MoodScenario(
                age_group="6-8",
                scenario_text_en="Your friend broke your favorite toy. How do you feel?",
                scenario_text_ur="آپ کے دوست نے آپ کا پسندیدہ کھلونا توڑ دیا۔ آپ کو کیسا لگتا ہے؟",
                category="emotional",
                mood_weights={
                    "Anger": -5,
                    "Forgive": 10,
                    "Cry": -2,
                    "Calm": 5,
                    "Ignore": 2
                },
                tags=["anger_control", "forgiveness"]
            ),
            
            # Age 9-11: Teacher scolded
            MoodScenario(
                age_group="9-11",
                scenario_text_en="Your teacher scolded you in front of the class. How do you feel?",
                scenario_text_ur="آپ کے استاد نے سب کے سامنے آپ کو ڈانٹا ہے۔ آپ کو کیسا لگتا ہے؟",
                category="emotional",
                mood_weights={
                    "Sad": -2,
                    "Anger": -5,
                    "Calm": 5,
                    "Forgive": 7,
                    "Think": 6
                },
                tags=["emotional_control", "patience"]
            ),
            
            # Age 6-8: Sibling took pencil
            MoodScenario(
                age_group="6-8",
                scenario_text_en="Your sibling took your pencil without asking. How do you feel?",
                scenario_text_ur="آپ کے بہن بھائی نے بغیر پوچھے آپ کی پنسل لے لی۔ آپ کو کیسا لگتا ہے؟",
                category="social",
                mood_weights={
                    "Anger": -5,
                    "Talk": 8,
                    "Cry": -2,
                    "Forgive": 10,
                    "Ignore": 3
                },
                tags=["sharing", "sibling_behavior"]
            ),
            
            # Age 9-11: Helped but no thanks
            MoodScenario(
                age_group="9-11",
                scenario_text_en="You helped someone and nobody thanked you. How do you feel?",
                scenario_text_ur="آپ نے کسی کی مدد کی لیکن کسی نے شکریہ ادا نہیں کیا۔ آپ کو کیسا لگا؟",
                category="moral",
                mood_weights={
                    "Happy": 8,
                    "Sad": -2,
                    "Anger": -5,
                    "Proud": 10,
                    "Calm": 5
                },
                tags=["selflessness", "patience"]
            ),
            
            # Age 12-14: Someone laughed
            MoodScenario(
                age_group="12-14",
                scenario_text_en="Someone laughed at you in front of others. How do you feel?",
                scenario_text_ur="کسی نے سب کے سامنے آپ کا مذاق اڑایا۔ آپ کو کیسا لگا؟",
                category="emotional",
                mood_weights={
                    "Anger": -8,
                    "Sad": -5,
                    "Stay Quiet": 6,
                    "Forgive": 10,
                    "Walk Away": 8
                },
                tags=["self_control", "confidence"]
            ),
        ]
        
        # Add all scenarios
        db.bulk_save_objects(scenarios)
        db.commit()
        
        print(f"✅ Successfully added {len(scenarios)} mood scenarios!")
        print("\nBreakdown:")
        print("  - Age 6-8: 2 scenarios")
        print("  - Age 9-11: 2 scenarios")
        print("  - Age 12-14: 1 scenario")
        print("\nCategories:")
        print("  - Emotional: 3 scenarios")
        print("  - Social: 1 scenario")
        print("  - Moral: 1 scenario")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error adding scenarios: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🎮 Adding Mood Scenarios to Database...\n")
    add_mood_scenarios()
    print("\n🎉 Done!")
