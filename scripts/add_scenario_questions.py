"""Script to add scenario questions (What Would You Do?) to the database."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models.game_questions import ScenarioQuestion


def add_scenario_questions():
    """Add scenario questions for all age groups."""
    db = SessionLocal()
    
    try:
        questions = [
            # Age 6-8: Found money
            ScenarioQuestion(
                age_group="6-8",
                question_text_en="You found money on the ground. What will you do?",
                question_text_ur="آپ کو زمین پر پیسے ملے۔ آپ کیا کریں گے؟",
                question_text_roman="Aap ko zameen par paisay mile. Aap kya karein ge?",
                category="moral",
                options=[
                    {"option": "Give to teacher/parent", "moral": 10, "emotional": 5, "social": 5},
                    {"option": "Keep it", "moral": -10, "emotional": -2, "social": -3},
                    {"option": "Ask whose it is", "moral": 8, "emotional": 3, "social": 7}
                ],
                tags=["honesty"]
            ),
            
            # Age 6-8: Friend crying
            ScenarioQuestion(
                age_group="6-8",
                question_text_en="Your friend is crying. What will you do?",
                question_text_ur="آپ کا دوست رو رہا ہے۔ آپ کیا کریں گے؟",
                question_text_roman="Aap ka dost ro raha hai. Aap kya karein ge?",
                category="emotional",
                options=[
                    {"option": "Comfort him", "moral": 8, "emotional": 10, "social": 8},
                    {"option": "Ignore", "moral": -6, "emotional": -5, "social": -8}
                ],
                tags=["empathy"]
            ),
            
            # Age 9-11: Lie to teacher
            ScenarioQuestion(
                age_group="9-11",
                question_text_en="Your friend wants you to lie to teacher.",
                question_text_ur="آپ کا دوست چاہتا ہے کہ آپ استاد سے جھوٹ بولیں۔",
                question_text_roman="Aap ka dost chahta hai ke aap ustad se jhoot bolein.",
                category="moral",
                options=[
                    {"option": "Refuse and tell truth", "moral": 10, "emotional": 6, "social": 8},
                    {"option": "Lie for friend", "moral": -10, "emotional": -4, "social": -5}
                ],
                tags=["integrity"]
            ),
            
            # Age 9-11: Someone bullied
            ScenarioQuestion(
                age_group="9-11",
                question_text_en="Someone is bullied in school.",
                question_text_ur="اسکول میں کسی کو تنگ کیا جا رہا ہے۔",
                question_text_roman="School mein kisi ko tang kiya ja raha hai.",
                category="social",
                options=[
                    {"option": "Help the victim", "moral": 10, "emotional": 8, "social": 10},
                    {"option": "Stay silent", "moral": -5, "emotional": -4, "social": -6}
                ],
                tags=["courage"]
            ),
            
            # Age 12-14: Bad content
            ScenarioQuestion(
                age_group="12-14",
                question_text_en="You see a friend watching bad content.",
                question_text_ur="آپ اپنے دوست کو بُرا مواد دیکھتے ہوئے دیکھتے ہیں۔",
                question_text_roman="Aap apne dost ko bura content dekhte hue dekhtay hain.",
                category="moral",
                options=[
                    {"option": "Stop and advise him", "moral": 10, "emotional": 6, "social": 8},
                    {"option": "Join him", "moral": -10, "emotional": -5, "social": -8}
                ],
                tags=["self_control"]
            ),
            
            # Age 12-14: Skip prayer
            ScenarioQuestion(
                age_group="12-14",
                question_text_en="Your group is planning to skip prayer.",
                question_text_ur="آپ کا گروپ نماز چھوڑنے کی منصوبہ بندی کر رہا ہے۔",
                question_text_roman="Aap ka group namaz chorne ka plan kar raha hai.",
                category="spiritual",
                options=[
                    {"option": "Pray alone", "moral": 10, "emotional": 5, "social": 4},
                    {"option": "Skip with them", "moral": -10, "emotional": -5, "social": -5}
                ],
                tags=["salah"]
            ),
        ]
        
        # Add all questions
        db.bulk_save_objects(questions)
        db.commit()
        
        print(f"✅ Successfully added {len(questions)} scenario questions!")
        print("\nBreakdown:")
        print("  - Age 6-8: 2 questions")
        print("  - Age 9-11: 2 questions")
        print("  - Age 12-14: 2 questions")
        print("\nCategories:")
        print("  - Moral: 3 questions")
        print("  - Emotional: 1 question")
        print("  - Social: 1 question")
        print("  - Spiritual: 1 question")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error adding questions: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🎮 Adding Scenario Questions (What Would You Do?) to Database...\n")
    add_scenario_questions()
    print("\n🎉 Done!")
