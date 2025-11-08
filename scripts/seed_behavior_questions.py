"""Bulk import behavior questions from a JSON file into the DB.

Usage (Windows PowerShell):
  # Activate your venv first if needed
  # python scripts/seed_behavior_questions.py

By default reads from app/behavoiur_questions.txt (array of objects).
Maps question_en to Question.question_text_template, converting
"your child" phrasing to a {child_name} template for personalization.
"""
from __future__ import annotations

import json
import os
import re
import sys
from typing import List, Dict

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.db.models.behavior_models import Question


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
DEFAULT_PATH = os.path.join(ROOT, "app", "behavoiur_questions.txt")


def to_template(text: str) -> str:
    """Convert phrases like 'Does your child ...' to 'Does {child_name} ...?'
    Handles 'Does/Is/Has/Did/Was/Will/Can/Should your child'.
    Leaves text unchanged if pattern not found.
    """
    patterns = [
        r"\b(Does|Is|Has|Did|Was|Will|Can|Should)\s+your\s+child\b",
        r"\b(Does|Is|Has|Did|Was|Will|Can|Should)\s+the\s+child\b",
    ]
    for pat in patterns:
        if re.search(pat, text, flags=re.IGNORECASE):
            return re.sub(pat, r"\\1 {child_name}", text, flags=re.IGNORECASE)
    # Also try generic 'your child' replacement
    return re.sub(r"\byour\s+child\b", "{child_name}", text, flags=re.IGNORECASE)


def load_questions(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def upsert_questions(data: List[Dict], dry_run: bool = False) -> Dict[str, int]:
    db = SessionLocal()
    created = 0
    skipped = 0

    try:
        for item in data:
            en = item.get("question_en") or item.get("question") or ""
            if not en:
                skipped += 1
                continue
            template = to_template(en).strip()
            category = (item.get("category") or "uncategorized").strip()
            age_group = (item.get("age_group") or "").strip() or None
            options = item.get("options") or ["Yes", "No"]
            weight = int(item.get("weight") or 1)

            # Skip if identical template already exists
            existing = db.query(Question).filter(Question.question_text_template == template).first()
            if existing:
                skipped += 1
                continue

            if not dry_run:
                q = Question(
                    question_text_template=template,
                    category=category,
                    age_group=age_group,
                    options=options,
                    weight=weight,
                )
                db.add(q)
                created += 1
        if not dry_run:
            db.commit()
    finally:
        db.close()

    return {"created": created, "skipped": skipped}


def main():
    path = os.environ.get("SEED_PATH", DEFAULT_PATH)
    if not os.path.isfile(path):
        raise SystemExit(f"Input file not found: {path}")

    data = load_questions(path)
    result = upsert_questions(data)
    print(f"Imported questions from {path}")
    print(f"Created: {result['created']} | Skipped (duplicates): {result['skipped']}")


if __name__ == "__main__":
    main()
