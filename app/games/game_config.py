"""Game configuration and timing rules."""

from typing import Dict, Any

# Game time limits (in seconds)
GAME_TIME_LIMITS = {
    "memory": 180,       # 3 minutes
    "mood": 300,         # 5 minutes
    "scenario": 300,     # 5 minutes
    "islamic_quiz": 180, # 3 minutes (6 questions × 30 seconds each)
}

# Questions per game
QUESTIONS_PER_GAME = {
    "memory": 1,         # Single memory game session
    "mood": 5,           # 5 mood scenarios
    "scenario": 5,       # 5 scenario questions (What Would You Do?)
    "islamic_quiz": 6,   # 6 quiz questions
}

# Time per question (in seconds)
TIME_PER_QUESTION = {
    "mood": 60,          # 1 minute per mood scenario
    "scenario": 60,      # 1 minute per scenario
    "islamic_quiz": 30,  # 30 seconds per quiz question
}

# Score calculation weights
SCORE_WEIGHTS = {
    "memory": {
        "correct_matches": 10,
        "time_bonus": 5,    # Bonus points for fast completion
        "flip_penalty": -1,  # Penalty for excessive flips
    },
    "mood": {
        "positive_response": 20,
        "neutral_response": 10,
        "negative_response": 5,
    },
    "scenario": {
        "best_choice": 20,
        "good_choice": 15,
        "neutral_choice": 10,
        "poor_choice": 5,
    },
    "islamic_quiz": {
        "correct_answer": 10,
        "time_bonus": 2,
    }
}

# Completion messages based on score ranges
COMPLETION_MESSAGES = {
    "excellent": {
        "en": "🌟 Outstanding! You showed great wisdom and understanding!",
        "ur": "بہترین! آپ نے بہت عقلمندی اور سمجھ دکھائی!"
    },
    "good": {
        "en": "👏 Well done! You're learning and growing!",
        "ur": "شاباش! آپ سیکھ رہے ہیں اور ترقی کر رہے ہیں!"
    },
    "average": {
        "en": "💪 Good effort! Keep practicing to improve!",
        "ur": "اچھی کوشش! بہتری کے لیے مشق جاری رکھیں!"
    },
    "needs_improvement": {
        "en": "📚 Don't give up! Practice makes perfect!",
        "ur": "ہمت مت ہارو! مشق سے ہر چیز آسان ہو جاتی ہے!"
    }
}

def get_completion_message(score_percentage: float, language: str = "en") -> str:
    """Get completion message based on score percentage."""
    if score_percentage >= 80:
        return COMPLETION_MESSAGES["excellent"][language]
    elif score_percentage >= 60:
        return COMPLETION_MESSAGES["good"][language]
    elif score_percentage >= 40:
        return COMPLETION_MESSAGES["average"][language]
    else:
        return COMPLETION_MESSAGES["needs_improvement"][language]

def calculate_game_score(game_type: str, game_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate final score for a completed game session.
    
    Returns:
        {
            "total_score": int,
            "max_score": int,
            "percentage": float,
            "breakdown": {...}
        }
    """
    if game_type == "memory":
        return _calculate_memory_score(game_data)
    elif game_type == "mood":
        return _calculate_mood_score(game_data)
    elif game_type == "scenario":
        return _calculate_scenario_score(game_data)
    elif game_type == "islamic_quiz":
        return _calculate_quiz_score(game_data)
    else:
        raise ValueError(f"Unknown game type: {game_type}")

def _calculate_memory_score(data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate score for memory game."""
    weights = SCORE_WEIGHTS["memory"]
    correct = data.get("correct_matches", 0)
    total_flips = data.get("total_flips", 0)
    time_taken = data.get("time_taken_seconds", 0)
    
    # Base score from correct matches
    base_score = correct * weights["correct_matches"]
    
    # Time bonus (if completed in under 2 minutes)
    time_bonus = 0
    if time_taken < 120:
        time_bonus = (120 - time_taken) // 10 * weights["time_bonus"]
    
    # Flip penalty (if took more flips than optimal)
    optimal_flips = correct * 2  # Optimal is 2 flips per match
    flip_penalty = max(0, (total_flips - optimal_flips)) * weights["flip_penalty"]
    
    total_score = max(0, base_score + time_bonus + flip_penalty)
    max_score = correct * weights["correct_matches"] + 30  # Max possible with bonuses
    
    return {
        "total_score": total_score,
        "max_score": max_score,
        "percentage": round((total_score / max_score * 100) if max_score > 0 else 0, 1),
        "breakdown": {
            "base_score": base_score,
            "time_bonus": time_bonus,
            "flip_penalty": flip_penalty
        }
    }

def _calculate_mood_score(data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate score for mood picker game."""
    responses = data.get("responses", [])
    weights = SCORE_WEIGHTS["mood"]
    
    total_score = 0
    for response in responses:
        mood = response.get("selected_mood", "")
        # Categorize mood (this is simplified - adjust based on scenario)
        if mood in ["Forgive", "Happy", "Help"]:
            total_score += weights["positive_response"]
        elif mood in ["Calm", "Think"]:
            total_score += weights["neutral_response"]
        else:
            total_score += weights["negative_response"]
    
    max_score = len(responses) * weights["positive_response"]
    
    return {
        "total_score": total_score,
        "max_score": max_score,
        "percentage": round((total_score / max_score * 100) if max_score > 0 else 0, 1),
        "breakdown": {
            "questions_answered": len(responses),
            "total_questions": QUESTIONS_PER_GAME["mood"]
        }
    }

def _calculate_scenario_score(data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate score for scenario game."""
    responses = data.get("responses", [])
    
    total_score = sum(r.get("score", 0) for r in responses)
    max_score = len(responses) * 20  # Assuming max 20 points per question
    
    return {
        "total_score": total_score,
        "max_score": max_score,
        "percentage": round((total_score / max_score * 100) if max_score > 0 else 0, 1),
        "breakdown": {
            "questions_answered": len(responses),
            "total_questions": QUESTIONS_PER_GAME["scenario"]
        }
    }

def _calculate_quiz_score(data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate score for Islamic quiz."""
    responses = data.get("responses", [])
    weights = SCORE_WEIGHTS["islamic_quiz"]
    
    correct_count = sum(1 for r in responses if r.get("is_correct", False))
    base_score = correct_count * weights["correct_answer"]
    
    # Time bonus for quick correct answers
    time_bonus = 0
    for response in responses:
        if response.get("is_correct") and response.get("time_taken", 999) < 15:
            time_bonus += weights["time_bonus"]
    
    total_score = base_score + time_bonus
    max_score = len(responses) * (weights["correct_answer"] + weights["time_bonus"])
    
    return {
        "total_score": total_score,
        "max_score": max_score,
        "percentage": round((total_score / max_score * 100) if max_score > 0 else 0, 1),
        "breakdown": {
            "correct_answers": correct_count,
            "total_questions": len(responses),
            "time_bonus": time_bonus
        }
    }

def validate_game_completion(game_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that game was completed properly.
    
    Returns:
        {
            "valid": bool,
            "message": str,
            "missing": list
        }
    """
    expected_questions = QUESTIONS_PER_GAME.get(game_type, 0)
    
    if game_type == "memory":
        required_fields = ["total_flips", "correct_matches", "wrong_matches", "time_taken_seconds"]
        missing = [f for f in required_fields if f not in data]
        
        return {
            "valid": len(missing) == 0,
            "message": "All fields present" if not missing else f"Missing fields: {missing}",
            "missing": missing
        }
    
    else:
        # For question-based games
        responses = data.get("responses", [])
        
        return {
            "valid": len(responses) == expected_questions,
            "message": f"Expected {expected_questions} answers, got {len(responses)}",
            "missing": [] if len(responses) == expected_questions else ["incomplete_responses"]
        }
