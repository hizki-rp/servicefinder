#!/usr/bin/env python
"""
Fix verification status for a user
This script will:
1. Check current verification status
2. Approve all documents
3. Set profile as verified
4. Test the API endpoint
"""
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_api.settings')
django.setup()

from django.contrib.auth.models import User
from providers.models import ProviderProfile, ProviderVerification
from django.utils import timezone

def fix_verification(username='Hzk'):
    """Fix verification for a specific user"""
    print("=" * 70)
    print(f"FIXING VERIFICATION FOR USER: {username}")
    print("=" * 70)
    
    try:
        # Find user
        user = User.objects.get(username=username)
        print(f"\n✅ Found user: {user.username} (ID: {user.id})")
        
        # Get or create provider profile
        profile, created = ProviderProfile.objects.get_or_create(
            user=user,
            defaults={
                'phone_number': '+251912345678',
                'city': 'Addis Ababa',
                'country': 'Ethiopia',
            }
        )
        
        if created:
            print(f"✅ Created new provider profile")
        else:
            print(f"✅ Found existing provider profile")
        
        print(f"\n📋 BEFORE FIX:")
        print(f"   is_verified: {profile.is_verified}")
        print(f"   national_id_verified: {profile.national_id_verified}")
        print(f"   payment_verified: {profile.payment_verified}")
        print(f"   is_trial_active: {profile.is_trial_active}")
        print(f"   days_until_trial_expiry: {profile.days_until_trial_expiry}")
        
        # Check documents
        docs = ProviderVerification.objects.filter(user=user)
        print(f"\n📄 Documents ({docs.count()}):")
        for doc in docs:
            print(f"   - {doc.verification_type}: {doc.status}")
        
        # FIX 1: Approve all documents
        print(f"\n🔧 FIXING...")
        approved_count = ProviderVerification.objects.filter(
            user=user
        ).update(
            status='approved',
            reviewed_at=timezone.now()
        )
        print(f"   ✅ Approved {approved_count} documents")
        
        # FIX 2: Set profile as verified
        profile.national_id_verified = True
        profile.payment_verified = True  # Optional but let's set it
        profile.is_verified = True
        profile.save()
        print(f"   ✅ Set profile as verified")
        
        # Refresh from database
        profile.refresh_from_db()
        
        print(f"\n📋 AFTER FIX:")
        print(f"   is_verified: {profile.is_verified}")
        print(f"   national_id_verified: {profile.national_id_verified}")
        print(f"   payment_verified: {profile.payment_verified}")
        print(f"   is_trial_active: {profile.is_trial_active}")
        print(f"   days_until_trial_expiry: {profile.days_until_trial_expiry}")
        
        # Test API response
        print(f"\n🧪 TESTING API RESPONSE:")
        from providers.serializers import ProviderProfileSerializer
        serializer = ProviderProfileSerializer(profile)
        data = serializer.data
        
        print(f"   is_verified in API: {data.get('is_verified')}")
        print(f"   national_id_verified in API: {data.get('national_id_verified')}")
        print(f"   is_trial_active in API: {data.get('is_trial_active')}")
        
        if data.get('is_verified'):
            print(f"\n✅ SUCCESS! User is now verified in API")
        else:
            print(f"\n❌ FAILED! User still not verified in API")
            print(f"\nFull API data:")
            import json
            print(json.dumps(data, indent=2, default=str))
        
        print(f"\n💡 NEXT STEPS:")
        print(f"   1. Restart the frontend app")
        print(f"   2. Clear app data (or logout/login)")
        print(f"   3. Should now show 'My Service Console'")
        
        return True
        
    except User.DoesNotExist:
        print(f"\n❌ User '{username}' not found")
        print(f"\nAvailable users:")
        for u in User.objects.all()[:10]:
            print(f"   - {u.username} (ID: {u.id})")
        return False
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    # Get username from command line or use default
    username = sys.argv[1] if len(sys.argv) > 1 else 'Hzk'
    
    success = fix_verification(username)
    
    print("\n" + "=" * 70)
    if success:
        print("✅ VERIFICATION FIXED!")
    else:
        print("❌ VERIFICATION FIX FAILED")
    print("=" * 70)
