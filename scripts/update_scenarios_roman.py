"""Script to update existing mood scenarios with Roman Urdu text."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models.game_questions import MoodScenario


def update_scenarios_with_roman():
    """Update existing scenarios with Roman Urdu text."""
    db = SessionLocal()
    
    try:
        # Define updates: scenario_text_en -> scenario_text_roman mapping
        updates = {
            "Your friend broke your favorite toy. How do you feel?": 
                "Aap ke dost ne aap ka pasandeeda khilona tor diya. Aap kaise mehsoos karte ho?",
            
            "Your teacher scolded you in front of the class. How do you feel?":
                "Aap ke teacher ne sab ke samnay aapko daanta. Aap kaisa mehsoos karte ho?",
            
            "Your sibling took your pencil without asking. How do you feel?":
                "Aap ke behn bhai ne baghair poochay aap ki pencil le li. Aap kaise mehsoos karte ho?",
            
            "You helped someone and nobody thanked you. How do you feel?":
                "Aap ne kisi ki madad ki lekin kisi ne shukriya nahi kaha. Aap kaisa mehsoos karte ho?",
            
            "Someone laughed at you in front of others. How do you feel?":
                "Kisi ne sab ke samnay aap ka mazak uraya. Aap ko kaisa laga?"
        }
        
        updated_count = 0
        
        for english_text, roman_text in updates.items():
            scenario = db.query(MoodScenario).filter(
                MoodScenario.scenario_text_en == english_text
            ).first()
            
            if scenario:
                scenario.scenario_text_roman = roman_text
                updated_count += 1
                print(f"✅ Updated: {english_text[:50]}...")
            else:
                print(f"⚠️  Not found: {english_text[:50]}...")
        
        db.commit()
        print(f"\n🎉 Successfully updated {updated_count}/{len(updates)} scenarios with Roman Urdu text!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error updating scenarios: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("📝 Updating mood scenarios with Roman Urdu text...\n")
    update_scenarios_with_roman()
    print("\n✨ Done!")
