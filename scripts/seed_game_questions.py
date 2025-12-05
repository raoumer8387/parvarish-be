"""Seed game questions for Mood Picker, Scenario Game, and Islamic Quiz.

Run with: python scripts/seed_game_questions.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.game_questions import MoodScenario, ScenarioQuestion, IslamicQuizQuestion


# ==================== MOOD SCENARIOS ====================
MOOD_SCENARIOS = [
    # Age 6-8
    {
        "age_group": "6-8",
        "scenario_text_en": "Your friend broke your favorite toy by mistake. How do you feel?",
        "scenario_text_ur": "Aapke dost ne ghalti se aapka pasandeeda khilona tor diya. Aap kaisa mehsoos karte hain?",
        "category": "emotional",
        "mood_weights": {"Anger": -5, "Forgive": +5, "Happy": 0, "Sad": +1},
        "tags": ["anger_control", "forgiveness", "empathy"]
    },
    {
        "age_group": "6-8",
        "scenario_text_en": "Someone took your turn in a game. What do you feel?",
        "scenario_text_ur": "Kisi ne game mein aapki baari le li. Aap kaisa mehsoos karte hain?",
        "category": "emotional",
        "mood_weights": {"Anger": -4, "Forgive": +4, "Happy": 0, "Sad": +2},
        "tags": ["patience", "fairness"]
    },
    {
        "age_group": "6-8",
        "scenario_text_en": "A classmate shared their lunch with you. How do you feel?",
        "scenario_text_ur": "Class ke dost ne apna lunch aapke saath share kiya. Aap kaisa mehsoos karte hain?",
        "category": "social",
        "mood_weights": {"Anger": 0, "Forgive": +2, "Happy": +5, "Sad": 0},
        "tags": ["gratitude", "kindness"]
    },
    # Age 9-11
    {
        "age_group": "9-11",
        "scenario_text_en": "Your team lost a match because of one player's mistake. How do you feel?",
        "scenario_text_ur": "Aapki team ek player ki ghalti ki wajah se haar gayi. Aap kaisa mehsoos karte hain?",
        "category": "emotional",
        "mood_weights": {"Anger": -5, "Forgive": +5, "Happy": 0, "Sad": +2},
        "tags": ["teamwork", "forgiveness", "anger_control"]
    },
    {
        "age_group": "9-11",
        "scenario_text_en": "Someone spread a rumor about you that wasn't true. How do you feel?",
        "scenario_text_ur": "Kisi ne aapke bare mein galat afwah phelai. Aap kaisa mehsoos karte hain?",
        "category": "emotional",
        "mood_weights": {"Anger": -4, "Forgive": +4, "Happy": 0, "Sad": +3},
        "tags": ["emotional_regulation", "patience"]
    },
    {
        "age_group": "9-11",
        "scenario_text_en": "You helped a younger child tie their shoes and they smiled at you. How do you feel?",
        "scenario_text_ur": "Aapne ek chhote bachhe ko joote baandhne mein madad ki aur woh muskuraya. Aap kaisa mehsoos karte hain?",
        "category": "moral",
        "mood_weights": {"Anger": 0, "Forgive": +2, "Happy": +5, "Sad": 0},
        "tags": ["kindness", "empathy", "service"]
    },
    # Age 12-14
    {
        "age_group": "12-14",
        "scenario_text_en": "Your best friend forgot your birthday. How do you feel?",
        "scenario_text_ur": "Aapke behtareen dost ne aapka janamdin bhula diya. Aap kaisa mehsoos karte hain?",
        "category": "emotional",
        "mood_weights": {"Anger": -3, "Forgive": +5, "Happy": 0, "Sad": +3},
        "tags": ["forgiveness", "emotional_maturity"]
    },
    {
        "age_group": "12-14",
        "scenario_text_en": "You studied hard but still got a lower grade than expected. How do you feel?",
        "scenario_text_ur": "Aapne mehnat se parhai ki lekin phir bhi umeed se kam grade mile. Aap kaisa mehsoos karte hain?",
        "category": "emotional",
        "mood_weights": {"Anger": -2, "Forgive": +3, "Happy": 0, "Sad": +2},
        "tags": ["resilience", "perseverance"]
    },
    {
        "age_group": "12-14",
        "scenario_text_en": "You saw someone being bullied and you stood up for them. How do you feel?",
        "scenario_text_ur": "Aapne kisi ko tang hote dekha aur aap unki madad ke liye khade hue. Aap kaisa mehsoos karte hain?",
        "category": "moral",
        "mood_weights": {"Anger": 0, "Forgive": +3, "Happy": +5, "Sad": 0},
        "tags": ["courage", "justice", "empathy"]
    },
]


# ==================== SCENARIO QUESTIONS ====================
SCENARIO_QUESTIONS = [
    # Age 6-8
    {
        "age_group": "6-8",
        "question_text_en": "Your friend pushed you in the playground. What will you do?",
        "question_text_ur": "Aapke dost ne aapko playground mein dhakka diya. Aap kya karenge?",
        "category": "moral",
        "options": [
            {"option": "Push them back", "moral": -8, "emotional": -5, "social": -3},
            {"option": "Tell a teacher", "moral": +6, "emotional": +3, "social": +4},
            {"option": "Forgive and move on", "moral": +10, "emotional": +5, "social": +5}
        ],
        "tags": ["forgiveness", "conflict_resolution"]
    },
    {
        "age_group": "6-8",
        "question_text_en": "You found a toy that doesn't belong to you. What will you do?",
        "question_text_ur": "Aapko aisa khilona mila jo aapka nahi hai. Aap kya karenge?",
        "category": "moral",
        "options": [
            {"option": "Keep it", "moral": -10, "emotional": 0, "social": -5},
            {"option": "Return it to the owner", "moral": +10, "emotional": +3, "social": +5},
            {"option": "Give it to someone else", "moral": -5, "emotional": 0, "social": +2}
        ],
        "tags": ["honesty", "integrity"]
    },
    {
        "age_group": "6-8",
        "question_text_en": "Your little sibling is crying because they lost a game. What will you do?",
        "question_text_ur": "Aapka chhota bhai/behan game harne ki wajah se ro raha hai. Aap kya karenge?",
        "category": "emotional",
        "options": [
            {"option": "Laugh at them", "moral": -8, "emotional": -10, "social": -5},
            {"option": "Comfort and encourage them", "moral": +8, "emotional": +10, "social": +7},
            {"option": "Ignore them", "moral": -3, "emotional": -5, "social": -2}
        ],
        "tags": ["empathy", "kindness", "family_values"]
    },
    # Age 9-11
    {
        "age_group": "9-11",
        "question_text_en": "You see a classmate being left out during recess. What will you do?",
        "question_text_ur": "Aap dekh rahe hain ke ek classmate ko recess mein chhora ja raha hai. Aap kya karenge?",
        "category": "social",
        "options": [
            {"option": "Ignore it", "moral": -5, "emotional": -3, "social": -8},
            {"option": "Invite them to join you", "moral": +10, "emotional": +7, "social": +10},
            {"option": "Ask others why they're excluding them", "moral": +5, "emotional": +3, "social": +5}
        ],
        "tags": ["inclusion", "kindness", "leadership"]
    },
    {
        "age_group": "9-11",
        "question_text_en": "Your parent asked you to help with chores but your favorite show is on. What will you do?",
        "question_text_ur": "Aapke walidain ne kaam mein madad maangi lekin aapka pasandeeda show chal raha hai. Aap kya karenge?",
        "category": "moral",
        "options": [
            {"option": "Ignore and watch TV", "moral": -8, "emotional": -3, "social": -5},
            {"option": "Help immediately", "moral": +10, "emotional": +5, "social": +7},
            {"option": "Ask to help after the show", "moral": +5, "emotional": +2, "social": +4}
        ],
        "tags": ["obedience", "family_responsibility"]
    },
    {
        "age_group": "9-11",
        "question_text_en": "You accidentally broke something at a friend's house. What will you do?",
        "question_text_ur": "Aapne ghalti se apne dost ke ghar kuch tor diya. Aap kya karenge?",
        "category": "moral",
        "options": [
            {"option": "Hide it and say nothing", "moral": -10, "emotional": -5, "social": -8},
            {"option": "Tell the truth and apologize", "moral": +10, "emotional": +7, "social": +8},
            {"option": "Blame someone else", "moral": -12, "emotional": -7, "social": -10}
        ],
        "tags": ["honesty", "accountability", "courage"]
    },
    # Age 12-14
    {
        "age_group": "12-14",
        "question_text_en": "Your friends are planning to cheat on a test and want you to join. What will you do?",
        "question_text_ur": "Aapke dost test mein cheating karne ka plan bana rahe hain aur chahte hain aap bhi shaamil hon. Aap kya karenge?",
        "category": "moral",
        "options": [
            {"option": "Join them", "moral": -15, "emotional": -5, "social": -8},
            {"option": "Refuse and study honestly", "moral": +15, "emotional": +8, "social": +5},
            {"option": "Report to the teacher", "moral": +10, "emotional": +3, "social": -3}
        ],
        "tags": ["integrity", "peer_pressure", "honesty"]
    },
    {
        "age_group": "12-14",
        "question_text_en": "You overhear someone spreading lies about your friend. What will you do?",
        "question_text_ur": "Aapne suna ke koi aapke dost ke bare mein jhoot phaila raha hai. Aap kya karenge?",
        "category": "social",
        "options": [
            {"option": "Join in the gossip", "moral": -10, "emotional": -5, "social": -10},
            {"option": "Defend your friend", "moral": +12, "emotional": +8, "social": +10},
            {"option": "Stay silent", "moral": -3, "emotional": 0, "social": -5}
        ],
        "tags": ["loyalty", "courage", "justice"]
    },
    {
        "age_group": "12-14",
        "question_text_en": "You're angry at your parents for a strict rule. What will you do?",
        "question_text_ur": "Aap apne walidain se naraz hain kyunki unhone sakht qaanoon banaya hai. Aap kya karenge?",
        "category": "emotional",
        "options": [
            {"option": "Yell and argue loudly", "moral": -10, "emotional": -12, "social": -8},
            {"option": "Talk calmly about your feelings", "moral": +10, "emotional": +12, "social": +10},
            {"option": "Obey silently but stay upset", "moral": +5, "emotional": -3, "social": +2}
        ],
        "tags": ["communication", "respect", "emotional_maturity"]
    },
]


# ==================== ISLAMIC QUIZ QUESTIONS ====================
ISLAMIC_QUIZ_QUESTIONS = [
    # Age 6-8
    {
        "age_group": "6-8",
        "question_text_en": "How many times do Muslims pray in a day?",
        "question_text_ur": "Musalman din mein kitni baar namaz parhte hain?",
        "category": "spiritual",
        "options": ["3 times", "5 times", "7 times", "10 times"],
        "correct_answer": "5 times",
        "explanation_en": "Muslims pray 5 times a day: Fajr, Dhuhr, Asr, Maghrib, and Isha.",
        "explanation_ur": "Musalman din mein 5 baar namaz parhte hain: Fajr, Dhuhr, Asr, Maghrib, aur Isha.",
        "difficulty": 1,
        "tags": ["salah", "basics"]
    },
    {
        "age_group": "6-8",
        "question_text_en": "What do we say before starting something?",
        "question_text_ur": "Koi kaam shuru karne se pehle hum kya kehte hain?",
        "category": "spiritual",
        "options": ["Alhamdulillah", "Bismillah", "SubhanAllah", "Allahu Akbar"],
        "correct_answer": "Bismillah",
        "explanation_en": "We say 'Bismillah' (In the name of Allah) before starting anything.",
        "explanation_ur": "Hum kisi bhi kaam ko shuru karne se pehle 'Bismillah' kehte hain.",
        "difficulty": 1,
        "tags": ["dua", "manners"]
    },
    {
        "age_group": "6-8",
        "question_text_en": "Who is the last Prophet of Islam?",
        "question_text_ur": "Islam ke aakhri Nabi kaun hain?",
        "category": "cognitive",
        "options": ["Prophet Ibrahim", "Prophet Musa", "Prophet Muhammad (PBUH)", "Prophet Isa"],
        "correct_answer": "Prophet Muhammad (PBUH)",
        "explanation_en": "Prophet Muhammad (Peace Be Upon Him) is the last messenger of Allah.",
        "explanation_ur": "Hazrat Muhammad (Sallallahu Alaihi Wasallam) Allah ke aakhri Rasool hain.",
        "difficulty": 1,
        "tags": ["prophets", "knowledge"]
    },
    # Age 9-11
    {
        "age_group": "9-11",
        "question_text_en": "What is the first pillar of Islam?",
        "question_text_ur": "Islam ka pehla rukn kya hai?",
        "category": "spiritual",
        "options": ["Salah", "Zakat", "Shahada", "Hajj"],
        "correct_answer": "Shahada",
        "explanation_en": "Shahada (declaration of faith) is the first pillar of Islam.",
        "explanation_ur": "Shahada (iman ki gawahi) Islam ka pehla rukn hai.",
        "difficulty": 1,
        "tags": ["pillars", "faith"]
    },
    {
        "age_group": "9-11",
        "question_text_en": "In which month do Muslims fast?",
        "question_text_ur": "Musalman kis mahine mein roza rakhte hain?",
        "category": "spiritual",
        "options": ["Shawwal", "Ramadan", "Muharram", "Rajab"],
        "correct_answer": "Ramadan",
        "explanation_en": "Muslims fast during the month of Ramadan.",
        "explanation_ur": "Musalman Ramadan ke mahine mein roza rakhte hain.",
        "difficulty": 1,
        "tags": ["fasting", "ramadan"]
    },
    {
        "age_group": "9-11",
        "question_text_en": "What does 'Alhamdulillah' mean?",
        "question_text_ur": "'Alhamdulillah' ka matlab kya hai?",
        "category": "cognitive",
        "options": ["All praise to Allah", "In the name of Allah", "Allah is Great", "Glory to Allah"],
        "correct_answer": "All praise to Allah",
        "explanation_en": "'Alhamdulillah' means 'All praise and thanks belong to Allah'.",
        "explanation_ur": "'Alhamdulillah' ka matlab hai 'Tamam tareef Allah ke liye hai'.",
        "difficulty": 2,
        "tags": ["arabic", "gratitude"]
    },
    {
        "age_group": "9-11",
        "question_text_en": "Which companion of the Prophet was known as 'The Truthful'?",
        "question_text_ur": "Nabi ke kaun se sahabi ko 'Siddiq' kaha jata tha?",
        "category": "cognitive",
        "options": ["Umar ibn al-Khattab", "Abu Bakr", "Ali ibn Abi Talib", "Uthman ibn Affan"],
        "correct_answer": "Abu Bakr",
        "explanation_en": "Abu Bakr was called 'As-Siddiq' (The Truthful) for his unwavering faith.",
        "explanation_ur": "Hazrat Abu Bakr ko 'Siddiq' kaha jata tha unki pakki imaan ki wajah se.",
        "difficulty": 2,
        "tags": ["companions", "history"]
    },
    # Age 12-14
    {
        "age_group": "12-14",
        "question_text_en": "What is the meaning of 'Taqwa'?",
        "question_text_ur": "'Taqwa' ka matlab kya hai?",
        "category": "spiritual",
        "options": ["Faith", "God-consciousness/Piety", "Charity", "Prayer"],
        "correct_answer": "God-consciousness/Piety",
        "explanation_en": "Taqwa means being conscious of Allah and avoiding His displeasure.",
        "explanation_ur": "Taqwa ka matlab hai Allah ka khauf rakhna aur unki narazgi se bachna.",
        "difficulty": 2,
        "tags": ["spirituality", "character"]
    },
    {
        "age_group": "12-14",
        "question_text_en": "Which Surah is called the 'Heart of the Quran'?",
        "question_text_ur": "Kis Surah ko 'Quran ka dil' kaha jata hai?",
        "category": "cognitive",
        "options": ["Surah Al-Fatiha", "Surah Yaseen", "Surah Al-Baqarah", "Surah Ar-Rahman"],
        "correct_answer": "Surah Yaseen",
        "explanation_en": "Surah Yaseen is often called the heart of the Quran.",
        "explanation_ur": "Surah Yaseen ko aksar Quran ka dil kaha jata hai.",
        "difficulty": 2,
        "tags": ["quran", "knowledge"]
    },
    {
        "age_group": "12-14",
        "question_text_en": "What does 'Sadaqah' mean?",
        "question_text_ur": "'Sadaqah' ka matlab kya hai?",
        "category": "spiritual",
        "options": ["Fasting", "Voluntary charity", "Prayer", "Pilgrimage"],
        "correct_answer": "Voluntary charity",
        "explanation_en": "Sadaqah is voluntary charity given for the sake of Allah.",
        "explanation_ur": "Sadaqah wo khairaat hai jo Allah ki raza ke liye di jaye.",
        "difficulty": 2,
        "tags": ["charity", "generosity"]
    },
    {
        "age_group": "12-14",
        "question_text_en": "Which night is better than a thousand months?",
        "question_text_ur": "Kaun si raat hazaar maheenon se behtar hai?",
        "category": "spiritual",
        "options": ["Laylat al-Qadr", "Laylat al-Miraj", "First night of Ramadan", "Night of Eid"],
        "correct_answer": "Laylat al-Qadr",
        "explanation_en": "Laylat al-Qadr (The Night of Power) is better than a thousand months.",
        "explanation_ur": "Laylat al-Qadr (Shab-e-Qadr) hazaar maheenon se behtar hai.",
        "difficulty": 2,
        "tags": ["ramadan", "special_nights"]
    },
]


def seed_game_questions():
    """Seed all game questions into the database."""
    db: Session = next(get_db())
    
    try:
        # Clear existing data
        db.query(MoodScenario).delete()
        db.query(ScenarioQuestion).delete()
        db.query(IslamicQuizQuestion).delete()
        
        # Seed Mood Scenarios
        for item in MOOD_SCENARIOS:
            scenario = MoodScenario(**item)
            db.add(scenario)
        
        # Seed Scenario Questions
        for item in SCENARIO_QUESTIONS:
            question = ScenarioQuestion(**item)
            db.add(question)
        
        # Seed Islamic Quiz Questions
        for item in ISLAMIC_QUIZ_QUESTIONS:
            quiz = IslamicQuizQuestion(**item)
            db.add(quiz)
        
        db.commit()
        print(f"✅ Seeded {len(MOOD_SCENARIOS)} mood scenarios")
        print(f"✅ Seeded {len(SCENARIO_QUESTIONS)} scenario questions")
        print(f"✅ Seeded {len(ISLAMIC_QUIZ_QUESTIONS)} Islamic quiz questions")
        print("Game questions seeding completed successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding game questions: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_game_questions()
