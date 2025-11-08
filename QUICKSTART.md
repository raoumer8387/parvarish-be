# Quick Start - Role-Based Authentication

## 🚀 Get Started in 5 Minutes

This is a streamlined guide to get your role-based auth system running. For detailed explanations, see `SETUP_GUIDE.md`.

---

## Prerequisites
- ✅ PostgreSQL installed and running
- ✅ Python 3.8+ installed
- ✅ Google Cloud project with OAuth 2.0 credentials

---

## Step 1: Install Dependencies (2 minutes)

```powershell
# Navigate to project
cd "e:\KIET\Parvaish AI\parvarish-be"

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install packages
pip install -r requirements.txt
```

---

## Step 2: Configure Environment (1 minute)

```powershell
# Copy template
copy .env.example .env

# Edit .env and update these values:
# - JWT_SECRET=<generate-random-64-char-string>
# - GOOGLE_CLIENT_ID=<your-client-id>.apps.googleusercontent.com
```

**Generate JWT Secret:**
```powershell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object {[char]$_})
```

**Get Google Client ID:**
1. Go to https://console.cloud.google.com/
2. Create OAuth 2.0 Client ID
3. Copy the Client ID

---

## Step 3: Setup Database (1 minute)

```powershell
# Initialize Alembic
alembic init alembic

# Edit alembic.ini line 63:
# sqlalchemy.url = postgresql://postgres:rao14593@localhost:5432/parvarish_db

# Create migration
alembic revision --autogenerate -m "Add parent-child auth system"

# Apply migration
alembic upgrade head
```

**Verify:**
```powershell
psql -U postgres -d parvarish_db
\dt
# Should show: users, parents, children, games, etc.
```

---

## Step 4: Run Server (30 seconds)

```powershell
uvicorn main:app --reload
```

**Visit:**
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

---

## Step 5: Test API (30 seconds)

### Option A: Swagger UI
1. Go to http://localhost:8000/docs
2. Find `POST /api/v1/auth/google-login`
3. Click "Try it out"
4. Paste Google ID token
5. Execute

### Option B: PowerShell
```powershell
# Parent login
$response = Invoke-RestMethod -Uri http://localhost:8000/api/v1/auth/google-login `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"id_token":"YOUR_GOOGLE_TOKEN_HERE"}'

$token = $response.access_token

# Add child
Invoke-RestMethod -Uri http://localhost:8000/api/v1/auth/add-child `
  -Method POST `
  -Headers @{Authorization="Bearer $token"} `
  -ContentType "application/json" `
  -Body '{"username":"test_child","password":"pass123","name":"Test Child","age":8}'

# Child login
Invoke-RestMethod -Uri http://localhost:8000/api/v1/auth/login-child `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"username":"test_child","password":"pass123"}'
```

---

## ✅ Success Checklist

After completing steps above, you should have:
- [ ] Server running on http://localhost:8000
- [ ] 8 database tables created (users, parents, children, games, etc.)
- [ ] `/docs` showing all auth endpoints
- [ ] Able to login with Google OAuth
- [ ] Able to create child accounts
- [ ] Able to login as child with username/password

---

## 🐛 Quick Troubleshooting

| Issue | Fix |
|-------|-----|
| Import errors | Run `pip install -r requirements.txt` |
| Database connection failed | Check PostgreSQL is running: `Get-Service postgresql*` |
| Alembic errors | See `ALEMBIC_GUIDE.md` |
| Invalid Google token | Get fresh token from frontend |
| Migration fails | See `ALEMBIC_GUIDE.md` Step 4 |

---

## 📚 Next Steps

1. **Add Role-Based Access Control**
   - Update `app/routes/chatbot.py` to require parent JWT
   - See `IMPLEMENTATION_SUMMARY.md` "Priority 1"

2. **Create Dashboard Endpoints**
   - Create `app/routes/dashboard.py`
   - Add endpoints for parent to view children stats
   - See `SETUP_GUIDE.md` "Next Steps"

3. **Create Games Endpoints**
   - Create `app/routes/games.py`
   - Add endpoints for children to play games
   - See `SETUP_GUIDE.md` "Next Steps"

4. **Seed Initial Data**
   - Populate `games` table with educational games
   - See `IMPLEMENTATION_SUMMARY.md` "Priority 4"

---

## 📖 Documentation

- **Full Setup Guide**: `SETUP_GUIDE.md` (400+ lines)
- **Implementation Summary**: `IMPLEMENTATION_SUMMARY.md`
- **Alembic Guide**: `ALEMBIC_GUIDE.md`
- **Main README**: `README.md`
- **Environment Template**: `.env.example`

---

## 🎯 What You've Built

A complete FastAPI backend with:
- ✅ Dual authentication (Google OAuth + username/password)
- ✅ Role-based access (parent/child)
- ✅ JWT token generation and validation
- ✅ 8 database tables with proper relationships
- ✅ 4 auth endpoints
- ✅ Secure password hashing (bcrypt)
- ✅ Google OAuth verification

**Time to completion**: ~5 minutes  
**Files created**: 14 Python files + 4 docs  
**Lines of code**: ~800  
**Next**: Add role-based access control to chatbot endpoint

---

**Need Help?** See detailed guides:
- Setup issues → `SETUP_GUIDE.md#troubleshooting`
- Migration errors → `ALEMBIC_GUIDE.md#troubleshooting`
- Implementation details → `IMPLEMENTATION_SUMMARY.md`
