# Parvarish AI - Games API Documentation

## Overview

The Games system provides **4 interactive, Islamic-themed activities** for children that feed into behavioral analysis and task generation. All game questions are stored in the database with rich, age-appropriate content mapped to behavior categories.

---

## Architecture

### Database Tables

1. **child_game_results** - Stores game outcomes and analysis scores
2. **mood_scenarios** - Mood Picker game scenarios
3. **scenario_questions** - "What Would You Do?" moral choice questions
4. **islamic_quiz_questions** - Islamic knowledge quiz questions

### Behavior Categories

Games map to these behavior categories (same as daily behavior questions):
- **Emotional** - anger control, empathy, emotional regulation
- **Moral** - honesty, integrity, kindness, justice
- **Social** - teamwork, communication, respect, inclusion
- **Spiritual** - religious knowledge, piety, worship
- **Cognitive** - focus, memory, learning, critical thinking

---

## Setup & Migration

### 1. Run Database Migrations

```powershell
# Set your DB URL
$env:DATABASE_URL = "postgresql://postgres:rao14593@localhost:5432/parvarish_db"

# Create game results table
python "migrations/007_add_child_game_results.py"

# Create game questions tables
python "migrations/008_add_game_questions.py"
```

### 2. Seed Game Questions

```powershell
python "scripts/seed_game_questions.py"
```

This populates:
- 9 mood scenarios (3 per age group)
- 9 scenario questions (3 per age group)
- 11 Islamic quiz questions (varying difficulty)

---

## API Endpoints

Base path: `/api/v1/games`

### Authentication & Authorization

- **Child-only endpoints**: Game question fetching and submission
  - Requires child authentication token
  - Child can only submit for their own `child_id`
- **Parent-only endpoints**: Analysis/dashboard
  - Requires parent authentication token
  - Parent can only view their own children's data

---

## 🎮 Game 1: Memory Card Match

**No database questions needed** - logic-based game tracking flips and matches.

### Submit Memory Game Result

**Endpoint:** `POST /games/memory/submit`

**Access:** Child only

**Request Body:**
```json
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
  "result_id": "uuid-here",
  "analysis": {
    "cognitive": 78,
    "focus": 70
  },
  "tasks_generated": 1
}
```

**Behavior Mapping:**
- `focus_score = (correct_matches / total_flips) * 100`
- `memory_score = (correct_matches / (correct + wrong)) * 100`
- Maps to: **cognitive**, **focus**

---

## 🎭 Game 2: Mood Picker

Child reads a scenario and selects their emotional response.

### Get Mood Scenarios

**Endpoint:** `GET /games/mood/questions?age_group=6-8&limit=5`

**Access:** Child only

**Query Parameters:**
- `age_group` (optional): "6-8", "9-11", "12-14"
- `limit` (optional): number of scenarios (default 5)

**Response:**
```json
{
  "scenarios": [
    {
      "id": 1,
      "scenario_en": "Your friend broke your favorite toy by mistake. How do you feel?",
      "scenario_ur": "Aapke dost ne ghalti se aapka pasandeeda khilona tor diya...",
      "category": "emotional",
      "mood_options": ["Anger", "Forgive", "Happy", "Sad"]
    }
  ]
}
```

### Submit Mood Response

**Endpoint:** `POST /games/mood/submit`

**Access:** Child only

**Request Body:**
```json
{
  "child_id": 1,
  "scenario_id": 3,
  "selected_mood": "Forgive"
}
```

**Response:**
```json
{
  "result_id": "uuid-here",
  "analysis": {
    "emotional_control": 80,
    "empathy": 75
  },
  "tasks_generated": 1
}
```

**Behavior Mapping:**
- Each scenario has DB-defined mood weights
- Example: `{"Anger": -5, "Forgive": +5, "Happy": +3, "Sad": 0}`
- Maps to: **emotional_control**, **empathy**

---

## 🎬 Game 3: What Would You Do? (Scenario Game)

Moral and social choice scenarios with weighted options.

### Get Scenario Questions

**Endpoint:** `GET /games/scenario/questions?age_group=9-11&limit=5`

**Access:** Child only

**Query Parameters:**
- `age_group` (optional): "6-8", "9-11", "12-14"
- `limit` (optional): number of questions (default 5)

**Response:**
```json
{
  "questions": [
    {
      "id": 2,
      "question_en": "Your friend pushed you in the playground. What will you do?",
      "question_ur": "Aapke dost ne aapko playground mein dhakka diya...",
      "category": "moral",
      "options": ["Push them back", "Tell a teacher", "Forgive and move on"]
    }
  ]
}
```

### Submit Scenario Choice

**Endpoint:** `POST /games/scenario/submit`

**Access:** Child only

**Request Body:**
```json
{
  "child_id": 1,
  "scenario_id": 2,
  "selected_option": "Forgive and move on"
}
```

**Response:**
```json
{
  "result_id": "uuid-here",
  "analysis": {
    "moral": 75,
    "emotional": 65,
    "social": 70
  },
  "tasks_generated": 1
}
```

**Behavior Mapping:**
- Each option has DB-defined score deltas
- Example:
  ```json
  [
    {"option": "Push them back", "moral": -8, "emotional": -5, "social": -3},
    {"option": "Tell a teacher", "moral": +6, "emotional": +3, "social": +4},
    {"option": "Forgive and move on", "moral": +10, "emotional": +5, "social": +5}
  ]
  ```
- Maps to: **moral**, **emotional**, **social**

---

## 📘 Game 4: Islamic Quiz

Test Islamic knowledge and values.

### Get Quiz Questions

**Endpoint:** `GET /games/islamic-quiz/questions?age_group=12-14&difficulty=2&limit=5`

**Access:** Child only

**Query Parameters:**
- `age_group` (optional): "6-8", "9-11", "12-14"
- `difficulty` (optional): 1 (easy), 2 (medium), 3 (hard)
- `limit` (optional): number of questions (default 5)

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

**Note:** `correct_answer` is NOT returned to prevent cheating.

### Submit Quiz Answer

**Endpoint:** `POST /games/islamic-quiz/submit`

**Access:** Child only

**Request Body:**
```json
{
  "child_id": 1,
  "question_id": 5,
  "selected_answer": "Shahada"
}
```

**Response:**
```json
{
  "result_id": "uuid-here",
  "analysis": {
    "spiritual": 75,
    "cognitive": 65
  },
  "tasks_generated": 1
}
```

**Behavior Mapping:**
- Correct answer: `+5` spiritual, `+5` cognitive
- Wrong answer: `-2` spiritual, `-3` cognitive
- Maps to: **spiritual**, **cognitive**

---

## 📊 Parent Dashboard - Child Analysis

View aggregated game performance and suggested improvements.

### Get Child Analysis

**Endpoint:** `GET /games/{child_id}/analysis`

**Access:** Parent only

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

**Logic:**
- Aggregates last 10 game results
- Averages scores per behavior category
- Identifies strongest and weakest areas
- Suggests task aligned with weakest category

---

## Task Generation Integration

After every game submission, the system:
1. Saves raw result and analysis scores to `child_game_results`
2. Calls `generate_tasks_from_scores(db, child_id, days=3)`
3. Checks recent behavior scores (games + daily questions)
4. Creates tasks for low-scoring categories (< 50%)
5. Avoids duplicate tasks within 7-day window

**Task Mapping:**
- Emotional weakness → "Kindness challenge"
- Moral weakness → "Honesty task"
- Cognitive weakness → "Memory training"
- Spiritual weakness → "Dua/Salah task"
- Social weakness → "Share and help a friend"

---

## Frontend Integration Guide

### Child Login Flow

1. User logs in → backend returns JWT token
2. Decode token or call `/api/v1/auth/me` to get user profile
3. If `role === "child"`, redirect to `/child/games`
4. If `role === "parent"`, redirect to `/parent/dashboard`

### Fetch Questions (Child)

```typescript
async function getMoodScenarios(token: string, ageGroup: string) {
  const res = await fetch(`/api/v1/games/mood/questions?age_group=${ageGroup}&limit=5`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return res.json();
}
```

### Submit Game Result (Child)

```typescript
async function submitMoodGame(token: string, childId: number, scenarioId: number, mood: string) {
  const res = await fetch('/api/v1/games/mood/submit', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ child_id: childId, scenario_id: scenarioId, selected_mood: mood })
  });
  return res.json();
}
```

### View Dashboard (Parent)

```typescript
async function getChildAnalysis(token: string, childId: number) {
  const res = await fetch(`/api/v1/games/${childId}/analysis`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return res.json();
}
```

---

## Example Game Content

### Mood Scenario Example (Age 9-11)
```json
{
  "scenario_en": "Your team lost a match because of one player's mistake. How do you feel?",
  "scenario_ur": "Aapki team ek player ki ghalti ki wajah se haar gayi. Aap kaisa mehsoos karte hain?",
  "category": "emotional",
  "mood_weights": {
    "Anger": -5,
    "Forgive": +5,
    "Happy": 0,
    "Sad": +2
  },
  "tags": ["teamwork", "forgiveness", "anger_control"]
}
```

### Scenario Question Example (Age 12-14)
```json
{
  "question_en": "Your friends are planning to cheat on a test and want you to join. What will you do?",
  "category": "moral",
  "options": [
    {"option": "Join them", "moral": -15, "emotional": -5, "social": -8},
    {"option": "Refuse and study honestly", "moral": +15, "emotional": +8, "social": +5},
    {"option": "Report to the teacher", "moral": +10, "emotional": +3, "social": -3}
  ],
  "tags": ["integrity", "peer_pressure", "honesty"]
}
```

### Islamic Quiz Example (Age 6-8)
```json
{
  "question_en": "How many times do Muslims pray in a day?",
  "question_ur": "Musalman din mein kitni baar namaz parhte hain?",
  "category": "spiritual",
  "options": ["3 times", "5 times", "7 times", "10 times"],
  "correct_answer": "5 times",
  "explanation_en": "Muslims pray 5 times a day: Fajr, Dhuhr, Asr, Maghrib, and Isha.",
  "difficulty": 1,
  "tags": ["salah", "basics"]
}
```

---

## Error Handling

### Common Error Responses

**403 Forbidden - Wrong user type:**
```json
{
  "detail": "Only children can access game questions"
}
```

**403 Forbidden - Child mismatch:**
```json
{
  "detail": "Child can only submit their own results"
}
```

**403 Forbidden - Parent trying to play:**
```json
{
  "detail": "Only child accounts can submit game results"
}
```

**422 Unprocessable Entity - Missing field:**
```json
{
  "detail": "Missing field: scenario_id"
}
```

**404 Not Found - Child doesn't exist:**
```json
{
  "detail": "Child not found"
}
```

---

## Testing the API

### 1. Get a child token
Login as a child user and extract the JWT.

### 2. Fetch questions
```powershell
curl -X GET "http://localhost:8000/api/v1/games/mood/questions?age_group=6-8" `
  -H "Authorization: Bearer <CHILD_TOKEN>"
```

### 3. Submit a game result
```powershell
curl -X POST "http://localhost:8000/api/v1/games/mood/submit" `
  -H "Authorization: Bearer <CHILD_TOKEN>" `
  -H "Content-Type: application/json" `
  -d '{"child_id": 1, "scenario_id": 1, "selected_mood": "Forgive"}'
```

### 4. View analysis (as parent)
```powershell
curl -X GET "http://localhost:8000/api/v1/games/1/analysis" `
  -H "Authorization: Bearer <PARENT_TOKEN>"
```

---

## Adding More Questions

Edit `scripts/seed_game_questions.py` and add entries to:
- `MOOD_SCENARIOS`
- `SCENARIO_QUESTIONS`
- `ISLAMIC_QUIZ_QUESTIONS`

Then re-run:
```powershell
python "scripts/seed_game_questions.py"
```

---

## Summary

✅ **4 interactive games** with DB-backed questions
✅ **Rich Islamic content** aligned with behavior categories
✅ **Age-appropriate** content (6-8, 9-11, 12-14)
✅ **Bilingual** (English + Urdu)
✅ **Child-only access** for playing
✅ **Parent dashboard** for monitoring
✅ **Automatic task generation** based on weak areas
✅ **Secure validation** against DB (no client-side cheating for quiz)

---

## Next Steps

1. Run migrations and seed data
2. Test each endpoint with child/parent tokens
3. Build frontend UI for each game
4. Add confetti/animations for positive reinforcement
5. Expand question bank (target 50+ per game type)
6. Add leaderboards or achievement badges (optional)

For questions or contributions, contact the development team.
