# 🎮 Complete Game Session Flow - Visual Guide

```
┌─────────────────────────────────────────────────────────────────────┐
│                         GAME SESSION FLOW                           │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  STEP 1: AUTHENTICATION                                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Child Login → Get JWT Token → Store in localStorage               │
│                                                                      │
│  ✅ Child can: Play games, submit results                          │
│  ❌ Parent can: Only view dashboard                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

           ↓

┌─────────────────────────────────────────────────────────────────────┐
│  STEP 2: SELECT GAME                                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐
│  │   Memory     │  │     Mood     │  │   Scenario   │  │  Islamic │
│  │   Card       │  │   Picker     │  │     Game     │  │   Quiz   │
│  │  Match       │  │              │  │              │  │          │
│  │              │  │              │  │              │  │          │
│  │   🃏 🎴      │  │   😊 😢      │  │   🤔 💭      │  │   📖 ☪  │
│  │              │  │              │  │              │  │          │
│  │  3 minutes   │  │  5 minutes   │  │  5 minutes   │  │ 4 minutes│
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────┘
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

           ↓

┌─────────────────────────────────────────────────────────────────────┐
│  STEP 3: FETCH QUESTIONS                                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  GET /api/v1/games/{game_type}/questions                           │
│    ?age_group=6-8&limit=5                                          │
│                                                                      │
│  Response:                                                          │
│  {                                                                  │
│    "scenarios": [                                                   │
│      {                                                              │
│        "id": 1,                                                     │
│        "scenario_en": "Your friend broke your toy...",             │
│        "mood_options": ["Anger", "Forgive", "Happy", "Sad"]        │
│      },                                                             │
│      ...  (5 total questions)                                       │
│    ]                                                                │
│  }                                                                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

           ↓

┌─────────────────────────────────────────────────────────────────────┐
│  STEP 4: START TIMER                                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────┐                        │
│  │   GAME SCREEN                          │                        │
│  │                                        │                        │
│  │   ⏱️  Timer: 4:35  ⬅ Countdown        │                        │
│  │   📊 Progress: 1 of 5                  │                        │
│  │                                        │                        │
│  │   [Question 1 content here...]         │                        │
│  │                                        │                        │
│  │   [Option A]  [Option B]  [Option C]   │                        │
│  │                                        │                        │
│  └────────────────────────────────────────┘                        │
│                                                                      │
│  Timer Logic:                                                       │
│  • Starts at GAME_TIME_LIMITS[gameType]                            │
│  • Counts down every second                                        │
│  • Shows URGENT state when < 30 seconds                            │
│  • Auto-submits when reaches 0                                     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

           ↓

┌─────────────────────────────────────────────────────────────────────┐
│  STEP 5: ANSWER QUESTIONS (Loop)                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  For each question:                                                 │
│                                                                      │
│  1. Show question content                                           │
│  2. Track start time for this question                             │
│  3. Child selects answer                                            │
│  4. Calculate time_taken for this answer                           │
│  5. Store response locally:                                         │
│     {                                                               │
│       scenario_id: 1,                                               │
│       selected_mood: "Forgive",                                     │
│       time_taken: 45  ⬅ Seconds for this question                 │
│     }                                                               │
│  6. Move to next question (or submit if last)                      │
│                                                                      │
│  Local State:                                                       │
│  ┌────────────────────────────────────┐                            │
│  │ responses = [                      │                            │
│  │   { scenario_id: 1, ... },         │                            │
│  │   { scenario_id: 3, ... },         │                            │
│  │   { scenario_id: 5, ... },         │                            │
│  │   { scenario_id: 2, ... },         │                            │
│  │   { scenario_id: 4, ... }  ⬅ 5th  │                            │
│  │ ]                                  │                            │
│  └────────────────────────────────────┘                            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

           ↓

┌─────────────────────────────────────────────────────────────────────┐
│  STEP 6: SUBMIT COMPLETE SESSION                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  When all questions answered OR timer expires:                     │
│                                                                      │
│  POST /api/v1/games/session/mood/complete                          │
│  {                                                                  │
│    "child_id": 15,                                                 │
│    "total_time_seconds": 245,  ⬅ From game start                  │
│    "responses": [                                                   │
│      { scenario_id: 1, selected_mood: "Forgive", time_taken: 45 }, │
│      { scenario_id: 3, selected_mood: "Happy", time_taken: 50 },   │
│      { scenario_id: 5, selected_mood: "Calm", time_taken: 48 },    │
│      { scenario_id: 2, selected_mood: "Help", time_taken: 52 },    │
│      { scenario_id: 4, selected_mood: "Forgive", time_taken: 50 }  │
│    ]                                                                │
│  }                                                                  │
│                                                                      │
│  Backend Processing:                                                │
│  ✅ Validate all questions answered                                │
│  ✅ Check time limit not exceeded                                  │
│  ✅ Save each response to database                                 │
│  ✅ Calculate final score                                          │
│  ✅ Generate completion message                                    │
│  ✅ Trigger task generation                                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

           ↓

┌─────────────────────────────────────────────────────────────────────┐
│  STEP 7: SCORE CALCULATION                                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Backend calculates score:                                          │
│                                                                      │
│  Mood Picker Example:                                               │
│  ┌─────────────────────────────────────────────┐                   │
│  │ Response 1: "Forgive"  → 20 pts (positive)  │                   │
│  │ Response 2: "Happy"    → 20 pts (positive)  │                   │
│  │ Response 3: "Calm"     → 10 pts (neutral)   │                   │
│  │ Response 4: "Help"     → 20 pts (positive)  │                   │
│  │ Response 5: "Forgive"  → 20 pts (positive)  │                   │
│  │                        ─────────────────     │                   │
│  │ Total:                   90 pts              │                   │
│  │ Max possible:           100 pts              │                   │
│  │ Percentage:              90%                 │                   │
│  └─────────────────────────────────────────────┘                   │
│                                                                      │
│  Completion Message:                                                │
│  90% → "🌟 Outstanding! You showed great wisdom!"                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

           ↓

┌─────────────────────────────────────────────────────────────────────┐
│  STEP 8: SHOW COMPLETION SCREEN                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────┐                    │
│  │                                            │                    │
│  │           🎉 GAME COMPLETE! 🎉            │                    │
│  │                                            │                    │
│  │         ┌─────────────────┐                │                    │
│  │         │                 │                │                    │
│  │         │       90        │                │                    │
│  │         │      ─────      │                │                    │
│  │         │      100        │                │                    │
│  │         │                 │                │                    │
│  │         │      90%        │                │                    │
│  │         │                 │                │                    │
│  │         └─────────────────┘                │                    │
│  │                                            │                    │
│  │   🌟 Outstanding! You showed great wisdom! │                    │
│  │                                            │                    │
│  │   ───────── Stats ─────────                │                    │
│  │   ⏱️  Time: 245s / 300s                    │                    │
│  │   ✅ Questions: 5 / 5                      │                    │
│  │   📋 Tasks Generated: 2                    │                    │
│  │                                            │                    │
│  │   [Back to Dashboard]                      │                    │
│  │                                            │                    │
│  └────────────────────────────────────────────┘                    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

           ↓

┌─────────────────────────────────────────────────────────────────────┐
│  STEP 9: RETURN TO DASHBOARD                                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Child's dashboard now shows:                                       │
│  • Updated game history                                             │
│  • New tasks generated from performance                            │
│  • Overall progress tracking                                        │
│                                                                      │
│  Parent's dashboard now shows:                                      │
│  • Child's game results (via GET /games/{child_id}/analysis)       │
│  • Strengths and improvement areas                                 │
│  • Suggested tasks                                                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Timer State Diagram

```
    START GAME
         │
         ▼
  ┌─────────────┐
  │  timeLeft   │
  │     300     │ ← Initialize with game time limit
  └─────────────┘
         │
         ▼
  ┌─────────────┐
  │  setInterval│
  │  (1 second) │ ← Start countdown
  └─────────────┘
         │
         ▼
    ┌────────┐
    │ > 30s? │ ── YES ──→ Normal display (green)
    └────────┘
         │
        NO
         │
         ▼
    Urgent state (red, pulsing)
         │
         ▼
    ┌────────┐
    │ = 0? │ ── YES ──→ Auto-submit session
    └────────┘
         │
        NO
         │
         ▼
    Continue countdown
```

---

## 📊 Score Range to Message Mapping

```
    100%
      │
      │  🌟 OUTSTANDING!
      │  "You showed great wisdom!"
    80% ├───────────────────────────
      │
      │  👏 WELL DONE!
      │  "You're learning and growing!"
    60% ├───────────────────────────
      │
      │  💪 GOOD EFFORT!
      │  "Keep practicing to improve!"
    40% ├───────────────────────────
      │
      │  📚 DON'T GIVE UP!
      │  "Practice makes perfect!"
     0% └───────────────────────────
```

---

## 🎯 Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. Fetch Questions  ────→  Store in state                         │
│  2. Start Timer      ────→  Countdown interval                     │
│  3. Collect Answers  ────→  Local array: responses[]               │
│  4. Calculate Total Time ──→ Date.now() - startTime                │
│  5. Submit Batch     ────→  POST all responses                     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼ HTTP POST
┌─────────────────────────────────────────────────────────────────────┐
│                     BACKEND API LAYER                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  games.py (routes)                                                  │
│  ├─ Authentication Check  ──→  _assert_child_is_self()             │
│  ├─ Validation           ──→  validate_game_completion()           │
│  ├─ Time Check           ──→  Compare vs GAME_TIME_LIMITS          │
│  └─ Save Results         ──→  Call service layer                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    SERVICE LAYER                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  game_services (mood, scenario, quiz, memory)                      │
│  ├─ Validate question exists                                       │
│  ├─ Create ChildGameResult                                         │
│  ├─ Calculate behavior scores                                      │
│  └─ Save to database                                               │
│                                                                      │
│  game_config.py                                                     │
│  ├─ calculate_game_score()  ──→  Points + bonuses                  │
│  ├─ get_completion_message() ──→  Based on %                       │
│  └─ validate_game_completion() ──→  Check all answered             │
│                                                                      │
│  task_service.py                                                    │
│  └─ generate_tasks_from_scores() ──→  Create tasks                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       DATABASE                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  child_game_results                                                 │
│  ├─ id (UUID)                                                       │
│  ├─ child_id                                                        │
│  ├─ game_type                                                       │
│  ├─ raw_result (JSONB)     ← All response data                     │
│  ├─ analysis_score (JSONB) ← Behavior category scores              │
│  └─ created_at                                                      │
│                                                                      │
│  child_tasks (auto-generated)                                       │
│  ├─ Based on weak categories                                       │
│  └─ Personalized to child's needs                                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼ JSON Response
┌─────────────────────────────────────────────────────────────────────┐
│                    RESPONSE TO FRONTEND                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  {                                                                  │
│    "success": true,                                                 │
│    "score": { total, max, percentage, breakdown },                 │
│    "completion_message": "🌟 Outstanding!",                        │
│    "tasks_generated": 2,                                            │
│    "time_taken": 245,                                               │
│    "time_limit": 300                                                │
│  }                                                                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

**This visual guide shows the complete end-to-end flow!** 🎮✨
