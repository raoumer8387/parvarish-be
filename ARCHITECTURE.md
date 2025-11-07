# System Architecture - Role-Based Authentication

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│  • HTML/JS Frontend (frontend/)                                  │
│  • Google Sign-In Button (Parent)                               │
│  • Username/Password Form (Child)                                │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ HTTP Requests (JSON)
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI APPLICATION                         │
│                         (main.py)                                │
├─────────────────────────────────────────────────────────────────┤
│  CORS Middleware                                                 │
│  Static File Serving                                             │
│  Health Check: /health                                           │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                       API ROUTES LAYER                           │
│                      (app/routes/)                               │
├──────────────────────────┬──────────────────────────────────────┤
│  AUTH ROUTES            │  CHATBOT ROUTES                       │
│  (auth_v2.py)           │  (chatbot.py)                          │
│                         │                                        │
│  POST /auth/google-login│  POST /api/chat                        │
│  POST /auth/register-..│  • Requires Parent JWT (TODO)          │
│  POST /auth/add-child   │  • RAG-powered responses               │
│  POST /auth/login-child │  • Islamic parenting advice            │
└────────────┬─────────────┴──────────────────┬───────────────────┘
             │                                │
             ▼                                ▼
┌────────────────────────────────┐  ┌─────────────────────────────┐
│     AUTH SERVICE LAYER         │  │    NLP/RAG LAYER            │
│  (app/services/)               │  │  (app/nlp/, app/rag/)       │
├────────────────────────────────┤  ├─────────────────────────────┤
│  auth_service.py:              │  │  • Intent Detection         │
│  • verify_google_id_token()    │  │  • Reference Fetcher        │
│  • login_or_create_parent()    │  │  • Embedder (transformers)  │
│  • register_parent_details()   │  │  • Retriever (ChromaDB)     │
│  • add_child()                 │  │  • LLM Client (OpenRouter)  │
│  • login_child()               │  │                             │
└────────────┬───────────────────┘  └──────────────┬──────────────┘
             │                                     │
             ▼                                     ▼
┌────────────────────────────────┐  ┌─────────────────────────────┐
│      SECURITY UTILITIES        │  │   EXTERNAL APIS             │
│  (app/utils/security.py)       │  │                             │
├────────────────────────────────┤  ├─────────────────────────────┤
│  • hash_password() [bcrypt]    │  │  • Google OAuth API         │
│  • verify_password()           │  │  • OpenRouter API           │
│  • create_access_token() [JWT] │  │  • Sentence Transformers    │
│  • decode_token()              │  │                             │
└────────────┬───────────────────┘  └─────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATABASE LAYER                              │
│                 (PostgreSQL + SQLAlchemy)                        │
├─────────────────────────────────────────────────────────────────┤
│  CORE TABLES:                                                    │
│  • users (google_uid, username, hashed_password, user_type)      │
│  • parents (name, phone, demographics)                           │
│  • children (name, age, school, temperament)                     │
│                                                                  │
│  ACTIVITY TABLES:                                                │
│  • games (catalog)                                               │
│  • child_game_activity (session tracking)                        │
│  • child_behavior_responses (Q&A)                                │
│  • child_behavior_scores (metrics)                               │
│  • chat_logs (parent chatbot history)                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔐 Authentication Flow Diagrams

### Parent Authentication (Google OAuth)

```
┌──────────┐                                   ┌──────────┐
│ Frontend │                                   │  Google  │
│  (HTML)  │                                   │   OAuth  │
└────┬─────┘                                   └────┬─────┘
     │                                              │
     │ 1. User clicks "Sign in with Google"        │
     ├─────────────────────────────────────────────▶
     │                                              │
     │ 2. Google returns ID token                  │
     ◀─────────────────────────────────────────────┤
     │                                              │
     │                                         ┌────┴─────┐
     │ 3. POST /auth/google-login             │ Backend  │
     │    {id_token: "..."}                   │ FastAPI  │
     ├────────────────────────────────────────▶          │
     │                                         │          │
     │                                         │ 4. Verify token with Google
     │                                         │    verify_google_id_token()
     │                                         │          │
     │                                         │ 5. Extract email, name
     │                                         │          │
     │                                         │ 6. Query DB for User
     │                                         │    by google_uid
     │                                         │          │
     │                                         │ 7. If not exists:
     │                                         │    Create User + Parent
     │                                         │          │
     │                                         │ 8. Generate JWT
     │                                         │    create_access_token()
     │                                         │    payload: {
     │                                         │      sub: user_id,
     │                                         │      user_type: "parent"
     │                                         │    }
     │                                         │          │
     │ 9. Return JWT                           │          │
     ◀────────────────────────────────────────┤          │
     │    {access_token: "...", type: "bearer"}         │
     │                                         └──────────┘
     │
     │ 10. Store JWT in localStorage
     │
     │ 11. Include in future requests:
     │     Authorization: Bearer <JWT>
     │
```

---

### Child Authentication (Username/Password)

```
┌──────────┐                                   ┌──────────┐
│ Frontend │                                   │ Backend  │
│  (HTML)  │                                   │ FastAPI  │
└────┬─────┘                                   └────┬─────┘
     │                                              │
     │ 1. Parent creates child account              │
     │    POST /auth/add-child                      │
     │    {username: "sara", password: "..."}       │
     ├─────────────────────────────────────────────▶
     │                                              │
     │                                         2. Verify parent JWT
     │                                            require_parent()
     │                                              │
     │                                         3. Hash password
     │                                            hash_password()
     │                                              │
     │                                         4. Create User
     │                                            user_type="child"
     │                                              │
     │                                         5. Create Child
     │                                            linked to parent
     │                                              │
     │ 6. Return success                            │
     ◀─────────────────────────────────────────────┤
     │                                              │
     │ ─────────────────────────────────────────────
     │                                              │
     │ 7. Child logs in                             │
     │    POST /auth/login-child                    │
     │    {username: "sara", password: "..."}       │
     ├─────────────────────────────────────────────▶
     │                                              │
     │                                         8. Query User by username
     │                                              │
     │                                         9. Verify password
     │                                            verify_password()
     │                                              │
     │                                         10. Generate JWT
     │                                             payload: {
     │                                               sub: user_id,
     │                                               user_type: "child"
     │                                             }
     │                                              │
     │ 11. Return JWT                               │
     ◀─────────────────────────────────────────────┤
     │    {access_token: "...", type: "bearer"}    │
     │                                              │
     │ 12. Store JWT in child's session             │
     │                                              │
```

---

## 🗄️ Database Schema Diagram

```
┌─────────────────────────┐
│        users            │
├─────────────────────────┤
│ id (PK)                 │◀──────────┐
│ google_uid (unique)     │           │
│ email                   │           │
│ username (unique)       │           │
│ hashed_password         │           │
│ user_type (enum)        │           │
│ created_at              │           │
└────────┬────────────────┘           │
         │                            │
         │                            │
    ┌────┴────┐                      │
    │         │                      │
    ▼         ▼                      │
┌────────┐  ┌──────────┐             │
│parents │  │ children │             │
├────────┤  ├──────────┤             │
│ id (PK)│  │ id (PK)  │             │
│ user_id├──┘ user_id  ├─────────────┘
│  (FK)  │    (FK)     │
│ name   │  ┌─parent_id│
│ phone  │  │  (FK)    │
│ country│  │ name     │
│ city   │  │ age      │
│ ...    │  │ gender   │
└────┬───┘  │ school   │
     │      │ ...      │
     │      └────┬─────┘
     │           │
     │           │
     │      ┌────┴─────────────┬──────────────────┬─────────────────┐
     │      │                  │                  │                 │
     │      ▼                  ▼                  ▼                 ▼
     │  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐
     │  │child_game_  │  │child_behavior│  │child_behavior│  │   games     │
     │  │  activity   │  │  _responses  │  │   _scores    │  │             │
     │  ├─────────────┤  ├──────────────┤  ├──────────────┤  ├─────────────┤
     │  │ child_id(FK)│  │ child_id(FK) │  │ child_id(FK) │  │ id (PK)     │
     │  │ game_id(FK) │  │ question     │  │ overall_score│  │ title       │
     │  │ score       │  │ answer       │  │ emotional... │  │ description │
     │  │ time_spent  │  │ category     │  │ social...    │  │ type (enum) │
     │  │ ...         │  │ ...          │  │ ...          │  │ difficulty  │
     │  └─────────────┘  └──────────────┘  └──────────────┘  └─────────────┘
     │
     │
     ▼
┌────────────┐
│ chat_logs  │
├────────────┤
│ parent_id  │
│   (FK)     │
│ message    │
│ response   │
│ context    │
│ timestamp  │
└────────────┘
```

---

## 🔑 Role-Based Access Control

```
┌──────────────────────────────────────────────────────────────┐
│                     JWT TOKEN PAYLOAD                         │
├──────────────────────────────────────────────────────────────┤
│  Parent Token:                Child Token:                    │
│  {                            {                               │
│    "sub": "123",                "sub": "456",                 │
│    "user_type": "parent",       "user_type": "child",         │
│    "exp": 1234567890            "exp": 1234567890             │
│  }                            }                               │
└────────────┬──────────────────────────────┬──────────────────┘
             │                              │
             ▼                              ▼
┌────────────────────────┐     ┌───────────────────────────────┐
│   PARENT ENDPOINTS     │     │      CHILD ENDPOINTS          │
├────────────────────────┤     ├───────────────────────────────┤
│ ✅ /auth/register-parent│     │ ❌ /auth/register-parent      │
│ ✅ /auth/add-child      │     │ ❌ /auth/add-child            │
│ ✅ /api/chat           │     │ ❌ /api/chat                  │
│ ✅ /dashboard/children │     │ ❌ /dashboard/children        │
│ ❌ /games              │     │ ✅ /games                     │
│ ❌ /games/{id}/play    │     │ ✅ /games/{id}/play           │
└────────────────────────┘     └───────────────────────────────┘

Implementation:
┌─────────────────────────────────────────────────────────────┐
│ def require_parent(token: str = Depends(oauth2_scheme)):   │
│     payload = decode_token(token)                           │
│     if not payload or payload.get("user_type") != "parent": │
│         raise HTTPException(403, "Parent access required")  │
│     return int(payload.get("sub"))                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Module Dependencies

```
main.py
  ├── app.routes.auth_v2 (auth_v2_router)
  │     ├── app.schemas.auth (Pydantic models)
  │     ├── app.services.auth_service (business logic)
  │     │     ├── google.oauth2.id_token (Google verification)
  │     │     ├── app.db.models.users_ext (User model)
  │     │     ├── app.db.models.parent (Parent model)
  │     │     ├── app.db.models.child (Child model)
  │     │     └── app.utils.security (password & JWT)
  │     └── app.utils.security (JWT validation)
  │
  ├── app.routes.chatbot (chatbot_router)
  │     ├── app.services.llm_client (OpenRouter)
  │     ├── app.nlp.intent_detection
  │     ├── app.rag.retriever (ChromaDB)
  │     └── app.db.models.chat_log (TODO: add parent_id)
  │
  └── app.db.session (database connection)
        └── app.db.base (SQLAlchemy Base)
              └── app.db.models.* (all models)
```

---

## 🔄 Request/Response Flow

### Example: Parent Creates Child Account

```
1. REQUEST
   ┌─────────────────────────────────────────────────────────┐
   │ POST /api/v1/auth/add-child                             │
   │ Headers:                                                │
   │   Authorization: Bearer eyJhbGc...                      │
   │   Content-Type: application/json                        │
   │ Body:                                                   │
   │   {                                                     │
   │     "username": "sara_khan",                            │
   │     "password": "secure123",                            │
   │     "name": "Sara Khan",                                │
   │     "age": 8                                            │
   │   }                                                     │
   └─────────────────────────────────────────────────────────┘
                            │
                            ▼
2. AUTH MIDDLEWARE (OAuth2PasswordBearer)
   ┌─────────────────────────────────────────────────────────┐
   │ Extract token from Authorization header                 │
   └─────────────────────────────────────────────────────────┘
                            │
                            ▼
3. DEPENDENCY: require_parent()
   ┌─────────────────────────────────────────────────────────┐
   │ • Decode JWT token                                      │
   │ • Verify user_type == "parent"                          │
   │ • Return parent user_id                                 │
   │                                                         │
   │ If fails: raise HTTPException(403)                      │
   └─────────────────────────────────────────────────────────┘
                            │
                            ▼
4. ROUTE HANDLER: add_child()
   ┌─────────────────────────────────────────────────────────┐
   │ • Validate request body (Pydantic)                      │
   │ • Call auth_service.add_child()                         │
   └─────────────────────────────────────────────────────────┘
                            │
                            ▼
5. SERVICE LAYER: auth_service.add_child()
   ┌─────────────────────────────────────────────────────────┐
   │ • Get parent from DB by user_id                         │
   │ • Hash password: hash_password("secure123")             │
   │ • Create User record (username, hashed_password)        │
   │ • Create Child record (name, age, parent_id)            │
   │ • Commit to database                                    │
   └─────────────────────────────────────────────────────────┘
                            │
                            ▼
6. RESPONSE
   ┌─────────────────────────────────────────────────────────┐
   │ 200 OK                                                  │
   │ {                                                       │
   │   "message": "Child account created successfully",      │
   │   "user_id": 456,                                       │
   │   "child_id": 123,                                      │
   │   "username": "sara_khan"                               │
   │ }                                                       │
   └─────────────────────────────────────────────────────────┘
```

---

## 🛡️ Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: HTTPS/TLS (Production)                            │
│ • Encrypts all traffic                                     │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: CORS Middleware                                   │
│ • Validates origin                                         │
│ • Blocks unauthorized domains                              │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: JWT Authentication                                │
│ • Verifies token signature                                 │
│ • Checks expiration                                        │
│ • Extracts user identity                                   │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 4: Role-Based Access Control                         │
│ • Validates user_type from JWT                             │
│ • Enforces endpoint permissions                            │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 5: Database Constraints                              │
│ • Foreign keys prevent orphaned records                    │
│ • Unique constraints prevent duplicates                    │
│ • Password hashed with bcrypt (12 rounds)                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📈 Scalability Considerations

### Current Architecture (Single Server)
```
Client → FastAPI → PostgreSQL → ChromaDB → OpenRouter API
```

### Future Architecture (Scaled)
```
                  ┌──────────────┐
                  │ Load Balancer│
                  └──────┬───────┘
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼
      ┌─────────┐  ┌─────────┐  ┌─────────┐
      │FastAPI 1│  │FastAPI 2│  │FastAPI 3│
      └────┬────┘  └────┬────┘  └────┬────┘
           │            │            │
           └────────────┼────────────┘
                        ▼
               ┌─────────────────┐
               │ PostgreSQL Pool │
               └─────────────────┘
```

**Optimizations to Consider:**
- Redis for JWT token caching
- CDN for static files
- Read replicas for database
- Message queue for async tasks (email notifications)
- Separate vector DB service for RAG

---

**Document Version:** 1.0  
**Last Updated:** 2025-01-14
