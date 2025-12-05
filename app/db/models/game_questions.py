"""Models for game questions used in child activities."""

from sqlalchemy import Column, Integer, String, Text, JSON
from sqlalchemy.dialects.postgresql import JSONB
from app.db.base import Base


class MoodScenario(Base):
    """Mood Picker game scenarios.
    
    Each scenario presents a situation and child selects mood.
    Maps to emotional/empathy behavior analysis.
    """
    __tablename__ = "mood_scenarios"
    
    id = Column(Integer, primary_key=True, index=True)
    age_group = Column(String, nullable=False)  # e.g., "6-8", "9-11", "12-14"
    scenario_text_en = Column(Text, nullable=False)
    scenario_text_ur = Column(Text, nullable=True)
    scenario_text_roman = Column(Text, nullable=True)  # Roman Urdu
    category = Column(String, nullable=False)  # emotional, social, moral
    # Expected mood options with weights: {"Anger": -5, "Forgive": +5, "Happy": +3, "Sad": 0}
    mood_weights = Column(JSONB, nullable=False)
    tags = Column(JSONB, default=[])  # e.g., ["anger_control", "empathy"]


class ScenarioQuestion(Base):
    """What Would You Do? game scenarios.
    
    Moral/social choice questions with weighted options.
    Maps to moral, emotional, social behavior categories.
    """
    __tablename__ = "scenario_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    age_group = Column(String, nullable=False)
    question_text_en = Column(Text, nullable=False)
    question_text_ur = Column(Text, nullable=True)
    question_text_roman = Column(Text, nullable=True)  # Roman Urdu
    category = Column(String, nullable=False)  # moral, emotional, social
    # Options with behavior score deltas: [{"option": "Hit", "moral": -10, "emotional": -5}, ...]
    options = Column(JSONB, nullable=False)
    tags = Column(JSONB, default=[])


class IslamicQuizQuestion(Base):
    """Islamic knowledge quiz questions.
    
    Tests religious knowledge and values.
    Maps to spiritual and cognitive categories.
    """
    __tablename__ = "islamic_quiz_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    age_group = Column(String, nullable=False)
    question_text_en = Column(Text, nullable=False)
    question_text_ur = Column(Text, nullable=True)
    question_text_roman = Column(Text, nullable=True)  # Roman Urdu
    category = Column(String, nullable=False)  # spiritual, cognitive
    # Multiple choice options
    options = Column(JSONB, nullable=False)  # e.g., ["Option A", "Option B", ...]
    correct_answer = Column(String, nullable=False)
    explanation_en = Column(Text, nullable=True)
    explanation_ur = Column(Text, nullable=True)
    explanation_roman = Column(Text, nullable=True)  # Roman Urdu explanation
    difficulty = Column(Integer, default=1)  # 1=easy, 2=medium, 3=hard
    tags = Column(JSONB, default=[])  # e.g., ["salah", "quran", "prophets"]
