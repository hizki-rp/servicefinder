#!/usr/bin/env python
"""
Fix provider verification status
Usage: python fix-provider-status.py <username>
Run from backend directory: cd backend && python fix-provider-status.py hhz
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from providers.models import ProviderProfile

def fix_provider(username):
    print(f"\n{'='*60}")
    print(f"Fixing provider status for: {username}")
    print(f"{'='*60}\n")
    
    try:
        user = User.objects.get(username=username)
        print(f"✅ User found: {user.username}")
        
        try:
            profile = ProviderProfile.objects.get(user=user)
            print(f"✅ Provider Profile found\n")
            
            print(f"Current status:")
            print(f"   - Is Verified: {profile.is_verified}")
            print(f"   - National ID Verified: {profile.national_id_verified}")
            print(f"   - Payment Verified: {profile.payment_verified}")
            print()
            
            # Fix verification status
            if not profile.is_verified:
                profile.is_verified = True
                print(f"🔧 Setting is_verified = True")
            
            if not profile.national_id_verified:
                profile.national_id_verified = True
                print(f"🔧 Setting national_id_verified = True")
            
            # Save changes
            profile.save()
            print(f"\n✅ Provider status updated!")
            print()
            print(f"New status:")
            print(f"   - Is Verified: {profile.is_verified}")
            print(f"   - National ID Verified: {profile.national_id_verified}")
            print(f"   - Payment Verified: {profile.payment_verified}")
            print()
            print(f"📱 Tell user to:")
            print(f"   1. Go to Dashboard tab")
            print(f"   2. Tap Refresh button (🔄)")
            print(f"   3. Status should update to 'Verified'")
            
        except ProviderProfile.DoesNotExist:
            print(f"❌ No Provider Profile found!")
            print(f"   → User needs to complete provider onboarding first")
            
    except User.DoesNotExist:
        print(f"❌ User not found: {username}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python fix-provider-status.py <username>")
        print("Example: python fix-provider-status.py hhz")
        sys.exit(1)
    
    username = sys.argv[1]
    fix_provider(username)
