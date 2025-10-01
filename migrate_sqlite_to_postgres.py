#!/usr/bin/env python3
"""
Script to migrate data from SQLite to PostgreSQL.
This will copy all users, profiles, and other data from your SQLite database.
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
import json

def main():
    print("Migrating data from SQLite to PostgreSQL...")
    
    # Check if SQLite database exists
    sqlite_path = Path(__file__).parent / 'db.sqlite3'
    if not sqlite_path.exists():
        print(f"ERROR: SQLite database not found at {sqlite_path}")
        sys.exit(1)
    
    # Temporarily switch to SQLite to export data
    print("1. Exporting data from SQLite...")
    
    # Create a temporary settings configuration for SQLite
    original_db = settings.DATABASES['default'].copy()
    
    # Switch to SQLite
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': sqlite_path,
    }
    
    # Close existing connections
    connections.close_all()
    
    # Export data from SQLite
    with open('sqlite_data.json', 'w') as f:
        call_command('dumpdata', 
                    '--natural-foreign', 
                    '--natural-primary',
                    '--exclude=contenttypes',
                    '--exclude=auth.permission',
                    '--exclude=sessions.session',
                    '--exclude=admin.logentry',
                    stdout=f)
    
    print("2. Switching back to PostgreSQL...")
    
    # Switch back to PostgreSQL
    settings.DATABASES['default'] = original_db
    connections.close_all()
    
    print("3. Loading data into PostgreSQL...")
    
    # Load data into PostgreSQL
    try:
        call_command('loaddata', 'sqlite_data.json')
        print("✅ Data migration completed successfully!")
        
        # Clean up
        os.remove('sqlite_data.json')
        print("🗑️  Cleaned up temporary files")
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        print("💡 You may need to create a superuser manually:")
        print("   python manage.py createsuperuser")

if __name__ == "__main__":
    main()