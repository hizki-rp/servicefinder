#!/usr/bin/env python3
"""
Give all users active subscriptions.
"""
import os
import django
from datetime import date, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_api.settings')
django.setup()

from universities.models import UserDashboard
from django.contrib.auth.models import User

def activate_all_subscriptions():
    print("Activating subscriptions for all users...")
    
    users = User.objects.all()
    
    for user in users:
        dashboard, created = UserDashboard.objects.get_or_create(user=user)
        dashboard.subscription_status = 'active'
        dashboard.subscription_end_date = date.today() + timedelta(days=30)
        dashboard.save()
        
        print(f"Activated subscription for {user.username}")
    
    print(f"Activated subscriptions for {users.count()} users")

if __name__ == "__main__":
    activate_all_subscriptions()