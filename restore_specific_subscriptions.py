#!/usr/bin/env python3
"""
Restore subscriptions for specific users only.
"""
import os
import django
from datetime import date, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_api.settings')
django.setup()

from universities.models import UserDashboard
from django.contrib.auth.models import User

def restore_subscriptions():
    print("Restoring subscriptions for specific users...")
    
    # First, set all users to expired
    UserDashboard.objects.all().update(
        subscription_status='expired',
        subscription_end_date=None
    )
    print("Set all subscriptions to expired")
    
    # Give active subscription only to 'hizk' who had one
    try:
        user = User.objects.get(username='hizk')
        dashboard, created = UserDashboard.objects.get_or_create(user=user)
        dashboard.subscription_status = 'active'
        dashboard.subscription_end_date = date.today() + timedelta(days=30)
        dashboard.save()
        print(f"Activated subscription for {user.username}")
    except User.DoesNotExist:
        print("User 'hizk' not found")
    
    # Admins don't need subscriptions - they bypass the check
    print("Admins (staff users) automatically bypass subscription checks")

if __name__ == "__main__":
    restore_subscriptions()