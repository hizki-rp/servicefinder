#!/usr/bin/env python3
"""
Complete SQLite to PostgreSQL migration script.
"""
import os
import django
import sys
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_api.settings')
django.setup()

from django.core.management import call_command
from django.db import connections
from django.conf import settings
from django.contrib.auth.models import User
from universities.models import University
from profiles.models import Profile

def main():
    print("Starting complete SQLite to PostgreSQL migration...")
    
    # Check if SQLite database exists
    sqlite_path = Path(__file__).parent / 'db.sqlite3'
    if not sqlite_path.exists():
        print(f"ERROR: SQLite database not found at {sqlite_path}")
        sys.exit(1)
    
    # Store original PostgreSQL config
    original_db = settings.DATABASES['default'].copy()
    
    try:
        # Step 1: Export all data from SQLite
        print("1. Connecting to SQLite database...")
        settings.DATABASES['default'] = {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': sqlite_path,
        }
        connections.close_all()
        
        # Export everything except problematic tables
        print("2. Exporting all data from SQLite...")
        with open('full_data_export.json', 'w', encoding='utf-8') as f:
            call_command('dumpdata', 
                        '--natural-foreign', 
                        '--natural-primary',
                        '--exclude=contenttypes',
                        '--exclude=auth.permission',
                        '--exclude=sessions.session',
                        '--exclude=admin.logentry',
                        '--exclude=django_celery_beat',
                        '--exclude=django_celery_results',
                        stdout=f)
        
        # Step 2: Switch back to PostgreSQL and load data
        print("3. Switching to PostgreSQL...")
        settings.DATABASES['default'] = original_db
        connections.close_all()
        
        # Clear existing data (except groups we created)
        print("4. Clearing existing PostgreSQL data...")
        User.objects.all().delete()
        University.objects.all().delete()
        Profile.objects.all().delete()
        
        # Load the exported data
        print("5. Loading SQLite data into PostgreSQL...")
        call_command('loaddata', 'full_data_export.json')
        
        # Verify migration
        user_count = User.objects.count()
        uni_count = University.objects.count()
        
        print(f"SUCCESS: Migration completed!")
        print(f"- Users migrated: {user_count}")
        print(f"- Universities migrated: {uni_count}")
        
        # Clean up
        os.remove('full_data_export.json')
        print("Cleaned up temporary files")
        
    except Exception as e:
        print(f"ERROR during migration: {e}")
        print("Restoring PostgreSQL connection...")
        settings.DATABASES['default'] = original_db
        connections.close_all()
        
        # Clean up on error
        if os.path.exists('full_data_export.json'):
            os.remove('full_data_export.json')

if __name__ == "__main__":
    main()