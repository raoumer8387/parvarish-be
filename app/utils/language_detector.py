
from typing import Literal
import re

# Basic character range checks for script detection
_URDU_SCRIPT_PATTERN = re.compile(r"[\u0600-\u06FF]")

def detect_language(text: str) -> Literal["en", "ur", "rm"]:
    """
    Detects the language of the input text (English, Urdu, or Roman Urdu).
    
    This is a simple heuristic-based detector.
    - If it contains Arabic/Urdu script characters, it's 'ur'.
    - Otherwise, it's treated as 'en' or 'rm'. The model can differentiate.
      For our purpose, we will default to 'en' if no urdu script is found.
      A more sophisticated check could analyze common Roman Urdu words, but for now,
      this is sufficient to distinguish script.
    """
    if _URDU_SCRIPT_PATTERN.search(text):
        return "ur"
    
    # Simple check for Roman Urdu keywords, otherwise default to English
    roman_urdu_keywords = [
        "kaise", "kya", "hai", "mein", "aur", "ko", "se", "ki", 
        "par", "hota", "hoti", "karte", "karna", "acha", "koi"
    ]
    text_lower = text.lower()
    if any(word in text_lower.split() for word in roman_urdu_keywords):
        return "rm"
        
    return "en"
