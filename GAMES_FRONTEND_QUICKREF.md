# 🎮 Games API - Frontend Quick Reference

## Base URL
`/api/v1/games`

---

## 🔐 Authentication

**All endpoints require Bearer token in header:**
```
Authorization: Bearer <JWT_TOKEN>
```

**Role-based access:**
- 🧒 **Child** = Can fetch questions + submit results
- 👨‍👩‍👧 **Parent** = Can view analysis dashboard only

---

## 🧒 CHILD ENDPOINTS (Fetch & Play)

### 1️⃣ Memory Card Match
**No questions needed** - frontend tracks flips/matches

#### Submit Result
```http
POST /games/memory/submit
Content-Type: application/json

{
  "child_id": 1,
  "total_flips": 24,
  "correct_matches": 10,
  "wrong_matches": 5,
  "time_taken_seconds": 95
}
```

**Response:**
```json
{
  "result_id": "uuid",
  "analysis": { "cognitive": 78, "focus": 70 },
  "tasks_generated": 1
}
```

---

### 2️⃣ Mood Picker

#### Get Scenarios
```http
GET /games/mood/questions?age_group=6-8&limit=5
```

**Response:**
```json
{
  "scenarios": [
    {
      "id": 1,
      "scenario_en": "Your friend broke your favorite toy...",
      "scenario_ur": "Aapke dost ne...",
      "category": "emotional",
      "mood_options": ["Anger", "Forgive", "Happy", "Sad"]
    }
  ]
}
```

#### Submit Mood
```http
POST /games/mood/submit
Content-Type: application/json

{
  "child_id": 1,
  "scenario_id": 3,
  "selected_mood": "Forgive"
}
```

**Response:**
```json
{
  "result_id": "uuid",
  "analysis": { "emotional_control": 80, "empathy": 75 },
  "tasks_generated": 1
}
```

---

### 3️⃣ What Would You Do?

#### Get Scenario Questions
```http
GET /games/scenario/questions?age_group=9-11&limit=5
```

**Response:**
```json
{
  "questions": [
    {
      "id": 2,
      "question_en": "Your friend pushed you...",
      "question_ur": "Aapke dost ne...",
      "category": "moral",
      "options": ["Push them back", "Tell a teacher", "Forgive"]
    }
  ]
}
```

#### Submit Choice
```http
POST /games/scenario/submit
Content-Type: application/json

{
  "child_id": 1,
  "scenario_id": 2,
  "selected_option": "Forgive"
}
```

**Response:**
```json
{
  "result_id": "uuid",
  "analysis": { "moral": 75, "emotional": 65, "social": 70 },
  "tasks_generated": 1
}
```

---

### 4️⃣ Islamic Quiz

#### Get Quiz Questions
```http
GET /games/islamic-quiz/questions?age_group=12-14&difficulty=2&limit=5
```

**Response:**
```json
{
  "questions": [
    {
      "id": 5,
      "question_en": "What is the first pillar of Islam?",
      "question_ur": "Islam ka pehla rukn kya hai?",
      "category": "spiritual",
      "options": ["Salah", "Zakat", "Shahada", "Hajj"],
      "difficulty": 1
    }
  ]
}
```
⚠️ **Note:** `correct_answer` is NOT returned (anti-cheat)

#### Submit Answer
```http
POST /games/islamic-quiz/submit
Content-Type: application/json

{
  "child_id": 1,
  "question_id": 5,
  "selected_answer": "Shahada"
}
```

**Response:**
```json
{
  "result_id": "uuid",
  "analysis": { "spiritual": 75, "cognitive": 65 },
  "tasks_generated": 1
}
```

---

## 👨‍👩‍👧 PARENT ENDPOINT (Dashboard)

### Get Child Analysis
```http
GET /games/{child_id}/analysis
```

**Response:**
```json
{
  "dominant_strength": "Cognitive",
  "needs_improvement": "Moral",
  "suggested_task": "Honesty task",
  "category_scores": {
    "emotional": 72,
    "cognitive": 80,
    "moral": 60,
    "spiritual": 55,
    "social": 68
  }
}
```

---

## ⚠️ Error Responses

### 403 Forbidden (Wrong Role)
```json
{ "detail": "Only children can access game questions" }
{ "detail": "Only child accounts can submit game results" }
{ "detail": "Child can only submit their own results" }
```

### 422 Unprocessable
```json
{ "detail": "Missing field: scenario_id" }
```

### 404 Not Found
```json
{ "detail": "Child not found" }
```

---

## 🎨 UI Component Map

### Child Pages
```
/child/games
  ├─ Memory Match Card
  ├─ Mood Picker Card
  ├─ Scenario Game Card
  └─ Islamic Quiz Card

/child/games/memory
  └─ [Grid of flip cards, timer, submit button]

/child/games/mood
  └─ [Scenario text, 4 mood emoji buttons]

/child/games/scenario
  └─ [Question text, option buttons]

/child/games/quiz
  └─ [Question, multiple choice, submit]
```

### Parent Dashboard
```
/parent/dashboard/{childId}
  ├─ Category Scores Chart (Radar/Bar)
  ├─ Strengths Badge
  ├─ Needs Improvement Alert
  └─ Suggested Tasks List
```

---

## 🔄 Typical Flow

### Child Playing Mood Game
```typescript
// 1. Fetch scenarios
const { scenarios } = await fetch('/api/v1/games/mood/questions?age_group=6-8', {
  headers: { Authorization: `Bearer ${childToken}` }
}).then(r => r.json());

// 2. Display scenario + mood buttons

// 3. Submit selection
const result = await fetch('/api/v1/games/mood/submit', {
  method: 'POST',
  headers: {
    Authorization: `Bearer ${childToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    child_id: currentChildId,
    scenario_id: scenarios[0].id,
    selected_mood: 'Forgive'
  })
}).then(r => r.json());

// 4. Show analysis + confetti
console.log(result.analysis); // { emotional_control: 80, empathy: 75 }
```

### Parent Viewing Dashboard
```typescript
const analysis = await fetch(`/api/v1/games/${childId}/analysis`, {
  headers: { Authorization: `Bearer ${parentToken}` }
}).then(r => r.json());

// Display chart with category_scores
// Show badge for dominant_strength
// Alert for needs_improvement
```

---

## 📦 Query Parameters

| Endpoint | Param | Values | Default |
|----------|-------|--------|---------|
| `/mood/questions` | `age_group` | "6-8", "9-11", "12-14" | all |
| `/mood/questions` | `limit` | number | 5 |
| `/scenario/questions` | `age_group` | "6-8", "9-11", "12-14" | all |
| `/scenario/questions` | `limit` | number | 5 |
| `/islamic-quiz/questions` | `age_group` | "6-8", "9-11", "12-14" | all |
| `/islamic-quiz/questions` | `difficulty` | 1, 2, 3 | all |
| `/islamic-quiz/questions` | `limit` | number | 5 |

---

## ✅ Pre-Launch Checklist

- [ ] Auth tokens work (child + parent)
- [ ] Age group filtering tested
- [ ] Submit endpoints return 200
- [ ] Analysis endpoint shows scores
- [ ] Child can't access parent endpoint (403)
- [ ] Parent can't play games (403)
- [ ] Urdu text displays correctly
- [ ] Confetti on game completion
- [ ] Tasks appear after submission

---

## 🎯 Behavior Categories

| Category | Games That Track It |
|----------|---------------------|
| **Cognitive** | Memory Match, Islamic Quiz |
| **Focus** | Memory Match |
| **Emotional** | Mood Picker, Scenario Game |
| **Moral** | Scenario Game |
| **Social** | Scenario Game |
| **Spiritual** | Islamic Quiz |
| **Empathy** | Mood Picker |

---

## 🌐 Language Support

All questions include both:
- `question_en` / `scenario_en` (English)
- `question_ur` / `scenario_ur` (Urdu)

Frontend should detect user language preference and display accordingly.

---

## 📊 Score Interpretation

| Score Range | Meaning | UI Treatment |
|-------------|---------|--------------|
| 0-40 | Needs Work | Red, suggest task |
| 41-60 | Developing | Yellow |
| 61-80 | Good | Green |
| 81-100 | Excellent | Gold star ⭐ |

---

## 🚀 Quick Start

1. **Get child token** from login
2. **Fetch questions** for selected game
3. **Display UI** with options
4. **Submit result** when child completes
5. **Show feedback** with confetti + scores
6. **Optional:** Show new tasks generated

---

## 📞 Support

- API Docs: `/GAMES_API_DOCUMENTATION.md`
- Implementation Summary: `/GAMES_IMPLEMENTATION_SUMMARY.md`
- Backend Team: [Your contact]

---

**Happy Coding! 🎉**
