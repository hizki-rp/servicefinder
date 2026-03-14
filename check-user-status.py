#!/usr/bin/env python
"""
Check user and provider status in database
Usage: python check-user-status.py <username>
Run from backend directory: cd backend && python check-user-status.py hhz
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from providers.models import ProviderProfile

def check_user(username):
    print(f"\n{'='*60}")
    print(f"Checking user: {username}")
    print(f"{'='*60}\n")
    
    try:
        user = User.objects.get(username=username)
        print(f"✅ User found:")
        print(f"   - ID: {user.id}")
        print(f"   - Username: {user.username}")
        print(f"   - Email: {user.email}")
        print(f"   - Is Staff: {user.is_staff}")
        print(f"   - Is Active: {user.is_active}")
        print()
        
        # Check provider profile
        try:
            profile = ProviderProfile.objects.get(user=user)
            print(f"✅ Provider Profile found:")
            print(f"   - ID: {profile.id}")
            print(f"   - Phone: {profile.phone_number}")
            print(f"   - City: {profile.city}")
            print(f"   - Is Verified: {profile.is_verified}")
            print(f"   - National ID Verified: {profile.national_id_verified}")
            print(f"   - Payment Verified: {profile.payment_verified}")
            print(f"   - Has National ID: {profile.has_national_id}")
            print(f"   - Has Payment Proof: {profile.has_payment_proof}")
            print(f"   - Trial Active: {profile.is_trial_active}")
            print(f"   - Trial Start: {profile.trial_start_date}")
            print(f"   - Trial Expiry: {profile.trial_expiry_date}")
            print(f"   - Days Until Expiry: {profile.days_until_trial_expiry}")
            print(f"   - Services Count: {profile.services_count}")
            print(f"   - Max Services: {profile.max_services_allowed}")
            print()
            
            # Check services
            services = profile.services.all()
            print(f"📋 Services ({services.count()}):")
            for service in services:
                print(f"   - {service.name} ({service.service_category})")
            print()
            
            # Diagnosis
            print(f"🔍 Diagnosis:")
            if not profile.is_verified:
                print(f"   ❌ NOT VERIFIED - This is the issue!")
                print(f"   → Admin needs to check 'Is verified' in Django admin")
            else:
                print(f"   ✅ Verified")
                
            if not profile.national_id_verified:
                print(f"   ⚠️  National ID not verified")
            else:
                print(f"   ✅ National ID verified")
                
            if not profile.has_national_id:
                print(f"   ⚠️  No National ID uploaded")
            else:
                print(f"   ✅ National ID uploaded")
                
            print()
            print(f"🔧 Fix:")
            if not profile.is_verified:
                print(f"   1. Go to Django admin: http://localhost:8000/admin/")
                print(f"   2. Navigate to: Providers → Provider profiles")
                print(f"   3. Find user: {username}")
                print(f"   4. Check ✅ 'Is verified'")
                print(f"   5. Click 'Save'")
                print(f"   6. User should refresh app (tap Refresh button)")
            
        except ProviderProfile.DoesNotExist:
            print(f"❌ No Provider Profile found!")
            print(f"   → User has not completed provider onboarding")
            print(f"   → User needs to tap 'Become a Provider' and complete setup")
            
    except User.DoesNotExist:
        print(f"❌ User not found: {username}")
        print(f"   → Check username spelling")
        print(f"   → User may not exist in database")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python check-user-status.py <username>")
        print("Example: python check-user-status.py hhz")
        sys.exit(1)
    
    username = sys.argv[1]
    check_user(username)
