#!/usr/bin/env python3
"""
Migrate UserDashboard data from SQLite to PostgreSQL.
"""
import os
import django
import sqlite3
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_api.settings')
django.setup()

from universities.models import UserDashboard, University
from django.contrib.auth.models import User

def migrate_dashboard_data():
    print("Migrating UserDashboard data from SQLite...")
    
    sqlite_path = Path(__file__).parent / 'db.sqlite3'
    if not sqlite_path.exists():
        print("ERROR: SQLite database not found")
        return
    
    # Connect to SQLite
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()
    
    try:
        # Get dashboard data
        cursor.execute("SELECT * FROM universities_userdashboard")
        dashboards = cursor.fetchall()
        
        print(f"Found {len(dashboards)} dashboards in SQLite")
        
        for dash_row in dashboards:
            user_id = dash_row[1]  # user_id column
            subscription_status = dash_row[2]  # subscription_status
            subscription_end_date = dash_row[3]  # subscription_end_date
            
            try:
                user = User.objects.get(id=user_id)
                dashboard, created = UserDashboard.objects.get_or_create(user=user)
                
                # Update subscription info
                dashboard.subscription_status = subscription_status or 'expired'
                dashboard.subscription_end_date = subscription_end_date if subscription_end_date else None
                dashboard.save()
                
                print(f"Updated dashboard for user {user.username}: {subscription_status}")
                
            except User.DoesNotExist:
                print(f"User {user_id} not found, skipping dashboard")
        
        # Migrate favorites
        print("Migrating favorites...")
        cursor.execute("SELECT * FROM universities_userdashboard_favorites")
        favorites = cursor.fetchall()
        
        for fav_row in favorites:
            dashboard_id = fav_row[1]
            university_id = fav_row[2]
            
            try:
                # Find dashboard by original SQLite ID
                cursor.execute("SELECT user_id FROM universities_userdashboard WHERE id = ?", (dashboard_id,))
                user_id_result = cursor.fetchone()
                if user_id_result:
                    user_id = user_id_result[0]
                    user = User.objects.get(id=user_id)
                    dashboard = UserDashboard.objects.get(user=user)
                    university = University.objects.get(id=university_id)
                    dashboard.favorites.add(university)
                    print(f"Added favorite for {user.username}: {university.name}")
            except Exception as e:
                print(f"Error adding favorite: {e}")
        
        # Migrate planning_to_apply
        print("Migrating planning_to_apply...")
        cursor.execute("SELECT * FROM universities_userdashboard_planning_to_apply")
        planning = cursor.fetchall()
        
        for plan_row in planning:
            dashboard_id = plan_row[1]
            university_id = plan_row[2]
            
            try:
                cursor.execute("SELECT user_id FROM universities_userdashboard WHERE id = ?", (dashboard_id,))
                user_id_result = cursor.fetchone()
                if user_id_result:
                    user_id = user_id_result[0]
                    user = User.objects.get(id=user_id)
                    dashboard = UserDashboard.objects.get(user=user)
                    university = University.objects.get(id=university_id)
                    dashboard.planning_to_apply.add(university)
                    print(f"Added planning_to_apply for {user.username}: {university.name}")
            except Exception as e:
                print(f"Error adding planning_to_apply: {e}")
        
        print("Dashboard migration completed!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_dashboard_data()