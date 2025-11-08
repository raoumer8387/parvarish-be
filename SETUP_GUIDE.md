# Parvarish AI - Role-Based Authentication Setup Guide

## 🎯 Overview
This guide walks you through setting up the new two-role authentication system:
- **Parents**: Register via Google OAuth, access chatbot
- **Children**: Created by parents with username/password, access games only

---

## 📋 Prerequisites

### 1. Google OAuth Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Navigate to **APIs & Services** → **Credentials**
4. Create **OAuth 2.0 Client ID** (Web application)
5. Add authorized JavaScript origins:
   - `http://localhost:8000`
   - `http://localhost:5500` (or your frontend URL)
6. Copy the **Client ID** (you'll need this for `.env`)

### 2. Environment Configuration
Update your `.env` file with the following new variables:

```env
# Existing variables
DATABASE_URL=postgresql://postgres:rao14593@localhost:5432/parvarish_db
OPENROUTER_API_KEY=your_existing_key

# NEW: JWT Configuration
JWT_SECRET=your-super-secret-random-string-here-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRES_HOURS=24

# NEW: Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id-from-console.apps.googleusercontent.com
```

**Generate a secure JWT_SECRET:**
```bash
# PowerShell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object {[char]$_})
```

---

## 🔧 Installation Steps

### Step 1: Install Dependencies
```bash
# Activate virtual environment
.venv\Scripts\Activate.ps1

# Install new packages
pip install -r requirements.txt
```

**New packages added:**
- `passlib[bcrypt]` - Password hashing
- `python-jose` - JWT token generation
- `google-auth` - Google OAuth verification
- `alembic` - Database migrations

### Step 2: Initialize Alembic
```bash
# Initialize Alembic (if not already done)
alembic init alembic

# Edit alembic.ini - replace this line:
# sqlalchemy.url = driver://user:pass@localhost/dbname
# With:
sqlalchemy.url = postgresql://postgres:rao14593@localhost:5432/parvarish_db

# Or better, use environment variable in alembic/env.py:
```

Update `alembic/env.py`:
```python
from app.utils.config import get_settings
from app.db.base import Base  # Import your declarative base
from app.db.models import *  # Import all models

settings = get_settings()
config.set_main_option('sqlalchemy.url', settings.DATABASE_URL)
target_metadata = Base.metadata
```

### Step 3: Create Database Migration
```bash
# Generate migration from models
alembic revision --autogenerate -m "Add parent-child role system"

# Review the generated migration file in alembic/versions/
# Edit if needed (especially for existing 'users' table)

# Apply migration
alembic upgrade head
```

**Important:** If you have existing data in the `users` table, you may need to manually edit the migration to:
1. Add new columns (`google_uid`, `username`, `user_type`, etc.) as nullable
2. Set default values for `user_type` for existing users
3. Create new tables (parents, children, games, etc.)

### Step 4: Run the Application
```bash
uvicorn main:app --reload
```

Server will start at `http://localhost:8000`

---

## 🧪 Testing the API

### 1. Google OAuth Login (Parent)

**Endpoint:** `POST /api/v1/auth/google-login`

**Request:**
```json
{
  "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjE5MmFkNT..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Get Google ID Token:**
Use the frontend's Google Sign-In button or test with [Google OAuth Playground](https://developers.google.com/oauthplayground/).

### 2. Register Parent Details

**Endpoint:** `POST /api/v1/auth/register-parent`

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN_FROM_STEP_1
```

**Request:**
```json
{
  "name": "Ahmed Khan",
  "phone": "+92-300-1234567",
  "country": "Pakistan",
  "city": "Karachi",
  "father_age": 35,
  "mother_age": 32,
  "married_since": "2015-06-15",
  "is_single_parent": false
}
```

**Response:**
```json
{
  "message": "Parent profile updated successfully",
  "parent_id": 1
}
```

### 3. Add Child Account

**Endpoint:** `POST /api/v1/auth/add-child`

**Headers:**
```
Authorization: Bearer YOUR_PARENT_JWT_TOKEN
```

**Request:**
```json
{
  "username": "sara_khan",
  "password": "securePassword123",
  "name": "Sara Khan",
  "age": 8,
  "gender": "Female",
  "school": "Karachi Grammar School",
  "class_name": "3rd Grade",
  "temperament": "Curious and energetic"
}
```

**Response:**
```json
{
  "message": "Child account created successfully",
  "user_id": 5,
  "child_id": 2,
  "username": "sara_khan"
}
```

### 4. Child Login

**Endpoint:** `POST /api/v1/auth/login-child`

**Request:**
```json
{
  "username": "sara_khan",
  "password": "securePassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

## 🔐 Using JWT Tokens

### Decode Token Payload
Every JWT contains:
```json
{
  "sub": "5",           // User ID
  "user_type": "child", // "parent" or "child"
  "exp": 1705123456     // Expiration timestamp
}
```

### Protected Endpoints
Use the token in the `Authorization` header:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Parent-only endpoints:**
- `POST /api/v1/auth/register-parent`
- `POST /api/v1/auth/add-child`
- `POST /api/chat` (chatbot - after adding role check)

**Child-only endpoints (to be created):**
- `GET /api/games`
- `POST /api/games/{id}/play`

---

## 🗄️ Database Schema

### New Tables Created

#### 1. `users` (Extended)
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    google_uid VARCHAR,      -- For parents (Google OAuth)
    email VARCHAR,           -- For parents
    username VARCHAR,        -- For children
    hashed_password VARCHAR, -- For children
    user_type VARCHAR NOT NULL, -- 'parent' or 'child'
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 2. `parents`
```sql
CREATE TABLE parents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id),
    name VARCHAR,
    phone VARCHAR,
    country VARCHAR,
    city VARCHAR,
    father_age INTEGER,
    mother_age INTEGER,
    married_since DATE,
    is_single_parent BOOLEAN DEFAULT FALSE
);
```

#### 3. `children`
```sql
CREATE TABLE children (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id),
    parent_id INTEGER REFERENCES parents(id),
    name VARCHAR NOT NULL,
    age INTEGER,
    gender VARCHAR,
    school VARCHAR,
    class_name VARCHAR,
    temperament TEXT
);
```

#### 4. `games`
```sql
CREATE TABLE games (
    id SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    description TEXT,
    type VARCHAR, -- 'memory', 'patience', 'moral', 'quiz'
    difficulty_level INTEGER
);
```

#### 5. `child_game_activity`
```sql
CREATE TABLE child_game_activity (
    id SERIAL PRIMARY KEY,
    child_id INTEGER REFERENCES children(id),
    game_id INTEGER REFERENCES games(id),
    score INTEGER,
    time_spent INTEGER, -- seconds
    date_played TIMESTAMP DEFAULT NOW(),
    behavior_tag VARCHAR
);
```

#### 6. `child_behavior_responses`
```sql
CREATE TABLE child_behavior_responses (
    id SERIAL PRIMARY KEY,
    child_id INTEGER REFERENCES children(id),
    question TEXT,
    answer TEXT,
    behavior_category VARCHAR,
    score INTEGER,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

#### 7. `child_behavior_scores`
```sql
CREATE TABLE child_behavior_scores (
    id SERIAL PRIMARY KEY,
    child_id INTEGER UNIQUE REFERENCES children(id),
    overall_score FLOAT,
    emotional_score FLOAT,
    social_score FLOAT,
    discipline_score FLOAT,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### 8. `chat_logs`
```sql
CREATE TABLE chat_logs (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER REFERENCES parents(id),
    message_text TEXT,
    response_text TEXT,
    context TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

---

## 📚 API Reference

### Authentication Endpoints

#### `POST /api/v1/auth/google-login`
**Description:** Parent login/signup via Google OAuth  
**Auth Required:** No  
**Request Body:**
- `id_token` (string, required) - Google ID token from frontend

**Success Response:** `200 OK`
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

---

#### `POST /api/v1/auth/register-parent`
**Description:** Update parent demographic details  
**Auth Required:** Yes (Parent JWT)  
**Request Body:** All fields optional
- `name` (string)
- `phone` (string)
- `country` (string)
- `city` (string)
- `father_age` (integer)
- `mother_age` (integer)
- `married_since` (string, ISO date)
- `is_single_parent` (boolean)

**Success Response:** `200 OK`
```json
{
  "message": "Parent profile updated successfully",
  "parent_id": 1
}
```

---

#### `POST /api/v1/auth/add-child`
**Description:** Parent creates a child account  
**Auth Required:** Yes (Parent JWT)  
**Request Body:**
- `username` (string, required) - Unique username for child
- `password` (string, required) - Plain password (will be hashed)
- `name` (string, optional)
- `age` (integer, optional)
- `gender` (string, optional)
- `school` (string, optional)
- `class_name` (string, optional)
- `temperament` (string, optional)

**Success Response:** `200 OK`
```json
{
  "message": "Child account created successfully",
  "user_id": 5,
  "child_id": 2,
  "username": "sara_khan"
}
```

---

#### `POST /api/v1/auth/login-child`
**Description:** Child login with username/password  
**Auth Required:** No  
**Request Body:**
- `username` (string, required)
- `password` (string, required)

**Success Response:** `200 OK`
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

**Error Response:** `401 Unauthorized`
```json
{
  "detail": "Invalid credentials"
}
```

---

## 🛡️ Security Best Practices

### Password Storage
- Passwords hashed with **bcrypt** (12 rounds)
- Never stored in plain text
- Salted automatically by bcrypt

### JWT Tokens
- Signed with HS256 algorithm
- Expire after 24 hours (configurable via `JWT_EXPIRES_HOURS`)
- Include `user_type` claim for role-based access

### Google OAuth
- ID token verified server-side using Google's public keys
- `aud` claim must match your `GOOGLE_CLIENT_ID`
- Tokens expire after 1 hour (managed by Google)

### CORS Configuration
Current: `allow_origins=["*"]` (development only)  
**Production:** Update `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🐛 Troubleshooting

### Issue: "Invalid Google ID token"
**Causes:**
- Token expired (Google tokens expire after 1 hour)
- Wrong `GOOGLE_CLIENT_ID` in `.env`
- Token from different Google project

**Solution:**
- Get a fresh token from frontend
- Verify `GOOGLE_CLIENT_ID` matches your Google Cloud Console

---

### Issue: "Could not validate credentials"
**Causes:**
- JWT token expired
- Wrong `JWT_SECRET` in `.env`
- Token not sent in `Authorization` header

**Solution:**
- Login again to get new token
- Ensure header format: `Authorization: Bearer YOUR_TOKEN`
- Check `.env` file is loaded correctly

---

### Issue: "Username already exists"
**Cause:** Child username must be unique across all children

**Solution:** Choose a different username

---

### Issue: Alembic migration fails
**Cause:** Existing `users` table conflicts with new schema

**Solution:**
1. Backup your database
2. Manually edit the migration file:
```python
# Add columns as nullable first
op.add_column('users', sa.Column('user_type', sa.String(), nullable=True))
op.add_column('users', sa.Column('google_uid', sa.String(), nullable=True))

# Set default values for existing rows
op.execute("UPDATE users SET user_type = 'parent' WHERE user_type IS NULL")

# Make required columns non-nullable
op.alter_column('users', 'user_type', nullable=False)
```

---

## 🚀 Next Steps

### 1. Add Role-Based Access to Chatbot
Update `app/routes/chatbot.py`:
```python
from app.routes.auth_v2 import require_parent

@router.post("/chat")
async def chat(
    request: ChatRequest,
    parent_user_id: int = Depends(require_parent),
    db: Session = Depends(get_db)
):
    # Store parent_id in chat logs
    # ... existing logic
```

### 2. Create Games Endpoints
Create `app/routes/games.py`:
```python
from fastapi import APIRouter, Depends
from app.routes.auth_v2 import get_current_user

router = APIRouter(prefix="/games", tags=["games"])

@router.get("/")
async def list_games(
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Return available games for children
    pass

@router.post("/{game_id}/play")
async def play_game(
    game_id: int,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Record game activity
    pass
```

### 3. Create Dashboard Endpoints
Create `app/routes/dashboard.py`:
```python
@router.get("/children")
async def list_children(
    parent_user_id: int = Depends(require_parent),
    db: Session = Depends(get_db)
):
    # Return parent's children
    pass

@router.get("/child/{child_id}/stats")
async def child_stats(
    child_id: int,
    parent_user_id: int = Depends(require_parent),
    db: Session = Depends(get_db)
):
    # Return game activity, behavior scores
    pass
```

### 4. Seed Initial Game Data
```python
# scripts/seed_games.py
games = [
    {"title": "Memory Match", "type": "memory", "difficulty": 1},
    {"title": "Patience Puzzle", "type": "patience", "difficulty": 2},
    {"title": "Moral Story Quiz", "type": "quiz", "difficulty": 1},
]
```

---

## 📞 Support
For issues or questions, refer to:
- Main README: `README.md`
- Copilot Instructions: `.github/copilot-instructions.md`
- Database models: `app/db/models/`
- Route implementations: `app/routes/`

---

**Last Updated:** 2025-01-14  
**Version:** 1.0
