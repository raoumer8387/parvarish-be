# 🎮 Games API Quick Reference Card

## 🔗 Base URL
`http://localhost:8000/api/v1/games`

## 🔐 Authentication
All endpoints require: `Authorization: Bearer {JWT_TOKEN}`

---

## 📋 Endpoints Summary

| Game | Get Questions | Submit Complete Session |
|------|---------------|------------------------|
| **Memory** | N/A (frontend only) | `POST /session/memory/complete` |
| **Mood Picker** | `GET /mood/questions?age_group=6-8&limit=5` | `POST /session/mood/complete` |
| **Scenario** | `GET /scenario/questions?age_group=9-11&limit=5` | `POST /session/scenario/complete` |
| **Islamic Quiz** | `GET /islamic-quiz/questions?age_group=12-14&limit=10` | `POST /session/islamic-quiz/complete` |

---

## ⏱️ Time Limits

| Game | Time Limit | Questions | Time/Question |
|------|-----------|-----------|---------------|
| Memory Card | 3 min (180s) | 1 session | N/A |
| Mood Picker | 5 min (300s) | 5 | 60s |
| Scenario | 5 min (300s) | 5 | 60s |
| Islamic Quiz | 4 min (240s) | 10 | 24s |

---

## 📤 Submit Payload Examples

### Mood Picker
```json
{
  "child_id": 15,
  "total_time_seconds": 245,
  "responses": [
    {"scenario_id": 1, "selected_mood": "Forgive", "time_taken": 45},
    {"scenario_id": 2, "selected_mood": "Happy", "time_taken": 50}
    // ... 5 total
  ]
}
```

### Scenario Game
```json
{
  "child_id": 15,
  "total_time_seconds": 280,
  "responses": [
    {"scenario_id": 5, "selected_option": "Help them", "time_taken": 55}
    // ... 5 total
  ]
}
```

### Islamic Quiz
```json
{
  "child_id": 15,
  "total_time_seconds": 210,
  "responses": [
    {"question_id": 2, "selected_answer": "5", "time_taken": 18}
    // ... 10 total
  ]
}
```

### Memory Game
```json
{
  "child_id": 15,
  "total_flips": 24,
  "correct_matches": 10,
  "wrong_matches": 4,
  "time_taken_seconds": 95
}
```

---

## 📥 Success Response

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
  "time_limit": 300,
  "results_saved": 5
}
```

---

## 🏆 Score Ranges

| Percentage | Icon | Message | Description |
|-----------|------|---------|-------------|
| 80-100% | 🌟 | Outstanding! | Excellent performance |
| 60-79% | 👏 | Well done! | Good job |
| 40-59% | 💪 | Good effort! | Keep practicing |
| 0-39% | 📚 | Don't give up! | Needs improvement |

---

## ❌ Common Errors

| Status | Error | Cause | Solution |
|--------|-------|-------|----------|
| 422 | Time limit exceeded | total_time_seconds > limit | Complete faster |
| 422 | Expected N answers, got M | Not all questions answered | Answer all questions |
| 403 | Only children can submit | Parent trying to submit | Login as child |
| 403 | You can only submit for yourself | child_id mismatch | Use correct child_id |

---

## 🧪 Quick Test (cURL)

```bash
# Get questions
curl "http://localhost:8000/api/v1/games/mood/questions?age_group=6-8&limit=5" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Submit session
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

## 📱 Frontend Checklist

- [ ] Timer countdown (MM:SS)
- [ ] Progress indicator (X of Y)
- [ ] Store responses locally
- [ ] Submit all at once
- [ ] Show completion screen
- [ ] Display score percentage
- [ ] Show completion message
- [ ] Handle timeout (auto-submit)

---

## 🔧 Scoring Quick Ref

### Memory
- Base: 10pts × correct matches
- Bonus: Fast completion
- Penalty: Extra flips

### Mood
- Positive: 20pts
- Neutral: 10pts
- Negative: 5pts

### Scenario
- Best: 20pts
- Good: 15pts
- Neutral: 10pts
- Poor: 5pts

### Quiz
- Correct: 10pts
- Fast: +2pts bonus

---

**📚 Full Docs:** See `GAMES_COMPLETE_FLOW.md` for complete implementation guide
