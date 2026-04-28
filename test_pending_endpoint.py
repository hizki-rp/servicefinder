#!/usr/bin/env python
"""
Test the pending verifications endpoint directly
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_api.settings')
django.setup()

from providers.models import ProviderVerification
from django.contrib.auth.models import User

print("=" * 60)
print("🧪 Testing Pending Verifications Endpoint")
print("=" * 60)

# Check pending verifications
pending = ProviderVerification.objects.filter(status='pending')
print(f"\n📋 Total pending verifications: {pending.count()}")

for v in pending[:5]:  # Show first 5
    print(f"\n  ID: {v.id}")
    print(f"  Type: {v.verification_type}")
    print(f"  User: {v.user.username if v.user else 'NO USER'}")
    print(f"  File: {'YES' if v.file else 'NO FILE'}")
    
    # Check provider profile
    if v.user:
        try:
            profile = v.user.provider_profile
            print(f"  Provider Profile: YES (ID: {profile.id})")
        except Exception as e:
            print(f"  Provider Profile: NO ({str(e)})")

print("\n" + "=" * 60)
print("✅ Test complete")
print("=" * 60)
