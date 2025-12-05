"""Migration: Seed extended behavior categories (moral, habitual, cognitive, spiritual).

Run with: python migrations/005_add_extended_behavior_categories.py

Adds sample questions for new categories ONLY if those categories have no questions yet,
to avoid duplicates on repeated runs.
"""

import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import inspect
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.db.models.behavior_models import Question


NEW_CATEGORIES = {
    "moral": [
        ("Has {child_name} spoken truthfully today?", ["Yes", "No", "Sometimes"], 2),
        ("Did {child_name} help someone without being asked?", ["Yes", "No", "Sometimes"], 3),
    ],
    "habitual": [
        ("Did {child_name} follow the morning routine?", ["Yes", "No", "Sometimes"], 2),
        ("Was {child_name}'s bedtime routine consistent?", ["Yes", "No", "Sometimes"], 2),
    ],
    "cognitive": [
        ("Did {child_name} stay focused during study time?", ["Yes", "No", "Sometimes"], 2),
        ("Did {child_name} complete a thinking/puzzle activity today?", ["Yes", "No", "Sometimes"], 1),
    ],
    "spiritual": [
        ("Did {child_name} reflect on a moral story today?", ["Yes", "No", "Sometimes"], 1),
        ("Did {child_name} practice a gratitude moment?", ["Yes", "No", "Sometimes"], 1),
    ],
}


def category_exists(db: Session, category: str) -> bool:
    return db.query(Question).filter(Question.category.ilike(category)).first() is not None


def seed_extended_categories():
    db = SessionLocal()
    try:
        added_total = 0
        for cat, qs in NEW_CATEGORIES.items():
            if category_exists(db, cat):
                # Check if at least one existing; if yes, skip entire category seeding
                continue
            for text, options, weight in qs:
                q = Question(
                    question_text_template=text,
                    category=cat,
                    options=options,
                    weight=weight,
                )
                db.add(q)
                added_total += 1
        if added_total:
            db.commit()
        print(f"✅ Seeded {added_total} new questions across extended categories.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding extended categories: {e}")
        import traceback; traceback.print_exc()
    finally:
        db.close()


def run():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if "questions" not in tables:
        print("⚠ 'questions' table not found. Run earlier migrations first.")
        return
    seed_extended_categories()


if __name__ == "__main__":
    run()
