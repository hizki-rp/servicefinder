#!/usr/bin/env python
"""
Script to import production data into local database
Run this locally after getting the JSON files from production
"""
import os
import django
from django.core.management import call_command

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_api.settings')
django.setup()

def import_data():
    """Import data from fixtures"""
    
    # Clear existing data (optional - be careful!)
    print("WARNING: This will replace existing data!")
    confirm = input("Continue? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Import cancelled.")
        return
    
    try:
        print("Importing users...")
        call_command('loaddata', 'users.json')
        
        print("Importing profiles...")
        call_command('loaddata', 'profiles.json')
        
        print("Importing universities...")
        call_command('loaddata', 'universities.json')
        
        print("Importing content creator data...")
        call_command('loaddata', 'content_creator.json')
        
        print("Import completed successfully!")
        
    except Exception as e:
        print(f"Error during import: {e}")
        print("You may need to run migrations first: python manage.py migrate")

if __name__ == '__main__':
    import_data()