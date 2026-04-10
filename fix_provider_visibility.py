"""
Fix provider visibility - ensure all test providers are visible to clients.
Run: python fix_provider_visibility.py
"""
import os
import django
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_api.settings')
os.environ['USE_LOCAL_DB'] = 'false'
django.setup()

from django.utils import timezone
from providers.models import ProviderProfile, ProviderService

print("Fixing provider visibility...")
print()

# Get all provider profiles
profiles = ProviderProfile.objects.all()
print(f"Found {profiles.count()} provider profiles")

fixed_count = 0
for profile in profiles:
    needs_fix = False
    
    # Ensure verification flags are set
    if not profile.national_id_verified:
        profile.national_id_verified = True
        needs_fix = True
    
    if not profile.payment_verified:
        profile.payment_verified = True
        needs_fix = True
    
    if not profile.is_verified:
        profile.is_verified = True
        needs_fix = True
    
    # Ensure trial dates are set
    if not profile.trial_start_date:
        profile.trial_start_date = timezone.now()
        needs_fix = True
    
    if not profile.trial_expiry_date:
        profile.trial_expiry_date = timezone.now() + timedelta(days=30)
        needs_fix = True
    
    if needs_fix:
        profile.save()
        fixed_count += 1
        print(f"✅ Fixed: {profile.user.username}")
    else:
        print(f"✓ OK: {profile.user.username}")

print()
print(f"Fixed {fixed_count} provider profiles")
print()

# Check services
services = ProviderService.objects.all()
print(f"Found {services.count()} services")

service_fixed = 0
for service in services:
    needs_fix = False
    
    # Ensure service is active
    if not service.is_active:
        service.is_active = True
        needs_fix = True
    
    # Ensure verification status is approved
    if service.verification_status != 'approved':
        service.verification_status = 'approved'
        needs_fix = True
    
    # Ensure coordinates exist
    if not service.latitude or not service.longitude:
        # Use provider's coordinates
        try:
            profile = service.provider.provider_profile
            if profile.latitude and profile.longitude:
                service.latitude = profile.latitude
                service.longitude = profile.longitude
                needs_fix = True
        except:
            pass
    
    if needs_fix:
        service.save()
        service_fixed += 1
        print(f"✅ Fixed service: {service.name}")

print()
print(f"Fixed {service_fixed} services")
print()

# Test visibility
print("Testing visibility...")
visible_count = 0
for profile in ProviderProfile.objects.all():
    if profile.is_visible_to_clients:
        visible_count += 1
    else:
        print(f"❌ NOT VISIBLE: {profile.user.username}")
        print(f"   - national_id_verified: {profile.national_id_verified}")
        print(f"   - payment_verified: {profile.payment_verified}")
        print(f"   - is_trial_active: {profile.is_trial_active}")
        print(f"   - trial_expiry_date: {profile.trial_expiry_date}")

print()
print(f"✅ {visible_count}/{profiles.count()} providers are visible to clients")
print()
print("Done! Test the API:")
print("https://servicefinder-fvon.onrender.com/api/providers/services/nearby/?lat=9.03&lng=38.76&radius=50")
