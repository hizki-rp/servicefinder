# Database Sync Commands

## Method 1: Using Django Management Commands

### On Production (Render):
```bash
# Export data
python manage.py dumpdata auth.user --output=users.json --indent=2
python manage.py dumpdata profiles --output=profiles.json --indent=2
python manage.py dumpdata universities.university --output=universities.json --indent=2
python manage.py dumpdata content_creator --output=content_creator.json --indent=2
```

### Download files from Render to local:
```bash
# Use Render's file download or git to get the JSON files
```

### On Local:
```bash
# Backup current local database first
python manage.py dumpdata --output=local_backup.json --indent=2

# Import production data
python manage.py loaddata users.json
python manage.py loaddata profiles.json
python manage.py loaddata universities.json
python manage.py loaddata content_creator.json
```

## Method 2: Direct Database Dump (PostgreSQL)

### On Production:
```bash
# Get database URL from Render dashboard
pg_dump DATABASE_URL > production_dump.sql
```

### On Local:
```bash
# Drop and recreate local database
dropdb your_local_db
createdb your_local_db
psql your_local_db < production_dump.sql
```

## Method 3: Using Scripts
```bash
# On production
python export_production_data.py

# On local (after getting files)
python import_production_data.py
```

## Important Notes:
1. **Backup first**: Always backup your local database before importing
2. **Migrations**: Run migrations after import if needed
3. **Media files**: Don't forget to sync media files (profile pictures, etc.)
4. **Environment variables**: Update local .env with production-like settings if needed