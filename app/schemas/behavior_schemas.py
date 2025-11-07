"""Pydantic schemas for behavior tracking."""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class PersonalizedQuestion(BaseModel):
    """Schema for a personalized question for a specific child."""
    child_id: int
    child_name: str
    question_id: int
    question_text: str
    options: List[str]
    category: str
    
    class Config:
        from_attributes = True


class BehaviorResponseItem(BaseModel):
    """Single behavior response from parent."""
    child_id: int
    question_id: int
    answer: str


class BehaviorResponseRequest(BaseModel):
    """Request schema for submitting multiple behavior responses."""
    responses: List[BehaviorResponseItem]


class BehaviorResponseResult(BaseModel):
    """Response schema after saving behavior responses."""
    message: str
    saved_count: int


class QuestionCreate(BaseModel):
    """Schema for creating a new question."""
    question_text_template: str
    category: str
    options: List[str] = ["Yes", "No"]
    weight: int = 1


class QuestionRead(BaseModel):
    """Schema for reading a question."""
    id: int
    question_text_template: str
    category: str
    options: List[str]
    weight: int
    created_at: datetime
    
    class Config:
        from_attributes = True
