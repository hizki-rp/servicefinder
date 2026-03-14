#!/usr/bin/env python
"""
Quick approval script for user 'hizkk'
Run: python approve_hizkk.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_api.settings')
django.setup()

from providers.models import ProviderProfile
from django.contrib.auth.models import User

def approve_hizkk():
    """Approve user hizkk as verified provider"""
    
    print("\n" + "=" * 60)
    print(" " * 15 + "APPROVE HIZKK")
    print("=" * 60)
    
    try:
        # Get user
        user = User.objects.get(username='hizkk')
        print(f"\n✅ Found user: {user.username} (ID: {user.id})")
        
        try:
            # Get provider profile
            profile = ProviderProfile.objects.get(user=user)
            
            print(f"\n📋 Current Status:")
            print(f"   is_verified: {profile.is_verified}")
            print(f"   has_national_id: {profile.has_national_id}")
            print(f"   phone_number: {profile.phone_number}")
            print(f"   city: {profile.city}")
            
            if profile.is_verified:
                print("\n⚠️  User is already verified!")
                print("   No changes needed.")
            else:
                # Approve
                profile.is_verified = True
                profile.save()
                
                print("\n✅ SUCCESS! User approved!")
                print(f"   is_verified: {profile.is_verified}")
                
                print("\n📝 Next Steps:")
                print("   1. User 'hizkk' should pull-to-refresh Dashboard")
                print("   2. Or use Diagnostic Tool → Force Sync")
                print("   3. Green 'Verified' banner should appear")
                print("   4. 'Add Service' button should be visible")
                
        except ProviderProfile.DoesNotExist:
            print("\n❌ ERROR: No provider profile found for hizkk")
            print("   User needs to complete onboarding first")
            
    except User.DoesNotExist:
        print("\n❌ ERROR: User 'hizkk' not found")
        print("   User needs to register first")
    
    print("\n" + "=" * 60 + "\n")

if __name__ == '__main__':
    try:
        approve_hizkk()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
