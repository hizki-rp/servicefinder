#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status.
set -e

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Fix any missing columns from inconsistent migration history (safe, idempotent)
python fix_remote_db.py

# Create any new migrations
python manage.py makemigrations

# Apply database migrations
python manage.py migrate

# Create default groups
python manage.py create_groups

# Seed two-tier taxonomy (idempotent — safe to run every deploy)
python manage.py seed_taxonomy

# Create superuser if environment variables are set
python manage.py create_superuser

# Force-reset admin password to ensure access
python manage.py shell -c "
from django.contrib.auth.models import User
u, created = User.objects.get_or_create(username='admin')
u.set_password('MertAdmin2024!')
u.is_staff = True
u.is_superuser = True
u.is_active = True
u.save()
print('Admin password reset to MertAdmin2024!')
"