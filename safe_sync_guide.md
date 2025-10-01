# Safe Production Data Sync Guide

## 🚨 CRITICAL: Never Risk Production Data

### Step 1: Export Production Database (Render)
```bash
# Option A: Use Render Dashboard
# Go to Render Dashboard → Your Database → "Download Snapshot"

# Option B: Direct PostgreSQL dump (get connection details from Render)
pg_dump -h [RENDER_HOST] -U [RENDER_USER] -d [RENDER_DB] --no-owner --no-privileges > production_backup.sql
```

### Step 2: Setup Local PostgreSQL (Match Production)
```bash
# Install PostgreSQL locally if not already installed
# Create local database
createdb uni_finder_local

# Import production data
psql -d uni_finder_local < production_backup.sql
```

### Step 3: Update Local Settings
```python
# In settings.py - ensure you use PostgreSQL locally too
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'uni_finder_local',
        'USER': 'your_local_user',
        'PASSWORD': 'your_local_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Step 4: Test New Features Locally
```bash
# Run with production data
python manage.py runserver

# Test all new features thoroughly
# Ensure existing users can still login
# Verify subscriptions still work
```

### Step 5: Safe Deployment Process
```bash
# 1. Commit only code changes (never database files)
git add .
git commit -m "Add creator opportunities feature"
git push origin main

# 2. Render will auto-deploy and run migrations safely
# 3. Monitor deployment logs for any issues
```

## ✅ What This Approach Guarantees:
- All existing users keep their accounts
- Subscriptions remain active
- No data loss during deployment
- New features work with real data

## 🔒 Safety Checklist:
- [ ] Production database backed up
- [ ] Local environment matches production (PostgreSQL)
- [ ] New features tested with real production data
- [ ] Only code changes committed (no database files)
- [ ] Migrations tested locally first

## 🚫 Never Do:
- Don't commit database files
- Don't run `python manage.py flush` on production
- Don't delete migration files
- Don't assume SQLite behavior = PostgreSQL behavior