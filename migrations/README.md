# Database Migrations

## Running Migrations

To apply migrations, run them in order:

```powershell
python migrations/001_add_parent_child_support.py
```

## Migration History

### 001_add_parent_child_support.py
**Date:** 2025-11-05  
**Description:** Adds parent and child support to the database

**Changes:**
- Adds `username` column to `users` table (if missing)
- Adds `user_type` column to `users` table (if missing)
- Creates `parents` table (if not exists)
- Creates `children` table (if not exists)

**Usage:**
```powershell
python migrations/001_add_parent_child_support.py
```

## Creating New Migrations

1. Create a new file: `migrations/00X_migration_name.py`
2. Follow the pattern in existing migrations
3. Test the migration on a development database first
4. Update this README with migration details

## Rollback

Currently, migrations do not support automatic rollback. To rollback:
1. Manually write SQL to reverse changes
2. Or restore from database backup
