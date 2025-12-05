# 🎮 Frontend Developer Handoff - Games API Update

**Date:** December 4, 2025  
**Backend Developer:** Parvarish Backend Team  
**Frontend Implementation Required:** Yes - Major API Changes

---

## 🚨 BREAKING CHANGES

The games API has been completely redesigned to support:
- ⏱️ **Timer-based gameplay** (countdown for entire session)
- 📝 **Complete session submission** (all questions at once, not one-by-one)
- 🏆 **Automatic scoring** (backend calculates score & completion message)
- 📊 **Enhanced analytics** (time tracking, performance breakdown)

**Old individual submission endpoints still work but are deprecated.**

---

## 📋 TABLE OF CONTENTS

1. [What Changed](#what-changed)
2. [New API Endpoints](#new-api-endpoints)
3. [Implementation Guide](#implementation-guide)
4. [Timer Implementation](#timer-implementation)
5. [Complete Code Examples](#complete-code-examples)
6. [Testing Guide](#testing-guide)
7. [Error Handling](#error-handling)
8. [Migration Checklist](#migration-checklist)

---

## 🔄 WHAT CHANGED

### Before (Old Flow) ❌
```
1. Fetch questions
2. Show question 1
3. Submit answer 1 → Wait for response
4. Show question 2
5. Submit answer 2 → Wait for response
... repeat for each question
```

### After (New Flow) ✅
```
1. Fetch questions
2. Start timer (countdown begins)
3. Show question 1 → Collect answer locally
4. Show question 2 → Collect answer locally
... collect all answers
5. Submit ALL answers in one batch
6. Show completion screen with score
```

### Key Differences

| Feature | Old | New |
|---------|-----|-----|
| **Submission** | One-by-one | All at once |
| **Timer** | None | Required countdown |
| **Score** | Manual calculation | Auto-calculated by backend |
| **Message** | None | Personalized completion message |
| **Time Tracking** | No | Per-question + total |
| **Validation** | Partial OK | All questions required |

---

## 📡 NEW API ENDPOINTS

### Base URL
```
http://localhost:8000/api/v1/games
```

### Authentication
All endpoints require Bearer token:
```javascript
headers: {
  'Authorization': 'Bearer YOUR_JWT_TOKEN'
}
```

### Endpoints Overview

| Game | GET Questions | POST Complete Session |
|------|---------------|----------------------|
| Memory Card | N/A (frontend only) | `POST /session/memory/complete` |
| Mood Picker | `GET /mood/questions` | `POST /session/mood/complete` |
| Scenario Game | `GET /scenario/questions` | `POST /session/scenario/complete` |
| Islamic Quiz | `GET /islamic-quiz/questions` | `POST /session/islamic-quiz/complete` |

---

## 🎮 IMPLEMENTATION GUIDE

### Step 1: Fetch Questions

**Endpoint:** `GET /api/v1/games/{game_type}/questions`

**Example: Mood Picker**
```javascript
const fetchQuestions = async () => {
  const response = await fetch(
    '/api/v1/games/mood/questions?limit=5',
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  
  const data = await response.json();
  // data.scenarios contains 5 mood scenarios
  // Questions are automatically filtered by child's age
  return data.scenarios;
};
```

**Response Format:**
```json
{
  "scenarios": [
    {
      "id": 1,
      "scenario_en": "Your friend broke your favorite toy. What do you feel?",
      "scenario_ur": "آپ کے دوست نے آپ کا پسندیدہ کھلونا توڑ دیا۔ آپ کو کیسا لگتا ہے؟",
      "category": "emotional",
      "mood_options": ["Anger", "Forgive", "Happy", "Sad"]
    }
    // ... 4 more scenarios
  ]
}
```

### Step 2: Initialize Game State

```javascript
const GameSession = ({ childId, token }) => {
  // Questions from API
  const [questions, setQuestions] = useState([]);
  
  // Current question index
  const [currentQuestion, setCurrentQuestion] = useState(0);
  
  // Collected responses (stored locally, submit at end)
  const [responses, setResponses] = useState([]);
  
  // Timer (countdown from game time limit)
  const [timeLeft, setTimeLeft] = useState(300); // 5 minutes for mood game
  
  // Track when game started
  const [startTime] = useState(Date.now());
  
  // Game completion state
  const [isComplete, setIsComplete] = useState(false);
  const [finalResult, setFinalResult] = useState(null);
  
  // ... rest of implementation
};
```

### Step 3: Implement Timer

```javascript
useEffect(() => {
  // Don't run timer if game is complete
  if (isComplete) return;
  
  // Countdown every second
  const timer = setInterval(() => {
    setTimeLeft(prevTime => {
      if (prevTime <= 1) {
        clearInterval(timer);
        handleTimeUp(); // Auto-submit
        return 0;
      }
      return prevTime - 1;
    });
  }, 1000);
  
  // Cleanup on unmount
  return () => clearInterval(timer);
}, [isComplete]);

const handleTimeUp = () => {
  // Time expired - force submit with whatever answers we have
  submitSession();
};
```

### Step 4: Collect Answers

```javascript
const handleAnswer = (selectedOption) => {
  // Calculate time taken for this specific question
  const questionTimeTaken = Math.floor((Date.now() - startTime) / 1000);
  
  // Add response to local array
  const newResponse = {
    scenario_id: questions[currentQuestion].id,
    selected_mood: selectedOption,
    time_taken: questionTimeTaken
  };
  
  const updatedResponses = [...responses, newResponse];
  setResponses(updatedResponses);
  
  // Move to next question or submit if this was the last one
  if (currentQuestion < questions.length - 1) {
    setCurrentQuestion(currentQuestion + 1);
  } else {
    // Last question answered - submit immediately
    submitSession(updatedResponses);
  }
};
```

### Step 5: Submit Complete Session

```javascript
const submitSession = async (finalResponses = responses) => {
  // Calculate total time spent
  const totalTime = Math.floor((Date.now() - startTime) / 1000);
  
  try {
    const response = await fetch('/api/v1/games/session/mood/complete', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        child_id: childId,
        total_time_seconds: totalTime,
        responses: finalResponses
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Submission failed');
    }
    
    const result = await response.json();
    
    // Show completion screen
    setFinalResult(result);
    setIsComplete(true);
    
  } catch (error) {
    console.error('Error submitting game:', error);
    // Handle error (show message to user)
  }
};
```

**Request Payload Example:**
```json
{
  "child_id": 15,
  "total_time_seconds": 245,
  "responses": [
    {
      "scenario_id": 1,
      "selected_mood": "Forgive",
      "time_taken": 45
    },
    {
      "scenario_id": 3,
      "selected_mood": "Happy",
      "time_taken": 50
    },
    {
      "scenario_id": 5,
      "selected_mood": "Calm",
      "time_taken": 48
    },
    {
      "scenario_id": 2,
      "selected_mood": "Help",
      "time_taken": 52
    },
    {
      "scenario_id": 4,
      "selected_mood": "Forgive",
      "time_taken": 50
    }
  ]
}
```

**Response Format:**
```json
{
  "success": true,
  "game_type": "mood",
  "score": {
    "total_score": 90,
    "max_score": 100,
    "percentage": 90.0,
    "breakdown": {
      "questions_answered": 5,
      "total_questions": 5
    }
  },
  "completion_message": "🌟 Outstanding! You showed great wisdom and understanding!",
  "tasks_generated": 2,
  "time_taken": 245,
  "time_limit": 300,
  "results_saved": 5
}
```

### Step 6: Show Completion Screen

```javascript
const CompletionScreen = ({ result }) => {
  const { score, completion_message, tasks_generated, time_taken, time_limit } = result;
  
  return (
    <div className="completion-screen">
      <h1>🎉 Game Complete!</h1>
      
      {/* Score Display */}
      <div className="score-card">
        <div className="score-circle">
          <span className="score-value">{score.total_score}</span>
          <span className="score-divider">/</span>
          <span className="score-max">{score.max_score}</span>
        </div>
        <div className="score-percentage">
          {score.percentage}%
        </div>
      </div>
      
      {/* Completion Message */}
      <div className="completion-message">
        <p>{completion_message}</p>
      </div>
      
      {/* Stats */}
      <div className="game-stats">
        <div className="stat">
          <span className="stat-icon">⏱️</span>
          <span className="stat-label">Time:</span>
          <span className="stat-value">{time_taken}s / {time_limit}s</span>
        </div>
        <div className="stat">
          <span className="stat-icon">✅</span>
          <span className="stat-label">Questions:</span>
          <span className="stat-value">{score.breakdown.questions_answered}</span>
        </div>
        <div className="stat">
          <span className="stat-icon">📋</span>
          <span className="stat-label">Tasks Generated:</span>
          <span className="stat-value">{tasks_generated}</span>
        </div>
      </div>
      
      {/* Action Button */}
      <button 
        className="btn-primary"
        onClick={() => navigate('/dashboard')}
      >
        Back to Dashboard
      </button>
    </div>
  );
};
```

---

## ⏱️ TIMER IMPLEMENTATION

### Time Limits per Game

```javascript
const GAME_TIME_LIMITS = {
  memory: 180,       // 3 minutes
  mood: 300,         // 5 minutes
  scenario: 300,     // 5 minutes
  islamicQuiz: 240   // 4 minutes
};
```

### Timer Component

```javascript
const TimerDisplay = ({ seconds, isUrgent }) => {
  const minutes = Math.floor(seconds / 60);
  const secs = seconds % 60;
  
  return (
    <div className={`timer ${isUrgent ? 'urgent' : ''}`}>
      <span className="timer-icon">⏱️</span>
      <span className="timer-value">
        {minutes}:{secs.toString().padStart(2, '0')}
      </span>
    </div>
  );
};

// Usage in game
<TimerDisplay 
  seconds={timeLeft} 
  isUrgent={timeLeft < 30} 
/>
```

### Timer CSS (Recommended)

```css
.timer {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 24px;
  font-weight: bold;
  color: #2ecc71;
  padding: 12px 24px;
  background: #f8f9fa;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.timer.urgent {
  color: #e74c3c;
  background: #fee;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { 
    opacity: 1;
    transform: scale(1);
  }
  50% { 
    opacity: 0.7;
    transform: scale(1.05);
  }
}
```

---

## 💻 COMPLETE CODE EXAMPLES

### Example 1: Mood Picker Game (Full Component)

```jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const MoodPickerGame = ({ childId, token }) => {
  const navigate = useNavigate();
  
  // State management
  const [questions, setQuestions] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [responses, setResponses] = useState([]);
  const [timeLeft, setTimeLeft] = useState(300);
  const [startTime] = useState(Date.now());
  const [isComplete, setIsComplete] = useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Fetch questions on mount
  useEffect(() => {
    const fetchQuestions = async () => {
      try {
        const response = await fetch(
          '/api/v1/games/mood/questions?age_group=6-8&limit=5',
          {
            headers: { 'Authorization': `Bearer ${token}` }
          }
        );
        
        if (!response.ok) throw new Error('Failed to fetch questions');
        
        const data = await response.json();
        setQuestions(data.scenarios);
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };
    
    fetchQuestions();
  }, [token]);
  
  // Timer countdown
  useEffect(() => {
    if (isComplete || loading) return;
    
    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          handleSubmit();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    
    return () => clearInterval(timer);
  }, [isComplete, loading]);
  
  // Handle answer selection
  const handleAnswer = (mood) => {
    const timeTaken = Math.floor((Date.now() - startTime) / 1000);
    
    const newResponse = {
      scenario_id: questions[currentQuestion].id,
      selected_mood: mood,
      time_taken: timeTaken
    };
    
    const updatedResponses = [...responses, newResponse];
    setResponses(updatedResponses);
    
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      handleSubmit(updatedResponses);
    }
  };
  
  // Submit session
  const handleSubmit = async (finalResponses = responses) => {
    const totalTime = Math.floor((Date.now() - startTime) / 1000);
    
    try {
      const response = await fetch('/api/v1/games/session/mood/complete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          child_id: childId,
          total_time_seconds: totalTime,
          responses: finalResponses
        })
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail);
      }
      
      const data = await response.json();
      setResult(data);
      setIsComplete(true);
    } catch (err) {
      setError(err.message);
    }
  };
  
  // Loading state
  if (loading) {
    return <div className="loading">Loading game...</div>;
  }
  
  // Error state
  if (error) {
    return <div className="error">Error: {error}</div>;
  }
  
  // Completion screen
  if (isComplete && result) {
    return (
      <div className="completion-screen">
        <h1>🎉 Game Complete!</h1>
        <div className="score-display">
          <div className="score">{result.score.percentage}%</div>
          <p>{result.completion_message}</p>
        </div>
        <div className="stats">
          <p>⏱️ Time: {result.time_taken}s / {result.time_limit}s</p>
          <p>✅ Questions: {result.score.breakdown.questions_answered}</p>
          <p>📋 Tasks Generated: {result.tasks_generated}</p>
        </div>
        <button onClick={() => navigate('/dashboard')}>
          Back to Dashboard
        </button>
      </div>
    );
  }
  
  // Game screen
  const currentQ = questions[currentQuestion];
  
  return (
    <div className="game-screen">
      {/* Header */}
      <div className="game-header">
        <div className={`timer ${timeLeft < 30 ? 'urgent' : ''}`}>
          ⏱️ {Math.floor(timeLeft / 60)}:{(timeLeft % 60).toString().padStart(2, '0')}
        </div>
        <div className="progress">
          Question {currentQuestion + 1} of {questions.length}
        </div>
      </div>
      
      {/* Question */}
      <div className="question-card">
        <p className="question-text">{currentQ.scenario_en}</p>
        <p className="question-text-ur">{currentQ.scenario_ur}</p>
      </div>
      
      {/* Options */}
      <div className="options-grid">
        {currentQ.mood_options.map(mood => (
          <button
            key={mood}
            className="option-button"
            onClick={() => handleAnswer(mood)}
          >
            {mood}
          </button>
        ))}
      </div>
    </div>
  );
};

export default MoodPickerGame;
```

### Example 2: All Game Payloads

**Scenario Game:**
```json
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

**Islamic Quiz:**
```json
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

**Memory Game:**
```json
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

## 🧪 TESTING GUIDE

### cURL Test Commands

**Fetch Questions:**
```bash
curl -X GET "http://localhost:8000/api/v1/games/mood/questions?age_group=6-8&limit=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Submit Session:**
```bash
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

## ❌ ERROR HANDLING

### Common Errors

| Status | Error Message | Cause | Solution |
|--------|--------------|-------|----------|
| 422 | Time limit exceeded. Max: 300s | total_time_seconds > limit | User took too long |
| 422 | Expected 5 answers, got 3 | Incomplete responses | Ensure all questions answered |
| 403 | Only children can submit | Parent account trying to play | Login as child |
| 403 | You can only submit for yourself | child_id mismatch | Use correct child_id |
| 401 | Not authenticated | Missing/invalid token | Re-login |

### Error Handling Code

```javascript
const handleError = (error) => {
  if (error.status === 422) {
    if (error.detail.includes('Time limit')) {
      showMessage('⏰ Time ran out! Try to be faster next time.');
    } else if (error.detail.includes('Expected')) {
      showMessage('❌ Please answer all questions before submitting.');
    }
  } else if (error.status === 403) {
    showMessage('🔒 You need to be logged in as a child to play.');
  } else {
    showMessage('❌ Something went wrong. Please try again.');
  }
};
```

---

## ✅ MIGRATION CHECKLIST

### Frontend Tasks
- [ ] **Implement timer**
  - [ ] Add countdown state
  - [ ] Create timer display component
  - [ ] Implement urgent state (< 30s)
  - [ ] Add auto-submit on timer expiry
  
- [ ] **Update question flow**
  - [ ] Collect answers locally (don't submit yet)
  - [ ] Track time per question
  - [ ] Show progress indicator
  
- [ ] **Implement batch submission**
  - [ ] Build complete payload with all responses
  - [ ] Submit to new endpoint
  - [ ] Handle response correctly
  
- [ ] **Create completion screen**
  - [ ] Display score percentage
  - [ ] Show completion message
  - [ ] Display stats (time, questions, tasks)
  - [ ] Add navigation back to dashboard
  
- [ ] **Update all 4 games**
  - [ ] Memory Card Match
  - [ ] Mood Picker
  - [ ] Scenario Game
  - [ ] Islamic Quiz
  
- [ ] **Testing**
  - [ ] Test timer functionality
  - [ ] Test auto-submit
  - [ ] Test completion screen
  - [ ] Test error cases

---

## 📚 ADDITIONAL RESOURCES

### Documentation Files (in backend repo)

1. **GAMES_COMPLETE_FLOW.md** - Complete implementation guide
2. **GAMES_QUICK_REF.md** - Quick API reference
3. **GAMES_FLOW_DIAGRAM.md** - Visual flow diagrams
4. **README_GAMES.md** - Feature overview

### Key Configurations

**Game Time Limits:**
```javascript
{
  memory: 180,       // 3 minutes
  mood: 300,         // 5 minutes
  scenario: 300,     // 5 minutes
  islamicQuiz: 240   // 4 minutes
}
```

**Questions Per Game:**
```javascript
{
  memory: 1,
  mood: 5,
  scenario: 5,
  islamicQuiz: 10
}
```

**Score Ranges:**
- 80-100%: 🌟 "Outstanding!"
- 60-79%: 👏 "Well done!"
- 40-59%: 💪 "Good effort!"
- 0-39%: 📚 "Keep trying!"

---

## 🚀 NEXT STEPS

1. Read this document thoroughly
2. Check GAMES_COMPLETE_FLOW.md for more examples
3. Update one game first (start with Mood Picker)
4. Test thoroughly before moving to next game
5. Apply same pattern to remaining games

**Backend is ready! All endpoints are working. Your job:**
1. Add timer UI
2. Collect responses locally
3. Submit batch at end
4. Show completion screen

---

**Good luck! 🎮✨**
