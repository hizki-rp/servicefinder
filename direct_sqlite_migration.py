#!/usr/bin/env python3
"""
Direct SQLite to PostgreSQL migration using sqlite3 module.
"""
import os
import django
import sqlite3
import json
from pathlib import Path
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_api.settings')
django.setup()

from django.contrib.auth.models import User, Group
from universities.models import University, UserDashboard
from profiles.models import Profile

def migrate_data():
    print("Direct SQLite to PostgreSQL migration...")
    
    sqlite_path = Path(__file__).parent / 'db.sqlite3'
    if not sqlite_path.exists():
        print("ERROR: SQLite database not found")
        return
    
    # Connect directly to SQLite
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()
    
    try:
        # Clear existing PostgreSQL data
        print("1. Clearing PostgreSQL data...")
        UserDashboard.objects.all().delete()
        Profile.objects.all().delete()
        User.objects.all().delete()
        University.objects.all().delete()
        
        # Get user group
        user_group = Group.objects.get(name='user')
        
        # Migrate users
        print("2. Migrating users...")
        cursor.execute("SELECT * FROM auth_user")
        users = cursor.fetchall()
        
        for user_row in users:
            user = User.objects.create(
                id=user_row[0],
                password=user_row[1],
                last_login=user_row[2],
                is_superuser=bool(user_row[3]),
                username=user_row[4],
                first_name=user_row[5],
                email=user_row[6],
                is_staff=bool(user_row[7]),
                is_active=bool(user_row[8]),
                date_joined=user_row[9],
                last_name=user_row[10] if len(user_row) > 10 else ''
            )
            if not user.is_superuser:
                user.groups.add(user_group)
        
        print(f"Created {User.objects.count()} users")
        
        # Migrate profiles
        print("3. Migrating profiles...")
        cursor.execute("SELECT id, user_id, bio, phone_number FROM profiles_profile")
        profiles = cursor.fetchall()
        
        for profile_row in profiles:
            Profile.objects.get_or_create(
                user_id=profile_row[1],
                defaults={
                    'bio': profile_row[2] or '',
                    'phone_number': profile_row[3] or ''
                }
            )
        
        print(f"Created {Profile.objects.count()} profiles")
        
        # Migrate universities
        print("4. Migrating universities...")
        cursor.execute("SELECT id, name, country, city, application_link, application_fee, tuition_fee, university_link, description FROM universities_university")
        universities = cursor.fetchall()
        
        for uni_row in universities:
            University.objects.create(
                id=uni_row[0],
                name=uni_row[1],
                country=uni_row[2],
                city=uni_row[3],
                application_link=uni_row[4],
                application_fee=uni_row[5],
                tuition_fee=uni_row[6],
                university_link=uni_row[7],
                description=uni_row[8] or ''
            )
        
        print(f"Created {University.objects.count()} universities")
        
        # Migrate opportunities
        print("5. Migrating opportunities...")
        try:
            from content_creator.models import OpportunityPost
            cursor.execute("SELECT id, creator_id, title, description, content_type, content, is_active FROM content_creator_opportunitypost")
            opportunities = cursor.fetchall()
            
            for opp_row in opportunities:
                OpportunityPost.objects.create(
                    id=opp_row[0],
                    creator_id=opp_row[1],
                    title=opp_row[2],
                    description=opp_row[3],
                    content_type=opp_row[4] or 'guide',
                    content=opp_row[5] or '',
                    is_active=bool(opp_row[6])
                )
            
            print(f"Created {OpportunityPost.objects.count()} opportunities")
        except Exception as e:
            print(f"Error migrating opportunities: {e}")
        
        print("SUCCESS: Migration completed!")
        print(f"Final counts:")
        print(f"- Users: {User.objects.count()}")
        print(f"- Universities: {University.objects.count()}")
        print(f"- Profiles: {Profile.objects.count()}")
        try:
            from content_creator.models import OpportunityPost
            print(f"- Opportunities: {OpportunityPost.objects.count()}")
        except:
            print(f"- Opportunities: 0 (model not available)")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_data()