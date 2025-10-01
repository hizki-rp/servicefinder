#!/usr/bin/env python
"""
Script to export production data from Render PostgreSQL
Run this on your production server or with production database credentials
"""
import os
import django
from django.core.management import call_command

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_api.settings')
django.setup()

def export_data():
    """Export essential data to fixtures"""
    
    # Export users and profiles
    print("Exporting users...")
    call_command('dumpdata', 'auth.user', '--output=users.json', '--indent=2')
    
    print("Exporting profiles...")
    call_command('dumpdata', 'profiles', '--output=profiles.json', '--indent=2')
    
    print("Exporting universities...")
    call_command('dumpdata', 'universities.university', '--output=universities.json', '--indent=2')
    
    print("Exporting content creator data...")
    call_command('dumpdata', 'content_creator', '--output=content_creator.json', '--indent=2')
    
    print("Export completed!")
    print("Files created: users.json, profiles.json, universities.json, content_creator.json")

if __name__ == '__main__':
    export_data()