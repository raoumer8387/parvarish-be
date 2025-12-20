# Parvarish AI – FastAPI Backend

A scalable FastAPI backend for an Islamic parenting chatbot with **role-based authentication** supporting parent and child user roles.

## 🎯 Features
- **Dual Authentication System:**
  - **Parents**: Google OAuth login, access to AI chatbot
  - **Children**: Username/password login, access to educational games
- **FastAPI** with modular architecture
- **PostgreSQL** via SQLAlchemy ORM
- **RAG System**: Sentence transformers + ChromaDB for Quranic/Hadith references + **Islamic Scholar References**
  - **NEW**: 53+ scholarly references from classical Islamic literature (Ihya Ulum ad-Din, Tafsir Ibn Kathir, Adab al-Mufrad, etc.)
  - **Multilingual**: All responses in English + Urdu + Roman Urdu
  - **Proper Citations**: Book titles and author names in all responses
- **JWT Authentication** with role-based access control
- **Database Migrations** with Alembic
- **Clean separation**: routes, db models, services, schemas, utils

## 🚀 Quick Start

### 1. Setup Environment
```powershell
# Clone and navigate to project
cd parvarish-be

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Environment Variables
```powershell
# Copy example environment file
copy .env.example .env

# Edit .env and add your credentials:
# - DATABASE_URL (PostgreSQL connection)
# - OPENROUTER_API_KEY (for LLM)
# - JWT_SECRET (generate random string)
# - GOOGLE_CLIENT_ID (from Google Cloud Console)
```

### 3. Initialize Database
```powershell
# Initialize Alembic (first time only)
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Add role-based auth"

# Apply migration
alembic upgrade head
```

### 4. Run the Server
```powershell
uvicorn main:app --reload
```

Visit:
- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

---

## 📖 Documentation

### Complete Setup Guide
See **[SETUP_GUIDE.md](./SETUP_GUIDE.md)** for:
- Google OAuth setup
- Database schema details
- API endpoint testing
- Security best practices
- Troubleshooting

### Frontend Integration Guides
- **[FRONTEND_CHATBOT_INTEGRATION.md](./FRONTEND_CHATBOT_INTEGRATION.md)** - Complete chatbot UI implementation guide with React/Vanilla JS examples
- **[FRONTEND_QUICK_REF.md](./FRONTEND_QUICK_REF.md)** - Quick reference card for chatbot API
- **[FRONTEND_HANDOFF.md](./FRONTEND_HANDOFF.md)** - Games API integration guide

### API Endpoints

#### Authentication (`/api/v1/auth/`)
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/google-login` | None | Parent login via Google OAuth |
| POST | `/register-parent` | Parent JWT | Update parent demographics |
| POST | `/add-child` | Parent JWT | Create child account |
| POST | `/login-child` | None | Child login with username/password |

#### Chatbot (`/chat`)
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/chat` | Parent JWT | Islamic parenting advice (RAG + child context) with **multilingual responses** (EN/UR/RM) and **scholar citations** |
| GET | `/chat/history` | Parent JWT | Returns JSON array of past messages; filter by `child_id` query param for specific child or omit for general advice |

**NEW: Enhanced RAG System**
- Responses now include references from:
  - Quran & Hadith (existing)
  - Prophet Stories (existing)
  - **Islamic Scholars** (NEW): Imam Al-Ghazali, Ibn Kathir, Imam Bukhari, Abdullah Nasih Ulwan, and more
- All responses in **3 languages**: English, Urdu, Roman Urdu
- Proper citations with book titles and author names

See **[SCHOLAR_INTEGRATION_SUMMARY.md](./SCHOLAR_INTEGRATION_SUMMARY.md)** for details.

---

## 📁 Project Structure
```
parvarish-be/
├── app/
│   ├── db/
│   │   ├── base.py              # SQLAlchemy Base
│   │   ├── session.py           # DB session factory
│   │   ├── models/              # ORM models
│   │   │   ├── enums.py         # UserType, GameType enums
│   │   │   ├── users_ext.py     # Extended User model
│   │   │   ├── parent.py        # Parent demographics
│   │   │   ├── child.py         # Child profiles
│   │   │   ├── game.py          # Game catalog
│   │   │   ├── child_game_activity.py
│   │   │   ├── child_behavior_response.py
│   │   │   ├── child_behavior_score.py
│   │   │   └── chat_log.py      # Parent chatbot history
│   │   └── crud/                # CRUD operations
│   ├── routes/
│   │   ├── auth_v2.py           # New role-based auth endpoints
│   │   ├── chatbot.py           # Chatbot endpoints
│   │   └── auth.py              # Legacy auth (deprecated)
│   ├── services/
│   │   ├── auth_service.py      # Google OAuth, password auth
│   │   └── llm_client.py        # OpenRouter integration
│   ├── schemas/
│   │   ├── auth.py              # Auth request/response models
│   │   ├── chat.py              # Chat request/response models
│   │   └── user.py              # User schemas
│   ├── utils/
│   │   ├── security.py          # JWT & password hashing
│   │   ├── config.py            # Environment settings
│   │   └── logging.py           # Logging configuration
│   ├── nlp/
│   │   ├── intent_detection.py  # Intent classification
│   │   └── reference_fetcher.py # Quranic/Hadith retrieval
│   └── rag/
│       ├── data_loader.py       # Load JSON datasets
│       ├── embedder.py          # Sentence transformers
│       └── retriever.py         # Vector search
├── data/
│   ├── hadith_quranic.json      # Islamic references (Quran & Hadith)
│   ├── prophet_stories.json     # Story corpus
│   └── islamic_refrences.json   # NEW: Scholar references (53+ entries)
├── frontend/                     # Simple HTML frontend
├── main.py                       # FastAPI app entry
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
├── SETUP_GUIDE.md               # Detailed setup instructions
└── README.md                     # This file
```

---

## 🗄️ Database Schema

### Core Tables
- **users**: Base authentication (Google UID or username/password)
- **parents**: Demographics (age, location, marital status)
- **children**: Profiles (age, school, temperament)
- **games**: Educational game catalog
- **child_game_activity**: Game session tracking
- **child_behavior_responses**: Behavior assessment Q&A
- **child_behavior_scores**: Aggregated behavior metrics
- **chat_logs**: Parent-chatbot conversation history

See [SETUP_GUIDE.md](./SETUP_GUIDE.md#-database-schema) for SQL schemas.

---

## 🔐 Authentication Flow

### Parent Flow
1. Frontend sends Google ID token to `POST /api/v1/auth/google-login`
2. Backend verifies token with Google
3. Backend creates/fetches User + Parent records
4. Backend returns JWT with `user_type: "parent"`
5. Parent uses JWT to access chatbot and manage children

### Child Flow
1. Parent creates child via `POST /api/v1/auth/add-child`
2. Child logs in via `POST /api/v1/auth/login-child` with username/password
3. Backend returns JWT with `user_type: "child"`
4. Child uses JWT to access games (chatbot blocked)

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|-----------|
| Framework | FastAPI 0.1.0 |
| Database | PostgreSQL + SQLAlchemy |
| Auth | JWT (python-jose), Google OAuth (google-auth) |
| Password | bcrypt (passlib) |
| LLM | OpenRouter API (Gemini 2.5 Flash) |
| Embeddings | sentence-transformers |
| Vector DB | ChromaDB |
| Migrations | Alembic |

---

## 🧪 Testing Examples

### Using cURL (PowerShell)
```powershell
# Parent login
$token = Invoke-RestMethod -Uri http://localhost:8000/api/v1/auth/google-login `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"id_token":"YOUR_GOOGLE_TOKEN"}'

# Add child
Invoke-RestMethod -Uri http://localhost:8000/api/v1/auth/add-child `
  -Method POST `
  -Headers @{Authorization="Bearer $($token.access_token)"} `
  -ContentType "application/json" `
  -Body '{"username":"sara","password":"pass123","name":"Sara Khan","age":8}'

# Child login
$childToken = Invoke-RestMethod -Uri http://localhost:8000/api/v1/auth/login-child `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"username":"sara","password":"pass123"}'
```

### Using Swagger UI
Visit `http://localhost:8000/docs` and use the interactive API docs.

---

## 📦 Dependencies

### Core
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `sqlalchemy` - ORM
- `psycopg2-binary` - PostgreSQL driver
- `pydantic-settings` - Config management

### Authentication
- `passlib[bcrypt]` - Password hashing
- `python-jose` - JWT tokens
- `google-auth` - Google OAuth verification

### AI/ML
- `openai` - OpenRouter client
- `sentence-transformers` - Text embeddings
- `chromadb` - Vector database

### Utilities
- `alembic` - Database migrations
- `python-dotenv` - Environment variables

---

## 🔧 Development

### Run Migrations
```powershell
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1
```

### Check Errors
Visit `http://localhost:8000/docs` to see validation errors in Swagger UI.

### Debug Mode
Set in `.env`:
```
LOG_LEVEL=DEBUG
APP_ENV=development
```

---

## 🚧 Roadmap

### Completed ✅
- Dual-role authentication (Parent/Child)
- Google OAuth integration
- JWT-based authorization
- Database models for all entities
- Auth endpoints
- **Islamic Scholar References Integration** (Dec 2025)
  - 53+ scholarly references from classical Islamic books
  - Multilingual support (English + Urdu + Roman Urdu)
  - Enhanced citation system with book/author attribution

### In Progress 🚧
- Role-based access control on chatbot endpoint
- Dashboard endpoints (parent view children stats)
- Games endpoints (child play games)

### Planned 📋
- Email notifications for parents
- Behavior tracking analytics
- Game recommendation engine
- Enhanced multilingual UI support

---

## 📞 Support

- **Setup Issues**: See [SETUP_GUIDE.md](./SETUP_GUIDE.md#-troubleshooting)
- **API Reference**: Visit `/docs` endpoint
- **Code Guidelines**: See `.github/copilot-instructions.md`

---

## 📄 License
This project is for educational purposes.

---

**Last Updated:** 2025-01-14  
**Version:** 2.0 (Role-based auth system)
