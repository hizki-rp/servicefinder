#!/usr/bin/env python3
"""
Manual data migration from SQLite to PostgreSQL.
"""
import os
import django
import sys
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_api.settings')
django.setup()

from django.db import connections
from django.conf import settings
from django.contrib.auth.models import User, Group
from universities.models import University, UserDashboard
from profiles.models import Profile

def migrate_users_and_data():
    print("Manual migration from SQLite to PostgreSQL...")
    
    sqlite_path = Path(__file__).parent / 'db.sqlite3'
    if not sqlite_path.exists():
        print(f"ERROR: SQLite database not found")
        return
    
    # Store original config
    original_db = settings.DATABASES['default'].copy()
    
    try:
        # Connect to SQLite
        print("1. Reading data from SQLite...")
        settings.DATABASES['default'] = {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': sqlite_path,
        }
        connections.close_all()
        
        # Read all data from SQLite using raw queries
        from django.db import connection
        cursor = connection.cursor()
        
        print("Executing SQLite queries...")
        
        # Get users
        try:
            cursor.execute("SELECT * FROM auth_user")
            user_columns = [col[0] for col in cursor.description]
            sqlite_users = [dict(zip(user_columns, row)) for row in cursor.fetchall()]
            print(f"Read {len(sqlite_users)} users from SQLite")
        except Exception as e:
            print(f"Error reading users: {e}")
            sqlite_users = []
        
        # Get universities
        try:
            cursor.execute("SELECT * FROM universities_university")
            uni_columns = [col[0] for col in cursor.description]
            sqlite_universities = [dict(zip(uni_columns, row)) for row in cursor.fetchall()]
            print(f"Read {len(sqlite_universities)} universities from SQLite")
        except Exception as e:
            print(f"Error reading universities: {e}")
            sqlite_universities = []
        
        # Get profiles
        try:
            cursor.execute("SELECT * FROM profiles_profile")
            profile_columns = [col[0] for col in cursor.description]
            sqlite_profiles = [dict(zip(profile_columns, row)) for row in cursor.fetchall()]
            print(f"Read {len(sqlite_profiles)} profiles from SQLite")
        except Exception as e:
            print(f"Error reading profiles: {e}")
            sqlite_profiles = []
        
        print(f"Found {len(sqlite_users)} users, {len(sqlite_universities)} universities")
        print(f"Sample user: {sqlite_users[0] if sqlite_users else 'None'}")
        print(f"Sample university: {sqlite_universities[0] if sqlite_universities else 'None'}")
        
        # Switch to PostgreSQL
        print("2. Switching to PostgreSQL...")
        settings.DATABASES['default'] = original_db
        connections.close_all()
        
        # Clear existing data
        print("3. Clearing PostgreSQL data...")
        UserDashboard.objects.all().delete()
        Profile.objects.all().delete()
        User.objects.all().delete()
        University.objects.all().delete()
        
        # Migrate users
        print("4. Creating users...")
        user_group = Group.objects.get(name='user')
        
        for user_data in sqlite_users:
            user = User.objects.create(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                password=user_data['password'],
                is_staff=user_data['is_staff'],
                is_active=user_data['is_active'],
                is_superuser=user_data['is_superuser'],
                date_joined=user_data['date_joined'],
                last_login=user_data['last_login']
            )
            if not user.is_superuser:
                user.groups.add(user_group)
        
        # Migrate profiles
        print("5. Creating profiles...")
        for profile_data in sqlite_profiles:
            Profile.objects.create(
                user_id=profile_data['user_id'],
                bio=profile_data.get('bio', ''),
                phone_number=profile_data.get('phone_number', ''),
                preferred_intakes=profile_data.get('preferred_intakes', [])
            )
        
        # Migrate universities
        print("6. Creating universities...")
        for uni_data in sqlite_universities:
            University.objects.create(
                id=uni_data['id'],
                name=uni_data['name'],
                country=uni_data['country'],
                city=uni_data['city'],
                course_offered=uni_data['course_offered'],
                application_fee=uni_data['application_fee'],
                tuition_fee=uni_data['tuition_fee'],
                intakes=uni_data.get('intakes', []),
                bachelor_programs=uni_data.get('bachelor_programs', []),
                masters_programs=uni_data.get('masters_programs', []),
                scholarships=uni_data.get('scholarships', []),
                university_link=uni_data['university_link'],
                application_link=uni_data['application_link'],
                description=uni_data.get('description', '')
            )
        
        print("SUCCESS: Migration completed!")
        print(f"- Users: {User.objects.count()}")
        print(f"- Universities: {University.objects.count()}")
        print(f"- Profiles: {Profile.objects.count()}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        settings.DATABASES['default'] = original_db
        connections.close_all()

if __name__ == "__main__":
    migrate_users_and_data()