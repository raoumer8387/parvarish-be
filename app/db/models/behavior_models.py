"""Behavior tracking models for children."""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Question(Base):
    """Behavior questions with templates for personalization."""
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    question_text_template = Column(Text, nullable=False)  # e.g., "Has {child_name} eaten lunch today?"
    category = Column(String, nullable=False)  # e.g., 'emotional', 'social', 'physical'
    age_group = Column(String, nullable=True)  # e.g., '6-8', '9-11', '12-14'
    options = Column(JSON, default=["Yes", "No"])  # Answer options
    weight = Column(Integer, default=1)  # Weight for scoring
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to responses
    responses = relationship("ChildBehaviorResponse", back_populates="question")


class ChildBehaviorResponse(Base):
    """Stores parent's answers about child behavior."""
    __tablename__ = "child_behavior_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    question_text = Column(Text, nullable=False)  # Personalized question text
    answer = Column(String, nullable=False)  # e.g., "Yes", "No", "Sometimes"
    score = Column(Integer, default=0)  # Computed score based on answer
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    question = relationship("Question", back_populates="responses")
    child = relationship("Child", backref="behavior_responses")
