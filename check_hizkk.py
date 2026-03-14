#!/usr/bin/env python
"""
Quick status check for user 'hizkk'
Run: python check_hizkk.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_api.settings')
django.setup()

from providers.models import ProviderProfile, ProviderService
from django.contrib.auth.models import User

def check_hizkk():
    """Check complete status of user hizkk"""
    
    print("\n" + "=" * 60)
    print(" " * 15 + "HIZKK STATUS CHECK")
    print("=" * 60)
    
    try:
        # Get user
        user = User.objects.get(username='hizkk')
        
        print("\n📱 USER ACCOUNT")
        print("-" * 60)
        print(f"  ID: {user.id}")
        print(f"  Username: {user.username}")
        print(f"  Email: {user.email or 'Not set'}")
        print(f"  Is Staff: {'✅ Yes' if user.is_staff else '❌ No'}")
        print(f"  Is Active: {'✅ Yes' if user.is_active else '❌ No'}")
        print(f"  Date Joined: {user.date_joined.strftime('%Y-%m-%d %H:%M')}")
        
        try:
            # Get provider profile
            profile = ProviderProfile.objects.get(user=user)
            
            print("\n💼 PROVIDER PROFILE")
            print("-" * 60)
            print(f"  Is Verified: {'✅ TRUE' if profile.is_verified else '❌ FALSE'}")
            print(f"  Has National ID: {'✅ Yes' if profile.has_national_id else '❌ No'}")
            print(f"  Has Payment Proof: {'✅ Yes' if profile.has_payment_proof else '❌ No'}")
            print(f"  Phone: {profile.phone_number or 'Not set'}")
            print(f"  City: {profile.city or 'Not set'}")
            print(f"  Max Services: {profile.max_services_allowed}")
            print(f"  Rating: {profile.rating or 'No ratings yet'}")
            print(f"  Total Reviews: {profile.total_reviews}")
            
            # Trial info
            if profile.trial_start_date:
                print(f"\n🎉 TRIAL STATUS")
                print("-" * 60)
                print(f"  Start Date: {profile.trial_start_date.strftime('%Y-%m-%d')}")
                print(f"  Expiry Date: {profile.trial_expiry_date.strftime('%Y-%m-%d')}")
                
                from datetime import datetime
                now = datetime.now().date()
                expiry = profile.trial_expiry_date
                days_left = (expiry - now).days
                
                if days_left > 0:
                    print(f"  Days Remaining: {days_left} days")
                    print(f"  Status: ✅ Active")
                else:
                    print(f"  Status: ❌ Expired")
            
            # Get services
            services = ProviderService.objects.filter(provider=profile)
            
            print(f"\n📋 SERVICES ({services.count()}/{profile.max_services_allowed})")
            print("-" * 60)
            
            if services.exists():
                for i, service in enumerate(services, 1):
                    print(f"\n  {i}. {service.name}")
                    print(f"     Category: {service.service_category}")
                    print(f"     Price: {service.price} ETB")
                    print(f"     Description: {service.description[:50]}...")
                    print(f"     Created: {service.created_at.strftime('%Y-%m-%d %H:%M')}")
            else:
                print("  No services yet")
            
            # Status summary
            print("\n" + "=" * 60)
            print(" " * 20 + "STATUS SUMMARY")
            print("=" * 60)
            
            can_create = False
            issues = []
            
            if not profile.is_verified:
                issues.append("❌ NOT VERIFIED - Cannot create services")
                issues.append("   Fix: Approve in Django admin or Admin tab")
            elif services.count() >= profile.max_services_allowed:
                issues.append(f"⚠️  SERVICE LIMIT REACHED ({services.count()}/{profile.max_services_allowed})")
                issues.append("   Fix: Delete a service or increase max_services_allowed")
            else:
                can_create = True
            
            if can_create:
                print("\n✅ READY TO CREATE SERVICES")
                print(f"   Can add {profile.max_services_allowed - services.count()} more service(s)")
                print("\n📝 Next Steps:")
                print("   1. Login as hizkk in the app")
                print("   2. Go to Dashboard tab")
                print("   3. Tap 'Add Service' button")
                print("   4. Fill form and submit")
            else:
                print("\n❌ CANNOT CREATE SERVICES")
                for issue in issues:
                    print(f"   {issue}")
            
            # API endpoint info
            print("\n" + "=" * 60)
            print(" " * 18 + "API VERIFICATION")
            print("=" * 60)
            print("\nTo verify via API, use:")
            print(f"\n  curl -H 'Authorization: Bearer {{token}}' \\")
            print(f"       http://localhost:8000/api/providers/user-status/")
            print("\nExpected response:")
            print(f"  is_provider: true")
            print(f"  provider_profile.is_verified: {str(profile.is_verified).lower()}")
            print(f"  provider_profile.max_services_allowed: {profile.max_services_allowed}")
            
        except ProviderProfile.DoesNotExist:
            print("\n❌ NO PROVIDER PROFILE FOUND")
            print("-" * 60)
            print("  User 'hizkk' exists but has no provider profile")
            print("\n📝 Next Steps:")
            print("   1. Login as hizkk in the app")
            print("   2. Complete provider onboarding")
            print("   3. Upload National ID")
            print("   4. Wait for admin approval")
            
    except User.DoesNotExist:
        print("\n❌ USER 'hizkk' NOT FOUND")
        print("-" * 60)
        print("  No user with username 'hizkk' exists in database")
        print("\n📝 Next Steps:")
        print("   1. Register user 'hizkk' via OTP")
        print("   2. Complete provider onboarding")
        print("   3. Wait for admin approval")
    
    print("\n" + "=" * 60 + "\n")

if __name__ == '__main__':
    try:
        check_hizkk()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
