# ✅ Games Implementation - Complete with Timer & Scoring

## 🎯 What's New

### ⏱️ Timer System
- **Global time limits** for each game type
- **Per-question time tracking** for detailed analytics
- **Auto-submit** when time runs out
- **Visual countdown** with urgent state (< 30 seconds)

### 🎮 Complete Session Model
- **All questions must be answered** - No partial submissions
- **Batch submission** - Submit entire game session at once
- **Score calculation** - Comprehensive scoring with bonuses/penalties
- **Completion messages** - Personalized feedback based on performance

### 📊 Scoring Features
- **Percentage-based** - Easy to understand (0-100%)
- **Breakdown** - Shows how score was calculated
- **Time bonuses** - Reward fast, accurate responses
- **Performance tiers** - Excellent (80%+), Good (60%+), Average (40%+), Needs Improvement (<40%)

---

## 📁 Files Created/Modified

### New Files:
1. **`app/games/game_config.py`**
   - Game time limits and question counts
   - Score calculation algorithms
   - Completion message logic
   - Validation functions

2. **`GAMES_COMPLETE_FLOW.md`**
   - Complete frontend integration guide
   - Timer implementation examples
   - React component samples
   - API usage with all new endpoints

### Modified Files:
1. **`app/routes/games.py`**
   - Added 4 new batch submission endpoints:
     - `POST /games/session/mood/complete`
     - `POST /games/session/scenario/complete`
     - `POST /games/session/islamic-quiz/complete`
     - `POST /games/session/memory/complete`
   - Each returns score, message, and task count

2. **`migrations/007_add_child_game_results.py`**
   - Fixed logic to actually create table in database

---

## 🎮 Game Configuration

```python
# Time Limits (seconds)
GAME_TIME_LIMITS = {
    "memory": 180,       # 3 minutes
    "mood": 300,         # 5 minutes
    "scenario": 300,     # 5 minutes
    "islamic_quiz": 240, # 4 minutes (10 questions × 24s)
}

# Questions Required
QUESTIONS_PER_GAME = {
    "memory": 1,         # Single session
    "mood": 5,           # 5 scenarios
    "scenario": 5,       # 5 questions
    "islamic_quiz": 10,  # 10 questions
}
```

---

## 📡 New API Endpoints

### Complete Session Endpoints

All endpoints require:
- Bearer token authentication
- Child role (not parent)
- All questions answered
- Within time limit

#### 1. Mood Picker Complete
```http
POST /api/v1/games/session/mood/complete
{
  "child_id": 15,
  "total_time_seconds": 245,
  "responses": [
    {
      "scenario_id": 1,
      "selected_mood": "Forgive",
      "time_taken": 45
    }
    // ... 5 total responses required
  ]
}
```

**Returns:**
```json
{
  "success": true,
  "game_type": "mood",
  "score": {
    "total_score": 85,
    "max_score": 100,
    "percentage": 85.0,
    "breakdown": {
      "questions_answered": 5,
      "total_questions": 5
    }
  },
  "completion_message": "🌟 Outstanding! You showed great wisdom!",
  "tasks_generated": 2,
  "time_taken": 245,
  "time_limit": 300
}
```

#### 2. Scenario Game Complete
```http
POST /api/v1/games/session/scenario/complete
{
  "child_id": 15,
  "total_time_seconds": 280,
  "responses": [
    {
      "scenario_id": 5,
      "selected_option": "Help them study",
      "time_taken": 55
    }
    // ... 5 total
  ]
}
```

#### 3. Islamic Quiz Complete
```http
POST /api/v1/games/session/islamic-quiz/complete
{
  "child_id": 15,
  "total_time_seconds": 210,
  "responses": [
    {
      "question_id": 2,
      "selected_answer": "5",
      "time_taken": 18
    }
    // ... 10 total
  ]
}
```

**Returns:**
```json
{
  "score": {
    "breakdown": {
      "correct_answers": 8,
      "total_questions": 10,
      "time_bonus": 12
    }
  },
  "correct_answers": 8
}
```

#### 4. Memory Game Complete
```http
POST /api/v1/games/session/memory/complete
{
  "child_id": 15,
  "total_flips": 24,
  "correct_matches": 10,
  "wrong_matches": 4,
  "time_taken_seconds": 95
}
```

---

## 🏆 Score Calculation

### Memory Game
- **Base Score**: 10 points per correct match
- **Time Bonus**: +5 points per 10 seconds under 2 minutes
- **Flip Penalty**: -1 point per extra flip beyond optimal

### Mood Picker
- **Positive Response** (Forgive, Happy, Help): 20 points
- **Neutral Response** (Calm, Think): 10 points
- **Negative Response**: 5 points

### Scenario Game
- **Best Choice**: 20 points
- **Good Choice**: 15 points
- **Neutral Choice**: 10 points
- **Poor Choice**: 5 points

### Islamic Quiz
- **Correct Answer**: 10 points
- **Time Bonus**: +2 points if answered in < 15 seconds

---

## 💬 Completion Messages

Based on score percentage:

| Score Range | Message (EN) | Message (UR) |
|-------------|--------------|--------------|
| 80-100% | 🌟 Outstanding! You showed great wisdom! | بہترین! آپ نے عقلمندی دکھائی! |
| 60-79% | 👏 Well done! You're learning! | شاباش! آپ سیکھ رہے ہیں! |
| 40-59% | 💪 Good effort! Keep practicing! | اچھی کوشش! مشق جاری رکھیں! |
| 0-39% | 📚 Don't give up! Practice makes perfect! | ہمت مت ہارو! مشق سے آسان ہوگا! |

---

## ✅ Validation Rules

All submissions are validated:

1. **Time Limit Check**
   - Auto-reject if `total_time_seconds` > game's time limit
   - Error: "Time limit exceeded. Max: {limit}s"

2. **Complete Answers Check**
   - Must answer all required questions
   - Error: "Expected {N} answers, got {M}"

3. **Authentication Check**
   - Must be logged in as child
   - Must submit for own child_id
   - Error: "You can only submit results for yourself"

---

## 🎨 Frontend Implementation Summary

### Timer Component
```jsx
const [timeLeft, setTimeLeft] = useState(GAME_TIME_LIMITS[gameType]);

useEffect(() => {
  const timer = setInterval(() => {
    setTimeLeft(prev => {
      if (prev <= 1) {
        handleTimeUp(); // Auto-submit
        return 0;
      }
      return prev - 1;
    });
  }, 1000);
  return () => clearInterval(timer);
}, []);
```

### Progress Tracking
```jsx
const [currentQuestion, setCurrentQuestion] = useState(0);
const [responses, setResponses] = useState([]);

// Show: "Question 3 of 5"
<ProgressBar current={currentQuestion + 1} total={questions.length} />
```

### Completion Screen
```jsx
if (gameComplete) {
  return (
    <CompletionScreen
      score={result.score}
      message={result.completion_message}
      tasksGenerated={result.tasks_generated}
    />
  );
}
```

---

## 🔄 Game Flow

```
1. Child clicks "Play Game"
   ↓
2. Fetch questions (GET /games/{type}/questions)
   ↓
3. Start timer (countdown begins)
   ↓
4. Show question 1 of N
   ↓
5. Child selects answer
   ↓
6. Store response locally
   ↓
7. Move to next question (or step 8 if last)
   ↓
8. Submit ALL responses (POST /games/session/{type}/complete)
   ↓
9. Show completion screen with:
   - Final score (percentage)
   - Completion message
   - Tasks generated count
   - Time taken vs limit
   ↓
10. Redirect to dashboard
```

---

## 🧪 Testing the API

### Test Mood Game
```bash
# 1. Get questions
curl -X GET "http://localhost:8000/api/v1/games/mood/questions?age_group=6-8&limit=5" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 2. Submit complete session
curl -X POST "http://localhost:8000/api/v1/games/session/mood/complete" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "child_id": 15,
    "total_time_seconds": 245,
    "responses": [
      {"scenario_id": 1, "selected_mood": "Forgive", "time_taken": 45},
      {"scenario_id": 2, "selected_mood": "Happy", "time_taken": 50},
      {"scenario_id": 3, "selected_mood": "Calm", "time_taken": 48},
      {"scenario_id": 4, "selected_mood": "Help", "time_taken": 52},
      {"scenario_id": 5, "selected_mood": "Forgive", "time_taken": 50}
    ]
  }'
```

---

## 📚 Documentation Files

1. **`GAMES_COMPLETE_FLOW.md`** - Main frontend guide
   - Timer implementation
   - Complete React examples
   - API reference
   - UI/UX recommendations

2. **`GAMES_API_DOCUMENTATION.md`** - Original API docs
   - Still valid for question fetching
   - Single submission endpoints (legacy)

3. **`GAMES_IMPLEMENTATION_SUMMARY.md`** - Backend summary
   - Architecture overview
   - Database schema
   - Service layer details

---

## 🚀 Ready to Use!

All backend changes are complete:
- ✅ Timer limits configured
- ✅ Score calculation implemented
- ✅ Completion messages ready
- ✅ Batch submission endpoints created
- ✅ Validation rules enforced
- ✅ Database tables verified
- ✅ Authentication fixed

**Next Step:** Implement frontend using `GAMES_COMPLETE_FLOW.md` as your guide!

---

## 📞 Support

If you encounter issues:
1. Check `GAMES_COMPLETE_FLOW.md` for examples
2. Verify child authentication
3. Ensure all questions answered
4. Check time limits not exceeded
5. Review error messages from API
