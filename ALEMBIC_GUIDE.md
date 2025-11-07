# Alembic Database Migration Guide

## 🎯 Purpose
This guide helps you set up and run database migrations using Alembic for the role-based authentication system.

---

## Step 1: Initialize Alembic (First Time Only)

```powershell
# Make sure you're in the project root directory
cd e:\KIET\Parvaish AI\parvarish-be

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Initialize Alembic
alembic init alembic
```

**Output**: Creates `alembic/` directory with:
- `versions/` - migration scripts
- `env.py` - Alembic environment configuration
- `script.py.mako` - migration template
- `alembic.ini` - Alembic configuration file

---

## Step 2: Configure Alembic

### Option A: Simple Configuration (alembic.ini)

Edit `alembic.ini` line 63:
```ini
# BEFORE:
sqlalchemy.url = driver://user:pass@localhost/dbname

# AFTER:
sqlalchemy.url = postgresql://postgres:rao14593@localhost:5432/parvarish_db
```

⚠️ **Security Note**: Don't commit database credentials! Use Option B for production.

---

### Option B: Environment Variables (Recommended)

Edit `alembic/env.py` - add this at the top after imports:

```python
# Add these imports at the top
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import your Base and models
from app.db.base import Base
from app.db.models import (
    User, Message, UserExt, Parent, Child, Game,
    ChildGameActivity, ChildBehaviorResponse, 
    ChildBehaviorScore, ChatLog, UserType, GameType
)

# Replace the sqlalchemy.url line (around line 20-25)
config.set_main_option(
    'sqlalchemy.url',
    os.getenv('DATABASE_URL', 'postgresql://postgres:rao14593@localhost:5432/parvarish_db')
)

# Set target_metadata (around line 30)
target_metadata = Base.metadata
```

This allows Alembic to:
1. Read `DATABASE_URL` from your `.env` file
2. Auto-detect all your SQLAlchemy models
3. Generate migrations based on model changes

---

## Step 3: Create Initial Migration

```powershell
# Generate migration from models
alembic revision --autogenerate -m "Add parent-child role system"
```

**Output**: Creates a new file in `alembic/versions/` like:
```
alembic/versions/abc123def456_add_parent_child_role_system.py
```

---

## Step 4: Review Generated Migration

Open the generated file and check:

### ⚠️ IMPORTANT: Handle Existing `users` Table

If you already have a `users` table, the migration might try to create it again. 

**Before running the migration**, edit it:

```python
def upgrade():
    # Check if users table exists before creating
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    if 'users' not in inspector.get_table_names():
        # Create new users table
        op.create_table(
            'users',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('google_uid', sa.String(), nullable=True),
            sa.Column('email', sa.String(), nullable=True),
            sa.Column('username', sa.String(), nullable=True),
            sa.Column('hashed_password', sa.String(), nullable=True),
            sa.Column('user_type', sa.String(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('google_uid'),
            sa.UniqueConstraint('username')
        )
    else:
        # Add new columns to existing users table
        op.add_column('users', sa.Column('google_uid', sa.String(), nullable=True))
        op.add_column('users', sa.Column('username', sa.String(), nullable=True))
        op.add_column('users', sa.Column('hashed_password', sa.String(), nullable=True))
        op.add_column('users', sa.Column('user_type', sa.String(), nullable=True))
        
        # Set default user_type for existing rows
        op.execute("UPDATE users SET user_type = 'parent' WHERE user_type IS NULL")
        
        # Make user_type non-nullable after setting defaults
        op.alter_column('users', 'user_type', nullable=False)
        
        # Add unique constraints
        op.create_unique_constraint('uq_users_google_uid', 'users', ['google_uid'])
        op.create_unique_constraint('uq_users_username', 'users', ['username'])
    
    # Create other tables (parents, children, games, etc.)
    op.create_table(
        'parents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        # ... rest of columns
    )
    
    # ... continue with other tables
```

---

## Step 5: Apply Migration

```powershell
# Apply all pending migrations
alembic upgrade head
```

**Expected Output**:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> abc123def456, Add parent-child role system
```

**Verify in PostgreSQL**:
```sql
-- Connect to your database
psql -U postgres -d parvarish_db

-- List all tables
\dt

-- Should show:
-- users, parents, children, games, child_game_activity,
-- child_behavior_responses, child_behavior_scores, chat_logs, alembic_version
```

---

## Common Migration Commands

### Check Current Version
```powershell
alembic current
```

### View Migration History
```powershell
alembic history
```

### Rollback One Version
```powershell
alembic downgrade -1
```

### Rollback to Specific Version
```powershell
alembic downgrade abc123def456
```

### Rollback All Migrations
```powershell
alembic downgrade base
```

---

## Troubleshooting

### Error: "Can't locate revision identified by 'abc123'"
**Cause**: Migration file deleted or version mismatch

**Fix**:
```powershell
# Stamp database with current version
alembic stamp head
```

---

### Error: "Table 'users' already exists"
**Cause**: Table exists but not tracked by Alembic

**Fix**:
```powershell
# Option 1: Drop and recreate (DEVELOPMENT ONLY)
# psql: DROP TABLE users CASCADE;
# Then run: alembic upgrade head

# Option 2: Manually stamp version (if table structure matches)
alembic stamp head
```

---

### Error: "Column 'user_type' cannot be null"
**Cause**: Existing users table has no default for new column

**Fix**: Edit migration (see Step 4) to set default values before making column non-nullable.

---

### Error: "Cannot connect to database"
**Cause**: Database not running or wrong credentials

**Fix**:
```powershell
# Check PostgreSQL is running
Get-Service -Name postgresql*

# Start if stopped
Start-Service postgresql-x64-14  # Adjust version number

# Verify connection
psql -U postgres -d parvarish_db
```

---

## Future Migrations

When you add new models or modify existing ones:

```powershell
# 1. Update your model files
# e.g., add new column to Child model

# 2. Generate migration
alembic revision --autogenerate -m "Add new_column to Child"

# 3. Review generated migration file

# 4. Apply migration
alembic upgrade head
```

---

## Migration Best Practices

### ✅ DO:
- Review auto-generated migrations before applying
- Test migrations on development database first
- Backup production database before running migrations
- Use descriptive migration messages
- Handle backward compatibility for existing data

### ❌ DON'T:
- Edit migration files after they've been applied
- Delete migration files from `versions/` directory
- Run migrations directly on production without testing
- Commit database credentials in `alembic.ini`
- Skip reviewing auto-generated SQL

---

## Sample Migration Workflow

```powershell
# 1. Create new model or modify existing
# Edit app/db/models/child.py to add 'favorite_color' field

# 2. Generate migration
alembic revision --autogenerate -m "Add favorite_color to Child"

# 3. Review migration file
code alembic/versions/*_add_favorite_color_to_child.py

# 4. Test on development DB
alembic upgrade head

# 5. Verify changes
psql -U postgres -d parvarish_db
# \d children

# 6. If successful, commit migration
git add alembic/versions/*_add_favorite_color_to_child.py
git commit -m "Add favorite_color field to Child model"
```

---

## Verification Checklist

After running migrations, verify:
- [ ] `alembic current` shows latest version
- [ ] `alembic history` shows all migrations
- [ ] All tables exist: `\dt` in psql
- [ ] Foreign keys are correct: `\d table_name`
- [ ] Unique constraints applied
- [ ] Enum values accepted (test with INSERT)
- [ ] No orphaned records (run CRUD tests)

---

## Emergency Rollback

If migration causes issues in production:

```powershell
# 1. Rollback immediately
alembic downgrade -1

# 2. Verify app works
uvicorn main:app --reload

# 3. Investigate migration file
# Fix issues

# 4. Re-apply when ready
alembic upgrade head
```

---

**Last Updated**: 2025-01-14  
**Next Steps**: Follow Step 1 to initialize Alembic in your project
