#!/usr/bin/env python
"""
Create a test provider for testing admin dashboard.
Run: python backend/create_test_provider.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_api.settings')
django.setup()

from django.contrib.auth.models import User
from providers.models import ProviderProfile, UserProfile
import random

def create_test_provider():
    """Create a test provider with pending verification status"""
    
    print("=" * 60)
    print("🔧 CREATING TEST PROVIDER")
    print("=" * 60)
    
    # Generate unique username
    counter = 1
    username = f"testprovider{counter}"
    while User.objects.filter(username=username).exists():
        counter += 1
        username = f"testprovider{counter}"
    
    # Create user
    user = User.objects.create_user(
        username=username,
        password='test123456',
        first_name='Test',
        last_name='Provider',
        email=f'{username}@test.com'
    )
    
    print(f"\n✅ Created user: {username}")
    print(f"   Password: test123456")
    
    # Create UserProfile if needed
    user_profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'phone_number': f'091234{random.randint(1000, 9999)}',
            'is_email_verified': True
        }
    )
    
    if created:
        print(f"✅ Created UserProfile")
    
    # Create ProviderProfile (unverified)
    cities = ['Addis Ababa', 'Dire Dawa', 'Mekelle', 'Bahir Dar', 'Hawassa']
    city = random.choice(cities)
    
    provider = ProviderProfile.objects.create(
        user=user,
        phone_number=user_profile.phone_number,
        city=city,
        country='Ethiopia',
        latitude=9.0 + random.random(),
        longitude=38.7 + random.random(),
        is_verified=False,  # This makes it show in pending list
        national_id_verified=False,
        payment_verified=False
    )
    
    print(f"✅ Created ProviderProfile")
    print(f"   City: {city}")
    print(f"   Phone: {user_profile.phone_number}")
    print(f"   Status: PENDING VERIFICATION")
    
    print(f"\n" + "=" * 60)
    print(f"📋 TEST PROVIDER DETAILS")
    print("=" * 60)
    print(f"\n   Username: {username}")
    print(f"   Password: test123456")
    print(f"   Name: {user.get_full_name()}")
    print(f"   Email: {user.email}")
    print(f"   Phone: {user_profile.phone_number}")
    print(f"   City: {city}")
    print(f"   Verified: {provider.is_verified}")
    
    print(f"\n" + "=" * 60)
    print(f"🎯 WHAT TO DO NEXT")
    print("=" * 60)
    print(f"\n1. Log in to admin account:")
    print(f"   Username: admin")
    print(f"   Password: MertAdmin2024!")
    
    print(f"\n2. Go to Profile tab → 👑 Admin Dashboard")
    
    print(f"\n3. You should see '{username}' in pending list")
    
    print(f"\n4. Tap Approve to verify the provider")
    
    print(f"\n5. (Optional) Log in as test provider to see verified status:")
    print(f"   Username: {username}")
    print(f"   Password: test123456")
    
    print(f"\n" + "=" * 60)
    print(f"✅ TEST PROVIDER CREATED SUCCESSFULLY")
    print("=" * 60)

if __name__ == '__main__':
    create_test_provider()
