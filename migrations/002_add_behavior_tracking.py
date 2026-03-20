"""Migration: Add behavior tracking tables."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text
from app.db.session import engine
from app.db.base import Base
from app.db.models.behavior_models import Question, ChildBehaviorResponse

def run_migration():
    """Add behavior tracking tables to database."""
    
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    print("🔍 Checking existing tables...")
    print(f"   Found tables: {existing_tables}")
    
    # Check if tables already exist
    if "questions" in existing_tables and "child_behavior_responses" in existing_tables:
        print("✅ Behavior tracking tables already exist. Skipping creation.")
        return
    
    print("\n📦 Creating behavior tracking tables...")
    
    # Create tables
    Base.metadata.create_all(bind=engine, tables=[
        Question.__table__,
        ChildBehaviorResponse.__table__
    ])
    
    print("✅ Tables created successfully!")
    
    # Seed sample questions
    print("\n🌱 Seeding sample questions...")
    seed_sample_questions()
    
    print("\n✅ Migration completed successfully!")


def seed_sample_questions():
    """Seed database with sample behavior questions."""
    
    from sqlalchemy.orm import Session
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    
    try:
        # Check if questions already exist
        existing_count = db.query(Question).count()
        if existing_count > 0:
            print(f"   Found {existing_count} existing questions. Skipping seed.")
            return
        
        sample_questions = [
            # Emotional category
            {
                "question_text_template": "Does {child_name} get angry quickly?",
                "category": "emotional",
                "options": ["Yes", "No", "Sometimes"],
                "weight": 2
            },
            {
                "question_text_template": "Has {child_name} been happy today?",
                "category": "emotional",
                "options": ["Yes", "No", "Sometimes"],
                "weight": 1
            },
            {
                "question_text_template": "Does {child_name} cry often?",
                "category": "emotional",
                "options": ["Yes", "No", "Sometimes"],
                "weight": 2
            },
            {
                "question_text_template": "Is {child_name} easily frustrated?",
                "category": "emotional",
                "options": ["Yes", "No", "Sometimes"],
                "weight": 2
            },
            
            # Social category
            {
                "question_text_template": "Does {child_name} play well with siblings?",
                "category": "social",
                "options": ["Yes", "No", "Sometimes"],
                "weight": 1
            },
            {
                "question_text_template": "Does {child_name} share toys with others?",
                "category": "social",
                "options": ["Yes", "No", "Sometimes"],
                "weight": 1
            },
            {
                "question_text_template": "Is {child_name} friendly with new people?",
                "category": "social",
                "options": ["Yes", "No", "Sometimes"],
                "weight": 1
            },
            {
                "question_text_template": "Does {child_name} help others when asked?",
                "category": "social",
                "options": ["Yes", "No", "Sometimes"],
                "weight": 2
            },
            
            # Physical category
            {
                "question_text_template": "Has {child_name} eaten lunch today?",
                "category": "physical",
                "options": ["Yes", "No"],
                "weight": 1
            },
            {
                "question_text_template": "Did {child_name} sleep well last night?",
                "category": "physical",
                "options": ["Yes", "No"],
                "weight": 1
            },
            {
                "question_text_template": "Is {child_name} physically active today?",
                "category": "physical",
                "options": ["Yes", "No", "Sometimes"],
                "weight": 1
            },
            {
                "question_text_template": "Has {child_name} complained of any pain?",
                "category": "physical",
                "options": ["Yes", "No"],
                "weight": 3
            },
            
            # Behavioral category
            {
                "question_text_template": "Does {child_name} listen to instructions?",
                "category": "behavioral",
                "options": ["Yes", "No", "Sometimes"],
                "weight": 2
            },
            {
                "question_text_template": "Has {child_name} completed homework today?",
                "category": "behavioral",
                "options": ["Yes", "No"],
                "weight": 1
            },
            {
                "question_text_template": "Does {child_name} follow rules at home?",
                "category": "behavioral",
                "options": ["Yes", "No", "Sometimes"],
                "weight": 2
            },
            {
                "question_text_template": "Is {child_name} respectful to elders?",
                "category": "behavioral",
                "options": ["Yes", "No", "Sometimes"],
                "weight": 3
            },
            
            # Religious/Spiritual category
            {
                "question_text_template": "Did {child_name} pray today?",
                "category": "religious",
                "options": ["Yes", "No"],
                "weight": 2
            },
            {
                "question_text_template": "Does {child_name} ask questions about religion?",
                "category": "religious",
                "options": ["Yes", "No", "Sometimes"],
                "weight": 1
            },
        ]
        
        for q_data in sample_questions:
            question = Question(**q_data)
            db.add(question)
        
        db.commit()
        print(f"   ✅ Seeded {len(sample_questions)} sample questions")
        
    except Exception as e:
        print(f"   ❌ Error seeding questions: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("="*60)
    print("   MIGRATION: Add Behavior Tracking Tables")
    print("="*60)
    run_migration()
    print("\n" + "="*60)
