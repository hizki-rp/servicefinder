#!/usr/bin/env python
"""
ServiceFinder Backend Setup Test Script
Run this after migrations to verify everything is working.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_api.settings')
django.setup()

from django.contrib.auth.models import User
from providers.models import (
    ProviderProfile, 
    ProviderService, 
    ProviderVerification,
    CallLog,
    Review
)
from django.contrib.gis.geos import Point
from django.db import connection


def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)


def test_database_connection():
    """Test database connection"""
    print_header("Testing Database Connection")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ Database connection successful")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def test_models_exist():
    """Test that all provider models are accessible"""
    print_header("Testing Provider Models")
    
    models = [
        ('ProviderProfile', ProviderProfile),
        ('ProviderService', ProviderService),
        ('ProviderVerification', ProviderVerification),
        ('CallLog', CallLog),
        ('Review', Review),
    ]
    
    all_good = True
    for name, model in models:
        try:
            count = model.objects.count()
            print(f"✅ {name}: {count} records")
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
            all_good = False
    
    return all_good


def test_create_provider():
    """Test creating a provider with profile and service"""
    print_header("Testing Provider Creation")
    
    try:
        # Check if test user already exists
        username = 'testprovider_setup'
        if User.objects.filter(username=username).exists():
            print(f"⚠️  Test user '{username}' already exists. Skipping creation.")
            user = User.objects.get(username=username)
        else:
            # Create test user
            user = User.objects.create_user(
                username=username,
                email='testprovider@servicefinder.com',
                password='testpass123',
                first_name='Test',
                last_name='Provider'
            )
            print(f"✅ Created test user: {user.username}")
        
        # Create or get provider profile
        profile, created = ProviderProfile.objects.get_or_create(
            user=user,
            defaults={
                'phone_number': '+251911234567',
                'city': 'Addis Ababa',
                'country': 'Ethiopia',
                'location': Point(38.7578, 9.0320)  # Addis Ababa (lng, lat)
            }
        )
        
        if created:
            print(f"✅ Created provider profile: {profile}")
        else:
            print(f"⚠️  Provider profile already exists: {profile}")
        
        # Create test service if not exists
        service_name = 'Test Plumbing Service'
        if not ProviderService.objects.filter(provider=user, name=service_name).exists():
            service = ProviderService.objects.create(
                provider=user,
                name=service_name,
                service_category='Plumber',
                description='Test plumbing service for setup verification.',
                price_type='hourly',
                hourly_rate=500.00,
                location=Point(38.7578, 9.0320),
                city='Addis Ababa',
                country='Ethiopia'
            )
            print(f"✅ Created test service: {service.name}")
        else:
            print(f"⚠️  Test service already exists")
        
        # Create verification request if not exists
        if not ProviderVerification.objects.filter(user=user, verification_type='national_id').exists():
            verification = ProviderVerification.objects.create(
                user=user,
                verification_type='national_id',
                status='pending'
            )
            print(f"✅ Created verification request: {verification}")
        else:
            print(f"⚠️  Verification request already exists")
        
        return True
        
    except Exception as e:
        print(f"❌ Provider creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_business_rules():
    """Test business rules implementation"""
    print_header("Testing Business Rules")
    
    try:
        # Test 3-Service Cap
        username = 'testprovider_setup'
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            profile = user.provider_profile
            
            print(f"📊 Service Count: {profile.services_count}/{profile.max_services_allowed}")
            
            if profile.can_create_service():
                print(f"✅ 3-Service Cap: Provider can create more services")
            else:
                print(f"⚠️  3-Service Cap: Provider has reached limit")
            
            # Test verification status
            print(f"📊 Verification Status:")
            print(f"   - National ID: {'✅' if profile.national_id_verified else '❌'}")
            print(f"   - Payment: {'✅' if profile.payment_verified else '❌'}")
            print(f"   - Fully Verified: {'✅' if profile.is_verified else '❌'}")
            
            return True
        else:
            print("⚠️  No test provider found. Run test_create_provider first.")
            return False
            
    except Exception as e:
        print(f"❌ Business rules test failed: {e}")
        return False


def test_admin_accessible():
    """Check if admin is configured"""
    print_header("Testing Admin Configuration")
    
    try:
        from django.contrib import admin
        from providers.admin import (
            ProviderProfileAdmin,
            ProviderServiceAdmin,
            ProviderVerificationAdmin
        )
        
        # Check if models are registered
        registered_models = [
            ProviderProfile,
            ProviderService,
            ProviderVerification,
            CallLog,
            Review
        ]
        
        all_registered = True
        for model in registered_models:
            if model in admin.site._registry:
                print(f"✅ {model.__name__} registered in admin")
            else:
                print(f"❌ {model.__name__} NOT registered in admin")
                all_registered = False
        
        return all_registered
        
    except Exception as e:
        print(f"❌ Admin configuration test failed: {e}")
        return False


def print_summary(results):
    """Print test summary"""
    print_header("Test Summary")
    
    total = len(results)
    passed = sum(results.values())
    failed = total - passed
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")
    
    if failed == 0:
        print("\n🎉 All tests passed! Backend is ready.")
        print("\nNext steps:")
        print("1. Start server: python manage.py runserver")
        print("2. Access admin: http://localhost:8000/admin/")
        print("3. Test API: http://localhost:8000/api/")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the errors above.")


def main():
    """Run all tests"""
    print("\n" + "🚀 ServiceFinder Backend Setup Test")
    print("="*60)
    
    results = {}
    
    # Run tests
    results['Database Connection'] = test_database_connection()
    results['Models Exist'] = test_models_exist()
    results['Provider Creation'] = test_create_provider()
    results['Business Rules'] = test_business_rules()
    results['Admin Configuration'] = test_admin_accessible()
    
    # Print summary
    print_summary(results)
    
    # Exit with appropriate code
    sys.exit(0 if all(results.values()) else 1)


if __name__ == '__main__':
    main()
