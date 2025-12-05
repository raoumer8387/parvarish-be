# 🎮 Game Questions Format Guide

This document explains **exactly** how to format questions for each game type in the Parvarish AI backend database.

---

## 📋 Table of Contents

1. [Mood Picker Game](#1-mood-picker-game)
2. [Scenario Game (What Would You Do?)](#2-scenario-game-what-would-you-do)
3. [Islamic Quiz](#3-islamic-quiz)
4. [Memory Card Game](#4-memory-card-game)
5. [How to Add Questions](#how-to-add-questions)

---

## 1️⃣ MOOD PICKER GAME

**Table:** `mood_scenarios`

### Fields Required

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `age_group` | String | Target age range | `"6-8"`, `"9-11"`, `"12-14"` |
| `scenario_text_en` | Text | Scenario in English | `"Your friend broke your toy..."` |
| `scenario_text_ur` | Text | Scenario in Urdu (optional) | `"آپ کے دوست نے..."` |
| `scenario_text_roman` | Text | Scenario in Roman Urdu (optional) | `"Aap ke dost ne..."` |
| `category` | String | Behavior category | `"emotional"`, `"social"`, `"moral"` |
| `mood_weights` | JSONB | Mood options with scores | `{"Anger": -5, "Forgive": 10, ...}` |
| `tags` | JSONB Array | Optional tags | `["anger_control", "empathy"]` |

### Example JSON Format

```json
{
  "age_group": "6-8",
  "scenario_text_en": "Your friend broke your favorite toy. What do you feel?",
  "scenario_text_ur": "آپ کے دوست نے آپ کا پسندیدہ کھلونا توڑ دیا۔ آپ کو کیسا لگتا ہے؟",
  "scenario_text_roman": "Aap ke dost ne aap ka pasandeeda khilona tor diya. Aap kaise mehsoos karte ho?",
  "category": "emotional",
  "mood_weights": {
    "Anger": -5,
    "Forgive": 10,
    "Happy": 3,
    "Sad": 0,
    "Calm": 5
  },
  "tags": ["anger_control", "forgiveness", "empathy"]
}
```

### How Scoring Works

- **Positive scores** (5-10): Good emotional responses
- **Zero scores** (0): Neutral responses
- **Negative scores** (-5 to -10): Poor emotional choices
- Backend picks the **highest scoring mood** from child's selection

### More Examples

```json
[
  {
    "age_group": "9-11",
    "scenario_text_en": "Your sibling ate your snack without asking. What do you feel?",
    "scenario_text_ur": "آپ کے بہن بھائی نے پوچھے بغیر آپ کا ناشتہ کھا لیا۔ آپ کو کیسا لگتا ہے؟",
    "category": "social",
    "mood_weights": {
      "Anger": -5,
      "Talk": 10,
      "Ignore": 3,
      "Sad": 0,
      "Forgive": 8
    },
    "tags": ["sharing", "communication", "sibling_relations"]
  },
  {
    "age_group": "6-8",
    "scenario_text_en": "A classmate said mean words to you. What do you feel?",
    "scenario_text_ur": "ایک ہم جماعت نے آپ کو برے الفاظ کہے۔ آپ کو کیسا لگتا ہے؟",
    "category": "emotional",
    "mood_weights": {
      "Cry": -2,
      "Tell Teacher": 8,
      "Fight": -10,
      "Forgive": 10,
      "Sad": 0
    },
    "tags": ["bullying", "emotional_control", "conflict_resolution"]
  }
]
```

---

## 2️⃣ SCENARIO GAME (What Would You Do?)

**Table:** `scenario_questions`

### Fields Required

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `age_group` | String | Target age range | `"6-8"`, `"9-11"`, `"12-14"` |
| `question_text_en` | Text | Question in English | `"Your friend is being bullied..."` |
| `question_text_ur` | Text | Question in Urdu (optional) | `"آپ کے دوست کو..."` |
| `question_text_roman` | Text | Question in Roman Urdu (optional) | `"Aap ke dost ko..."` |
| `category` | String | Primary category | `"moral"`, `"emotional"`, `"social"` |
| `options` | JSONB Array | Choice options with behavior scores | See below |
| `tags` | JSONB Array | Optional tags | `["bullying", "courage"]` |

### Options Format

Each option has:
- `"option"`: The choice text
- `"moral"`: Impact on moral score (-10 to +10)
- `"emotional"`: Impact on emotional score (-10 to +10)
- `"social"`: Impact on social score (-10 to +10)

### Example JSON Format

```json
{
  "age_group": "9-11",
  "question_text_en": "Your friend is being bullied. What would you do?",
  "question_text_ur": "آپ کے دوست کو تنگ کیا جا رہا ہے۔ آپ کیا کریں گے؟",
  "question_text_roman": "Aap ke dost ko tang kiya ja raha hai. Aap kya karenge?",
  "category": "moral",
  "options": [
    {
      "option": "Help them and stand up to the bully",
      "moral": 10,
      "emotional": 5,
      "social": 8
    },
    {
      "option": "Tell a teacher or adult",
      "moral": 8,
      "emotional": 3,
      "social": 6
    },
    {
      "option": "Walk away and ignore it",
      "moral": -5,
      "emotional": -3,
      "social": -8
    },
    {
      "option": "Join the bully to avoid being bullied",
      "moral": -10,
      "emotional": -5,
      "social": -10
    }
  ],
  "tags": ["bullying", "courage", "empathy", "moral_choice"]
}
```

### More Examples

```json
[
  {
    "age_group": "6-8",
    "question_text_en": "You found money on the ground. What would you do?",
    "question_text_ur": "آپ کو زمین پر پیسےملے۔ آپ کیا کریں گے؟",
    "category": "moral",
    "options": [
      {
        "option": "Give it to teacher or parent",
        "moral": 10,
        "emotional": 3,
        "social": 5
      },
      {
        "option": "Keep it",
        "moral": -8,
        "emotional": -2,
        "social": -3
      },
      {
        "option": "Ask around if someone lost it",
        "moral": 10,
        "emotional": 5,
        "social": 8
      }
    ],
    "tags": ["honesty", "integrity", "moral_dilemma"]
  },
  {
    "age_group": "12-14",
    "question_text_en": "Your group is excluding a classmate. What would you do?",
    "question_text_ur": "آپ کا گروپ ایک ہم جماعت کو نظر انداز کر رہا ہے۔ آپ کیا کریں گے؟",
    "category": "social",
    "options": [
      {
        "option": "Invite them to join",
        "moral": 10,
        "emotional": 8,
        "social": 10
      },
      {
        "option": "Stay quiet to fit in",
        "moral": -5,
        "emotional": -3,
        "social": -5
      },
      {
        "option": "Make a separate plan with them",
        "moral": 7,
        "emotional": 5,
        "social": 6
      },
      {
        "option": "Support the exclusion",
        "moral": -10,
        "emotional": -5,
        "social": -10
      }
    ],
    "tags": ["inclusion", "peer_pressure", "empathy", "social_dynamics"]
  }
]
```

---

## 3️⃣ ISLAMIC QUIZ

**Table:** `islamic_quiz_questions`

### Fields Required

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `age_group` | String | Target age range | `"6-8"`, `"9-11"`, `"12-14"` |
| `question_text_en` | Text | Question in English | `"How many daily prayers..."` |
| `question_text_ur` | Text | Question in Urdu (optional) | `"روزانہ کتنی نمازیں..."` |
| `question_text_roman` | Text | Question in Roman Urdu (optional) | `"Rozana kitni namazen..."` |
| `category` | String | Knowledge category | `"spiritual"`, `"cognitive"` |
| `options` | JSONB Array | Answer choices | `["3", "4", "5", "6"]` |
| `correct_answer` | String | The correct option | `"5"` |
| `explanation_en` | Text | Explanation in English (optional) | `"Muslims pray 5 times..."` |
| `explanation_ur` | Text | Explanation in Urdu (optional) | `"مسلمان دن میں 5 بار..."` |
| `explanation_roman` | Text | Explanation in Roman Urdu (optional) | `"Musalman din mein 5 baar..."` |
| `difficulty` | Integer | Difficulty level (1-3) | `1` (easy), `2` (medium), `3` (hard) |
| `tags` | JSONB Array | Optional tags | `["salah", "pillars"]` |

### Example JSON Format

```json
{
  "age_group": "6-8",
  "question_text_en": "How many daily prayers (Salah) do Muslims perform?",
  "question_text_ur": "مسلمان روزانہ کتنی نمازیں پڑھتے ہیں؟",
  "question_text_roman": "Musalman rozana kitni namazen parhte hain?",
  "category": "spiritual",
  "options": ["3", "4", "5", "6"],
  "correct_answer": "5",
  "explanation_en": "Muslims pray 5 times a day: Fajr, Dhuhr, Asr, Maghrib, and Isha.",
  "explanation_ur": "مسلمان دن میں 5 بار نماز پڑھتے ہیں: فجر، ظہر، عصر، مغرب، اور عشاء۔",
  "explanation_roman": "Musalman din mein 5 baar namaz parhte hain: Fajr, Zuhr, Asr, Maghrib, aur Isha.",
  "difficulty": 1,
  "tags": ["salah", "pillars", "worship"]
}
```

### More Examples

```json
[
  {
    "age_group": "9-11",
    "question_text_en": "Which Prophet built the Kaaba with his father?",
    "question_text_ur": "کس نبی نے اپنے والد کے ساتھ کعبہ تعمیر کیا؟",
    "category": "cognitive",
    "options": ["Prophet Musa", "Prophet Ibrahim", "Prophet Isa", "Prophet Muhammad"],
    "correct_answer": "Prophet Ibrahim",
    "explanation_en": "Prophet Ibrahim (AS) and his son Ismail (AS) built the Kaaba in Makkah.",
    "explanation_ur": "حضرت ابراہیم علیہ السلام اور ان کے بیٹے حضرت اسماعیل علیہ السلام نے مکہ میں کعبہ تعمیر کیا۔",
    "difficulty": 2,
    "tags": ["prophets", "kaaba", "history", "ibrahim"]
  },
  {
    "age_group": "12-14",
    "question_text_en": "What is the last revelation sent to mankind?",
    "question_text_ur": "انسانیت کو بھیجا جانے والا آخری وحی کیا ہے؟",
    "category": "spiritual",
    "options": ["Torah", "Gospel", "Quran", "Psalms"],
    "correct_answer": "Quran",
    "explanation_en": "The Quran is the final revelation from Allah, sent through Prophet Muhammad (PBUH).",
    "explanation_ur": "قرآن اللہ کی طرف سے آخری وحی ہے، جو نبی محمد صلی اللہ علیہ وسلم کے ذریعے بھیجی گئی۔",
    "difficulty": 1,
    "tags": ["quran", "revelation", "prophets", "muhammad"]
  },
  {
    "age_group": "9-11",
    "question_text_en": "During which month do Muslims fast from dawn to sunset?",
    "question_text_ur": "مسلمان کس مہینے میں صبح سے شام تک روزہ رکھتے ہیں؟",
    "category": "spiritual",
    "options": ["Rajab", "Shaban", "Ramadan", "Shawwal"],
    "correct_answer": "Ramadan",
    "explanation_en": "Muslims fast during the holy month of Ramadan, the 9th month of the Islamic calendar.",
    "explanation_ur": "مسلمان رمضان کے مقدس مہینے میں روزہ رکھتے ہیں، جو اسلامی کیلنڈر کا 9واں مہینہ ہے۔",
    "difficulty": 1,
    "tags": ["fasting", "ramadan", "pillars", "worship"]
  }
]
```

---

## 4️⃣ MEMORY CARD GAME

**Note:** This game doesn't use database questions!

The Memory Card game is **purely frontend-based**. It generates card pairs dynamically in the frontend with images/icons.

**What the backend needs:**
- Just the final score submission (flips, matches, time)

**Submission format:**
```json
POST /api/v1/games/session/memory/complete
{
  "child_id": 15,
  "total_flips": 24,
  "correct_matches": 10,
  "wrong_matches": 2,
  "time_taken_seconds": 95
}
```

No questions needed for this game! ✅

---

## 🔧 HOW TO ADD QUESTIONS

### Method 1: SQL Insert (Direct Database)

```sql
-- Mood Scenario
INSERT INTO mood_scenarios (age_group, scenario_text_en, scenario_text_ur, category, mood_weights, tags)
VALUES (
  '6-8',
  'Your friend broke your favorite toy. What do you feel?',
  'آپ کے دوست نے آپ کا پسندیدہ کھلونا توڑ دیا۔ آپ کو کیسا لگتا ہے؟',
  'emotional',
  '{"Anger": -5, "Forgive": 10, "Happy": 3, "Sad": 0, "Calm": 5}'::jsonb,
  '["anger_control", "forgiveness", "empathy"]'::jsonb
);

-- Scenario Question
INSERT INTO scenario_questions (age_group, question_text_en, question_text_ur, category, options, tags)
VALUES (
  '9-11',
  'Your friend is being bullied. What would you do?',
  'آپ کے دوست کو تنگ کیا جا رہا ہے۔ آپ کیا کریں گے؟',
  'moral',
  '[
    {"option": "Help them", "moral": 10, "emotional": 5, "social": 8},
    {"option": "Tell teacher", "moral": 8, "emotional": 3, "social": 6},
    {"option": "Walk away", "moral": -5, "emotional": -3, "social": -8}
  ]'::jsonb,
  '["bullying", "courage", "empathy"]'::jsonb
);

-- Islamic Quiz Question
INSERT INTO islamic_quiz_questions (
  age_group, question_text_en, question_text_ur, category, options, 
  correct_answer, explanation_en, explanation_ur, difficulty, tags
)
VALUES (
  '6-8',
  'How many daily prayers (Salah) do Muslims perform?',
  'مسلمان روزانہ کتنی نمازیں پڑھتے ہیں؟',
  'spiritual',
  '["3", "4", "5", "6"]'::jsonb,
  '5',
  'Muslims pray 5 times a day: Fajr, Dhuhr, Asr, Maghrib, and Isha.',
  'مسلمان دن میں 5 بار نماز پڑھتے ہیں: فجر، ظہر، عصر، مغرب، اور عشاء۔',
  1,
  '["salah", "pillars", "worship"]'::jsonb
);
```

### Method 2: Python Script (Recommended)

Create a file `scripts/add_game_questions.py`:

```python
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models.game_questions import MoodScenario, ScenarioQuestion, IslamicQuizQuestion

def add_mood_scenarios():
    db = SessionLocal()
    
    scenarios = [
        MoodScenario(
            age_group="6-8",
            scenario_text_en="Your friend broke your favorite toy. What do you feel?",
            scenario_text_ur="آپ کے دوست نے آپ کا پسندیدہ کھلونا توڑ دیا۔",
            category="emotional",
            mood_weights={
                "Anger": -5,
                "Forgive": 10,
                "Happy": 3,
                "Sad": 0,
                "Calm": 5
            },
            tags=["anger_control", "forgiveness", "empathy"]
        ),
        # Add more...
    ]
    
    db.bulk_save_objects(scenarios)
    db.commit()
    print(f"✅ Added {len(scenarios)} mood scenarios")
    db.close()

def add_scenario_questions():
    db = SessionLocal()
    
    questions = [
        ScenarioQuestion(
            age_group="9-11",
            question_text_en="Your friend is being bullied. What would you do?",
            question_text_ur="آپ کے دوست کو تنگ کیا جا رہا ہے۔",
            category="moral",
            options=[
                {"option": "Help them", "moral": 10, "emotional": 5, "social": 8},
                {"option": "Tell teacher", "moral": 8, "emotional": 3, "social": 6},
                {"option": "Walk away", "moral": -5, "emotional": -3, "social": -8}
            ],
            tags=["bullying", "courage", "empathy"]
        ),
        # Add more...
    ]
    
    db.bulk_save_objects(questions)
    db.commit()
    print(f"✅ Added {len(questions)} scenario questions")
    db.close()

def add_islamic_quiz():
    db = SessionLocal()
    
    questions = [
        IslamicQuizQuestion(
            age_group="6-8",
            question_text_en="How many daily prayers (Salah) do Muslims perform?",
            question_text_ur="مسلمان روزانہ کتنی نمازیں پڑھتے ہیں؟",
            category="spiritual",
            options=["3", "4", "5", "6"],
            correct_answer="5",
            explanation_en="Muslims pray 5 times a day.",
            explanation_ur="مسلمان دن میں 5 بار نماز پڑھتے ہیں۔",
            difficulty=1,
            tags=["salah", "pillars"]
        ),
        # Add more...
    ]
    
    db.bulk_save_objects(questions)
    db.commit()
    print(f"✅ Added {len(questions)} Islamic quiz questions")
    db.close()

if __name__ == "__main__":
    add_mood_scenarios()
    add_scenario_questions()
    add_islamic_quiz()
    print("🎉 All questions added successfully!")
```

Run it:
```bash
python scripts/add_game_questions.py
```

### Method 3: JSON File Import

Create `data/game_questions.json`:

```json
{
  "mood_scenarios": [
    {
      "age_group": "6-8",
      "scenario_text_en": "Your friend broke your favorite toy...",
      "category": "emotional",
      "mood_weights": {"Anger": -5, "Forgive": 10},
      "tags": ["anger_control"]
    }
  ],
  "scenario_questions": [...],
  "islamic_quiz": [...]
}
```

Then import with a script similar to Method 2.

---

## 📊 QUICK REFERENCE

### Age Groups
- `"6-8"` - Young children
- `"9-11"` - Pre-teens
- `"12-14"` - Teens

### Categories

**Mood Scenarios:**
- `"emotional"` - Feelings and emotional regulation
- `"social"` - Social interactions
- `"moral"` - Right vs wrong choices

**Scenario Questions:**
- `"moral"` - Ethical decisions
- `"emotional"` - Emotional intelligence
- `"social"` - Social skills

**Islamic Quiz:**
- `"spiritual"` - Worship, faith, practices
- `"cognitive"` - Knowledge, history, facts

### Score Ranges
- **+10**: Excellent choice
- **+5 to +8**: Good choice
- **0 to +3**: Neutral/acceptable
- **-3 to -5**: Poor choice
- **-10**: Very bad choice

---

## ✅ VALIDATION CHECKLIST

Before adding questions, verify:

- [ ] `age_group` is one of: `"6-8"`, `"9-11"`, `"12-14"`
- [ ] English text (`_en`) is provided (required)
- [ ] Urdu text (`_ur`) is provided (optional but recommended)
- [ ] `category` matches allowed values for that game
- [ ] **Mood Scenarios:** `mood_weights` has 4-6 mood options with scores
- [ ] **Scenario Questions:** `options` array has 3-5 choices with behavior scores
- [ ] **Islamic Quiz:** 
  - `options` has 3-4 choices
  - `correct_answer` matches one of the options exactly
  - `difficulty` is 1, 2, or 3
- [ ] `tags` is an array (even if empty: `[]`)
- [ ] No typos in field names
- [ ] JSON is valid (use JSONLint.com to check)

---

## 🎯 BEST PRACTICES

1. **Write clear scenarios** - Make them relatable to the age group
2. **Balance difficulty** - Mix easy, medium, and hard questions
3. **Use proper Urdu** - Get translations verified by native speakers
4. **Score consistently** - Use the score ranges guide above
5. **Test questions** - Make sure they work in the frontend
6. **Add explanations** - Especially for Islamic quiz (helps learning)
7. **Use relevant tags** - Helps with analytics and task generation
8. **Cover diverse topics** - Don't repeat similar scenarios

---

## 📞 NEED HELP?

If you need help adding questions or have questions about the format:
1. Check this document first
2. Look at existing questions in database for examples
3. Test with 1-2 questions before bulk adding
4. Verify JSON format online before inserting

**Happy question writing! 🎮📚**
