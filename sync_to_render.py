#!/usr/bin/env python3
"""
Sync SQLite data to Render's PostgreSQL database.
"""
import os
import django
import sqlite3
import json
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_api.settings')
django.setup()

from django.contrib.auth.models import User, Group
from universities.models import University, UserDashboard
from profiles.models import Profile
from content_creator.models import OpportunityPost

def sync_to_render():
    print("Syncing SQLite data to Render PostgreSQL...")
    
    sqlite_path = Path(__file__).parent / 'db.sqlite3'
    if not sqlite_path.exists():
        print("ERROR: SQLite database not found")
        return
    
    # Connect to SQLite
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()
    
    try:
        # Get user group
        user_group, created = Group.objects.get_or_create(name='user')
        if created:
            print("Created user group")
        
        # Clear existing data (be careful!)
        print("1. Clearing existing data...")
        UserDashboard.objects.all().delete()
        Profile.objects.all().delete()
        OpportunityPost.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()  # Keep superusers
        University.objects.all().delete()
        
        # Sync users
        print("2. Syncing users...")
        cursor.execute("SELECT * FROM auth_user")
        users = cursor.fetchall()
        
        for user_row in users:
            if not User.objects.filter(username=user_row[4]).exists():
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
        
        print(f"Synced {User.objects.count()} users")
        
        # Sync profiles
        print("3. Syncing profiles...")
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
        
        print(f"Synced {Profile.objects.count()} profiles")
        
        # Sync universities
        print("4. Syncing universities...")
        cursor.execute("SELECT id, name, country, city, application_link, application_fee, tuition_fee, university_link, description FROM universities_university")
        universities = cursor.fetchall()
        
        for uni_row in universities:
            University.objects.get_or_create(
                id=uni_row[0],
                defaults={
                    'name': uni_row[1],
                    'country': uni_row[2],
                    'city': uni_row[3],
                    'application_link': uni_row[4],
                    'application_fee': uni_row[5],
                    'tuition_fee': uni_row[6],
                    'university_link': uni_row[7],
                    'description': uni_row[8] or ''
                }
            )
        
        print(f"Synced {University.objects.count()} universities")
        
        # Sync opportunities
        print("5. Syncing opportunities...")
        try:
            cursor.execute("SELECT id, creator_id, title, description, content_type, content, is_active FROM content_creator_opportunitypost")
            opportunities = cursor.fetchall()
            
            for opp_row in opportunities:
                if User.objects.filter(id=opp_row[1]).exists():
                    OpportunityPost.objects.get_or_create(
                        id=opp_row[0],
                        defaults={
                            'creator_id': opp_row[1],
                            'title': opp_row[2],
                            'description': opp_row[3],
                            'content_type': opp_row[4] or 'guide',
                            'content': opp_row[5] or '',
                            'is_active': bool(opp_row[6])
                        }
                    )
            
            print(f"Synced {OpportunityPost.objects.count()} opportunities")
        except Exception as e:
            print(f"Error syncing opportunities: {e}")
        
        print("SUCCESS: Sync completed!")
        print("Your Render database now has all your SQLite data.")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()

if __name__ == "__main__":
    sync_to_render()