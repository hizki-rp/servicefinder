#!/usr/bin/env python
"""
Quick script to check user verification status in database
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_api.settings')
django.setup()

from django.contrib.auth.models import User
from providers.models import ProviderProfile, ProviderVerification

print("=" * 60)
print("USER VERIFICATION STATUS CHECK")
print("=" * 60)

# Find the user (adjust username as needed)
try:
    user = User.objects.get(username='Hzk')
    print(f"\n✅ Found user: {user.username}")
    print(f"   Email: {user.email}")
    print(f"   ID: {user.id}")
    
    # Check provider profile
    try:
        profile = ProviderProfile.objects.get(user=user)
        print(f"\n📋 Provider Profile:")
        print(f"   is_verified: {profile.is_verified}")
        print(f"   national_id_verified: {profile.national_id_verified}")
        print(f"   payment_verified: {profile.payment_verified}")
        print(f"   is_trial_active: {profile.is_trial_active}")
        print(f"   days_until_trial_expiry: {profile.days_until_trial_expiry}")
        print(f"   services_count: {profile.services_count}")
        
        # Check verification documents
        print(f"\n📄 Verification Documents:")
        docs = ProviderVerification.objects.filter(user=user)
        if docs.exists():
            for doc in docs:
                print(f"   - {doc.verification_type}: {doc.status}")
                print(f"     Uploaded: {doc.uploaded_at}")
                if doc.reviewed_at:
                    print(f"     Reviewed: {doc.reviewed_at}")
        else:
            print("   No documents uploaded")
            
        # Recommendation
        print(f"\n💡 Recommendation:")
        if not profile.is_verified:
            if not profile.national_id_verified:
                print("   ❌ National ID not verified - approve in Django Admin")
            elif not profile.is_trial_active and not profile.payment_verified:
                print("   ❌ Trial expired and no payment - need payment proof")
            else:
                print("   ⚠️  Profile should be verified but isn't - check signals")
        else:
            print("   ✅ Profile is verified - should work in app")
            
    except ProviderProfile.DoesNotExist:
        print(f"\n❌ No provider profile found for {user.username}")
        print("   User needs to complete onboarding")
        
except User.DoesNotExist:
    print("\n❌ User 'Hzk' not found")
    print("\nAvailable users:")
    for u in User.objects.all()[:10]:
        print(f"   - {u.username} (ID: {u.id})")

print("\n" + "=" * 60)
