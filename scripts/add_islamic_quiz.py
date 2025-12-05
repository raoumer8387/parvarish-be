"""Script to add Islamic quiz questions to the database."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models.game_questions import IslamicQuizQuestion


def add_islamic_quiz_questions():
    """Add Islamic quiz questions for all age groups."""
    db = SessionLocal()
    
    try:
        questions = [
            # Age 6-8: Daily prayers
            IslamicQuizQuestion(
                age_group="6-8",
                question_text_en="How many daily prayers (Salah)?",
                question_text_ur="روزانہ کتنی نمازیں ہوتی ہیں؟",
                question_text_roman="Rozana kitni namazein hoti hain?",
                category="spiritual",
                options=["3", "4", "5", "6"],
                correct_answer="5",
                explanation_en="Muslims pray 5 times daily.",
                explanation_ur="مسلمان دن میں پانچ بار نماز پڑھتے ہیں۔",
                explanation_roman="Muslim din mein 5 martaba namaz parhte hain.",
                difficulty=1,
                tags=["salah"]
            ),
            
            # Age 6-8: Holy book
            IslamicQuizQuestion(
                age_group="6-8",
                question_text_en="What is the holy book of Muslims?",
                question_text_ur="مسلمانوں کی مقدس کتاب کون سی ہے؟",
                question_text_roman="Muslmano ki muqaddas kitaab kaunsi hai?",
                category="spiritual",
                options=["Quran", "Bible", "Torah"],
                correct_answer="Quran",
                explanation_en="The Quran is the holy book revealed to Prophet Muhammad (PBUH).",
                explanation_ur="قرآن وہ مقدس کتاب ہے جو نبی محمد ﷺ پر نازل ہوئی۔",
                explanation_roman="Quran woh muqaddas kitaab hai jo Nabi Muhammad ﷺ par nazil hui.",
                difficulty=1,
                tags=["quran"]
            ),
            
            # Age 9-11: First Prophet
            IslamicQuizQuestion(
                age_group="9-11",
                question_text_en="Who was the first Prophet?",
                question_text_ur="پہلے نبی کون تھے؟",
                question_text_roman="Pehle Nabi kaun thay?",
                category="cognitive",
                options=["Adam (AS)", "Muhammad ﷺ", "Ibrahim (AS)"],
                correct_answer="Adam (AS)",
                explanation_en="Prophet Adam (AS) was the first human and first Prophet.",
                explanation_ur="حضرت آدم علیہ السلام پہلے انسان اور پہلے نبی تھے۔",
                explanation_roman="Hazrat Adam (AS) pehle insaan aur pehle Nabi thay.",
                difficulty=2,
                tags=["prophets"]
            ),
            
            # Age 9-11: Fasting month
            IslamicQuizQuestion(
                age_group="9-11",
                question_text_en="Which month do Muslims fast?",
                question_text_ur="مسلمان کس مہینے میں روزہ رکھتے ہیں؟",
                question_text_roman="Muslim kis mahine roze rakhte hain?",
                category="spiritual",
                options=["Rajab", "Ramadan", "Shaban"],
                correct_answer="Ramadan",
                explanation_en="Ramadan is the holy month of fasting, the 9th month of Islamic calendar.",
                explanation_ur="رمضان روزے کا مقدس مہینہ ہے، اسلامی کیلنڈر کا نواں مہینہ۔",
                explanation_roman="Ramadan roze ka muqaddas mahina hai, Islamic calendar ka 9wa mahina.",
                difficulty=1,
                tags=["ramadan"]
            ),
            
            # Age 12-14: Prophet's birthplace
            IslamicQuizQuestion(
                age_group="12-14",
                question_text_en="Where was Prophet Muhammad (PBUH) born?",
                question_text_ur="نبی ﷺ کہاں پیدا ہوئے؟",
                question_text_roman="Nabi ﷺ kahan paida huay?",
                category="cognitive",
                options=["Makkah", "Madinah", "Taif"],
                correct_answer="Makkah",
                explanation_en="Prophet Muhammad (PBUH) was born in Makkah in 570 CE.",
                explanation_ur="نبی محمد ﷺ 570 عیسوی میں مکہ میں پیدا ہوئے۔",
                explanation_roman="Nabi Muhammad ﷺ 570 CE mein Makkah mein paida huay.",
                difficulty=2,
                tags=["seerah"]
            ),
            
            # Age 12-14: Zakat
            IslamicQuizQuestion(
                age_group="12-14",
                question_text_en="What is Zakat?",
                question_text_ur="زکوٰۃ کیا ہے؟",
                question_text_roman="Zakat kya hai?",
                category="spiritual",
                options=["Charity", "Prayer", "Fasting"],
                correct_answer="Charity",
                explanation_en="Zakat is obligatory charity, one of the Five Pillars of Islam.",
                explanation_ur="زکوٰۃ فرض خیرات ہے، اسلام کے پانچ ارکان میں سے ایک۔",
                explanation_roman="Zakat farz khairat hai, Islam ke paanch arkan mein se aik.",
                difficulty=2,
                tags=["zakat"]
            ),
        ]
        
        # Add all questions
        db.bulk_save_objects(questions)
        db.commit()
        
        print(f"✅ Successfully added {len(questions)} Islamic quiz questions!")
        print("\nBreakdown:")
        print("  - Age 6-8: 2 questions")
        print("  - Age 9-11: 2 questions")
        print("  - Age 12-14: 2 questions")
        print("\nCategories:")
        print("  - Spiritual: 4 questions")
        print("  - Cognitive: 2 questions")
        print("\nDifficulty:")
        print("  - Easy (1): 3 questions")
        print("  - Medium (2): 3 questions")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error adding questions: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🕌 Adding Islamic Quiz Questions to Database...\n")
    add_islamic_quiz_questions()
    print("\n🎉 Done!")
