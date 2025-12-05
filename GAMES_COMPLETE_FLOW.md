# 🎮 Complete Game Flow - Frontend Integration Guide

## 🎯 Game Session Architecture

All games now follow a **complete session model** with:
- ⏱️ **Timer** - Countdown for entire game session
- 📝 **All questions must be answered** - No partial submissions
- 🏆 **Final score & completion message** - Shown at end
- 📊 **Detailed breakdown** - Performance analysis

---

## ⏱️ Time Limits

```javascript
const GAME_TIME_LIMITS = {
  memory: 180,       // 3 minutes
  mood: 300,         // 5 minutes (60s per question x 5)
  scenario: 300,     // 5 minutes (60s per question x 5)
  islamicQuiz: 240,  // 4 minutes (24s per question x 10)
};

const QUESTIONS_PER_GAME = {
  memory: 1,         // Single session
  mood: 5,           // 5 mood scenarios
  scenario: 5,       // 5 scenario questions
  islamicQuiz: 10,   // 10 quiz questions
};
```

---

## 🎮 Complete Game Flow (All Games)

### Step 1: Fetch Questions
```javascript
// Example: Mood Picker
const response = await fetch(
  `/api/v1/games/mood/questions?age_group=6-8&limit=5`,
  {
    headers: { Authorization: `Bearer ${token}` }
  }
);
const { scenarios } = await response.json();
```

### Step 2: Display Game with Timer
```jsx
const GameSession = () => {
  const [timeLeft, setTimeLeft] = useState(GAME_TIME_LIMITS.mood);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [responses, setResponses] = useState([]);
  const [startTime] = useState(Date.now());

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          handleTimeUp();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const handleAnswer = (answer) => {
    const timeTaken = Math.floor((Date.now() - startTime) / 1000);
    
    setResponses([...responses, {
      scenario_id: questions[currentQuestion].id,
      selected_mood: answer,
      time_taken: timeTaken
    }]);

    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      submitSession();
    }
  };

  return (
    <div>
      {/* Timer Display */}
      <div className="timer">
        ⏱️ {Math.floor(timeLeft / 60)}:{(timeLeft % 60).toString().padStart(2, '0')}
      </div>

      {/* Progress */}
      <div className="progress">
        Question {currentQuestion + 1} of {questions.length}
      </div>

      {/* Question */}
      <div className="question">
        {questions[currentQuestion].scenario_en}
      </div>

      {/* Options */}
      <div className="options">
        {questions[currentQuestion].mood_options.map(mood => (
          <button key={mood} onClick={() => handleAnswer(mood)}>
            {mood}
          </button>
        ))}
      </div>
    </div>
  );
};
```

### Step 3: Submit Complete Session
```javascript
const submitSession = async () => {
  const totalTime = Math.floor((Date.now() - startTime) / 1000);

  const response = await fetch('/api/v1/games/session/mood/complete', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({
      child_id: childId,
      total_time_seconds: totalTime,
      responses: responses // All answers collected
    })
  });

  const result = await response.json();
  showCompletionScreen(result);
};
```

### Step 4: Show Completion Screen
```jsx
const CompletionScreen = ({ result }) => {
  const { score, completion_message, tasks_generated, time_taken } = result;

  return (
    <div className="completion">
      <h1>🎉 Game Complete!</h1>
      
      <div className="score-card">
        <h2>Your Score</h2>
        <div className="score-circle">
          {score.total_score}/{score.max_score}
        </div>
        <div className="percentage">
          {score.percentage}%
        </div>
      </div>

      <div className="message">
        {completion_message}
      </div>

      <div className="stats">
        <div>⏱️ Time: {time_taken}s / {result.time_limit}s</div>
        <div>✅ Questions: {score.breakdown.questions_answered}</div>
        <div>📋 Tasks Generated: {tasks_generated}</div>
      </div>

      <button onClick={() => navigate('/dashboard')}>
        Back to Dashboard
      </button>
    </div>
  );
};
```

---

## 📱 Complete API Reference

### 1. Mood Picker Game

**GET Questions:**
```http
GET /api/v1/games/mood/questions?age_group=6-8&limit=5
Authorization: Bearer {token}
```

**Response:**
```json
{
  "scenarios": [
    {
      "id": 1,
      "scenario_en": "Your friend broke your toy...",
      "scenario_ur": "آپ کے دوست نے...",
      "category": "emotional",
      "mood_options": ["Anger", "Forgive", "Happy", "Sad"]
    }
  ]
}
```

**POST Complete Session:**
```http
POST /api/v1/games/session/mood/complete
Content-Type: application/json
Authorization: Bearer {token}

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
      "time_taken": 52
    }
    // ... all 5 responses
  ]
}
```

**Response:**
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

### 2. What Would You Do? (Scenario Game)

**GET Questions:**
```http
GET /api/v1/games/scenario/questions?age_group=9-11&limit=5
```

**POST Complete Session:**
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
    // ... all 5 responses
  ]
}
```

---

### 3. Islamic Quiz

**GET Questions:**
```http
GET /api/v1/games/islamic-quiz/questions?age_group=12-14&difficulty=2&limit=10
```

**Response:**
```json
{
  "questions": [
    {
      "id": 2,
      "question_en": "How many pillars of Islam are there?",
      "question_ur": "اسلام کے کتنے ستون ہیں؟",
      "category": "spiritual",
      "options": ["3", "4", "5", "6"],
      "difficulty": 1
    }
  ]
}
```

**POST Complete Session:**
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
    // ... all 10 responses
  ]
}
```

**Response:**
```json
{
  "success": true,
  "game_type": "islamic_quiz",
  "score": {
    "total_score": 92,
    "max_score": 120,
    "percentage": 76.7,
    "breakdown": {
      "correct_answers": 8,
      "total_questions": 10,
      "time_bonus": 12
    }
  },
  "completion_message": "👏 Well done! You're learning!",
  "correct_answers": 8
}
```

---

### 4. Memory Card Match

**POST Complete Session:**
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

**Response:**
```json
{
  "success": true,
  "game_type": "memory",
  "score": {
    "total_score": 115,
    "max_score": 130,
    "percentage": 88.5,
    "breakdown": {
      "base_score": 100,
      "time_bonus": 25,
      "flip_penalty": -10
    }
  },
  "completion_message": "🌟 Outstanding! Amazing memory!",
  "time_taken": 95,
  "time_limit": 180
}
```

---

## 🎨 UI/UX Recommendations

### Timer Display
```jsx
const TimerDisplay = ({ seconds }) => {
  const isUrgent = seconds < 30;
  const minutes = Math.floor(seconds / 60);
  const secs = seconds % 60;

  return (
    <div className={`timer ${isUrgent ? 'urgent' : ''}`}>
      <span className="icon">⏱️</span>
      <span className="time">
        {minutes}:{secs.toString().padStart(2, '0')}
      </span>
    </div>
  );
};

// CSS
.timer.urgent {
  color: #ff4444;
  animation: pulse 1s infinite;
}
```

### Progress Bar
```jsx
const ProgressBar = ({ current, total }) => (
  <div className="progress-container">
    <div className="progress-bar" style={{ width: `${(current / total) * 100}%` }} />
    <span className="progress-text">{current} / {total}</span>
  </div>
);
```

### Score Animation
```jsx
const ScoreReveal = ({ score }) => {
  const [revealed, setRevealed] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setRevealed(prev => {
        if (prev >= score) {
          clearInterval(interval);
          return score;
        }
        return prev + 1;
      });
    }, 20);

    return () => clearInterval(interval);
  }, [score]);

  return (
    <div className="score-reveal">
      {revealed}%
    </div>
  );
};
```

### Completion Messages by Score
```javascript
const getCompletionIcon = (percentage) => {
  if (percentage >= 80) return '🌟';
  if (percentage >= 60) return '👏';
  if (percentage >= 40) return '💪';
  return '📚';
};
```

---

## 🚨 Error Handling

```javascript
const handleSubmitError = (error) => {
  if (error.status === 422) {
    // Validation error
    if (error.detail.includes('Time limit exceeded')) {
      showMessage('⏰ Time ran out! Try to be faster next time.');
    } else if (error.detail.includes('Expected')) {
      showMessage('❌ Please answer all questions before submitting.');
    }
  } else if (error.status === 403) {
    // Auth error
    showMessage('🔒 You need to login as a child to play games.');
  }
};
```

---

## 📊 Analytics Tracking

```javascript
// Track game performance
const trackGameCompletion = (result) => {
  analytics.track('game_completed', {
    game_type: result.game_type,
    score_percentage: result.score.percentage,
    time_taken: result.time_taken,
    tasks_generated: result.tasks_generated,
    completion_time: new Date().toISOString()
  });
};
```

---

## ✅ Testing Checklist

- [ ] Timer starts when game begins
- [ ] Timer shows urgent state at < 30 seconds
- [ ] Auto-submit when timer reaches 0
- [ ] All questions must be answered
- [ ] No partial submissions accepted
- [ ] Score calculated correctly
- [ ] Completion message matches score range
- [ ] Tasks generated after submission
- [ ] Can't submit after time expires
- [ ] Progress bar updates correctly
- [ ] Responsive on mobile devices

---

## 🎯 Quick Start Example (React)

```jsx
import React, { useState, useEffect } from 'react';

const MoodGame = ({ token, childId }) => {
  const [questions, setQuestions] = useState([]);
  const [currentQ, setCurrentQ] = useState(0);
  const [responses, setResponses] = useState([]);
  const [timeLeft, setTimeLeft] = useState(300);
  const [gameOver, setGameOver] = useState(false);
  const [result, setResult] = useState(null);

  // Fetch questions
  useEffect(() => {
    fetch('/api/v1/games/mood/questions?age_group=6-8&limit=5', {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => setQuestions(data.scenarios));
  }, []);

  // Timer
  useEffect(() => {
    if (timeLeft <= 0) {
      handleSubmit();
      return;
    }
    const timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000);
    return () => clearTimeout(timer);
  }, [timeLeft]);

  const handleAnswer = (mood) => {
    const newResponses = [...responses, {
      scenario_id: questions[currentQ].id,
      selected_mood: mood,
      time_taken: 300 - timeLeft
    }];
    setResponses(newResponses);

    if (currentQ < questions.length - 1) {
      setCurrentQ(currentQ + 1);
    } else {
      handleSubmit(newResponses);
    }
  };

  const handleSubmit = async (finalResponses = responses) => {
    const res = await fetch('/api/v1/games/session/mood/complete', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({
        child_id: childId,
        total_time_seconds: 300 - timeLeft,
        responses: finalResponses
      })
    });
    const data = await res.json();
    setResult(data);
    setGameOver(true);
  };

  if (gameOver) {
    return (
      <div className="completion">
        <h1>{result.completion_message}</h1>
        <div className="score">{result.score.percentage}%</div>
      </div>
    );
  }

  return (
    <div className="game">
      <div className="timer">⏱️ {Math.floor(timeLeft/60)}:{timeLeft%60}</div>
      <div className="progress">{currentQ + 1} / {questions.length}</div>
      {questions[currentQ] && (
        <>
          <p>{questions[currentQ].scenario_en}</p>
          {questions[currentQ].mood_options.map(mood => (
            <button key={mood} onClick={() => handleAnswer(mood)}>
              {mood}
            </button>
          ))}
        </>
      )}
    </div>
  );
};
```

---

## 🎉 Success!

Your games now have:
✅ Complete timer implementation
✅ All questions must be answered
✅ Final score calculation
✅ Completion messages
✅ Task generation
✅ Professional UX flow
