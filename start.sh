#!/usr/bin/env bash
set -e

echo "==> Running migrations..."
python manage.py migrate --noinput

echo "==> Creating default groups..."
python manage.py create_groups

echo "==> Seeding taxonomy..."
python manage.py seed_taxonomy

echo "==> Resetting admin account..."
python manage.py reset_admin

echo "==> Starting gunicorn..."
exec gunicorn university_api.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers 2 \
  --timeout 120
