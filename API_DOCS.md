# Parvarish AI - Complete API Documentation

## Overview

Parvarish AI is a comprehensive child development platform that combines behavior tracking, educational games, task management, and AI-powered chatbot interactions. This document covers all API endpoints and integration guidelines.

## Authentication

All API endpoints require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Base URL

```
http://localhost:8000/api/v1
```

## Core Features

### 1. Child Progress Dashboard

Track comprehensive progress across all child activities including behavior, games, and tasks.

#### Individual Child Dashboard
**GET** `/child-progress/{child_id}/dashboard`

Parameters:
- `child_id` (path): Child ID
- `days` (query, optional): Analysis period in days (default: 30)

Response includes:
- Child basic information
- Behavior tracking summary with check-in status
- Game performance metrics and trends
- Task completion analysis
- Progress insights and recommendations
- Recent activity timeline

#### All Children Overview
**GET** `/child-progress/overview`

Parameters:
- `days` (query, optional): Analysis period in days (default: 7)

Returns summary for all children including engagement scores and attention alerts.

### 2. Behavior Tracking

Monitor daily behavior through personalized questions and responses.

#### Get Personalized Questions
**GET** `/behavior/questions/personalized`

Parameters:
- `total_questions` (query): Number of questions (default: 5)

#### Submit Behavior Responses
**POST** `/behavior/submit-responses`

Submit parent's answers about child behavior with automatic scoring.

#### Get Child Statistics
**GET** `/behavior/stats/{child_id}`

Parameters:
- `days` (query, optional): Analysis period

### 3. Educational Games

Four game types: Memory, Mood Picker, Scenario, and Islamic Quiz.

#### Complete Game Sessions
**POST** `/games/session/{game_type}/complete`

Game types: `memory`, `mood`, `scenario`, `islamic-quiz`

Each game tracks performance and generates improvement tasks automatically.

#### Get Game Questions
**GET** `/games/{game_type}/questions`

Age-appropriate questions filtered by child's profile.

#### Game Analysis
**GET** `/games/{child_id}/analysis`

Aggregate performance analysis with strengths and improvement areas.

### 4. Task Management

AI-generated tasks based on behavior patterns and game performance.

#### Generate Tasks from Chat
**POST** `/tasks/from-chat`

Create tasks based on chatbot interactions and recent behavior.

#### Generate Tasks from Scores
**POST** `/tasks/from-scores`

Generate tasks purely from low-performing behavior categories.

#### Get Child Tasks
**GET** `/tasks/child/{child_id}`

List recent tasks with filtering options.

#### Complete Task
**POST** `/tasks/{task_id}/complete`

Mark tasks as completed with timestamp tracking.

### 5. AI Chatbot

Multilingual chatbot with child-aware responses and Islamic guidance.

#### Chat Endpoint
**POST** `/chatbot/chat`

Supports English, Urdu, and Roman Urdu with automatic language detection.

#### Voice Chat Endpoint
**POST** `/chatbot/chat/voice`

Send `multipart/form-data` with an `audio` file and optional `child_id` to let the chatbot answer spoken questions. The response includes the generated reply and the recognized transcription.

#### Chat History
**GET** `/chatbot/history/{child_id}`

Retrieve conversation history for context.

### 6. User Management

#### Parent Registration
**POST** `/auth/register`

Create parent accounts with profile setup.

#### Child Management
**GET** `/parent/children`

List all children for authenticated parent.

**POST** `/settings/children`

Add new child profiles.

## Response Formats

### Success Response
```json
{
  "status": "success",
  "data": {...},
  "message": "Operation completed"
}
```

### Error Response
```json
{
  "detail": "Error description",
  "status_code": 400
}
```

## Integration Examples

### Frontend Dashboard Integration

```javascript
// Get child progress
const getChildProgress = async (childId, days = 30) => {
  const response = await fetch(`/api/v1/child-progress/${childId}/dashboard?days=${days}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return response.json();
};

// Display engagement score
const dashboard = await getChildProgress(1);
console.log(`Engagement: ${dashboard.progress_insights.overall_engagement_score}%`);

// Check for alerts
dashboard.progress_insights.insights.forEach(insight => {
  if (insight.type === 'attention') {
    showAlert(insight.message);
  }
});
```

### Game Integration

```javascript
// Complete memory game
const completeMemoryGame = async (childId, gameData) => {
  const response = await fetch('/api/v1/games/session/memory/complete', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      child_id: childId,
      total_flips: gameData.flips,
      correct_matches: gameData.matches,
      wrong_matches: gameData.errors,
      time_taken_seconds: gameData.time
    })
  });
  return response.json();
};
```

### Behavior Tracking

```javascript
// Submit daily check-in
const submitBehaviorResponses = async (childId, responses) => {
  const response = await fetch('/api/v1/behavior/submit-responses', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      child_id: childId,
      responses: responses
    })
  });
  return response.json();
};
```

## Key Features

### Multilingual Support
- English, Urdu, and Roman Urdu
- Automatic language detection
- Culturally appropriate responses

### Islamic Integration
- Islamic values in game content
- Halal-compliant recommendations
- Prayer time awareness
- Islamic quiz games

### Age-Appropriate Content
- Content filtered by child's age (6-8, 9-11, 12-14)
- Difficulty scaling
- Developmental stage awareness

### Progress Tracking
- Comprehensive analytics across all activities
- Trend analysis and improvement tracking
- Personalized recommendations
- Parent insights and alerts

### Smart Task Generation
- AI-powered task creation based on performance
- Category-specific improvements
- Difficulty adjustment
- Progress-based recommendations

## Error Handling

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `401`: Unauthorized (invalid/missing token)
- `403`: Forbidden (insufficient permissions)
- `404`: Not Found (resource doesn't exist)
- `422`: Validation Error (invalid data format)
- `500`: Internal Server Error

## Rate Limiting

API requests are limited to prevent abuse:
- 100 requests per minute per user
- 1000 requests per hour per user

## Development Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Set environment variables in `.env`
3. Run migrations: `python create_tables.py`
4. Start server: `uvicorn main:app --reload`
5. Access docs: `http://localhost:8000/docs`

## Testing

Use the interactive API documentation at `/docs` for testing endpoints, or test with curl:

```bash
# Get child progress
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/child-progress/1/dashboard?days=30"

# Submit game result
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"child_id":1,"total_flips":20,"correct_matches":10,"wrong_matches":0,"time_taken_seconds":120}' \
  "http://localhost:8000/api/v1/games/session/memory/complete"
```

## Support

For technical issues or questions about the API, refer to the interactive documentation at `/docs` or check the application logs for detailed error information.