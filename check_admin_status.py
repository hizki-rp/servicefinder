#!/usr/bin/env python
"""
Quick diagnostic script to check admin user status.
Run: python backend/check_admin_status.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_api.settings')
django.setup()

from django.contrib.auth.models import User
from providers.models import ProviderProfile

def check_admin_status():
    """Check if admin user exists and has correct permissions"""
    
    print("=" * 60)
    print("🔍 ADMIN STATUS CHECK")
    print("=" * 60)
    
    # Check if admin user exists
    try:
        admin = User.objects.get(username='admin')
        print(f"\n✅ Admin user found: {admin.username}")
        print(f"\n📋 Permissions:")
        print(f"   is_staff: {admin.is_staff} {'✅' if admin.is_staff else '❌ MUST BE TRUE'}")
        print(f"   is_superuser: {admin.is_superuser} {'✅' if admin.is_superuser else '❌ MUST BE TRUE'}")
        print(f"   is_active: {admin.is_active} {'✅' if admin.is_active else '❌ MUST BE TRUE'}")
        print(f"   email: {admin.email}")
        
        if not admin.is_staff or not admin.is_superuser:
            print(f"\n⚠️  WARNING: Admin user doesn't have correct permissions!")
            print(f"   Run: python backend/setup_admin.py")
        else:
            print(f"\n✅ Admin permissions are correct!")
            
    except User.DoesNotExist:
        print(f"\n❌ Admin user NOT found!")
        print(f"   Run: python backend/setup_admin.py")
        return
    
    # Check pending providers
    print(f"\n" + "=" * 60)
    print(f"📋 PENDING PROVIDERS")
    print("=" * 60)
    
    pending = ProviderProfile.objects.filter(is_verified=False)
    print(f"\nTotal pending: {pending.count()}")
    
    if pending.count() == 0:
        print(f"\n✅ No pending providers (admin dashboard will be empty)")
        print(f"\n💡 To test admin dashboard, create a test provider:")
        print(f"   python backend/create_test_provider.py")
    else:
        print(f"\n📋 Pending providers:")
        for p in pending:
            print(f"\n   👤 {p.user.username}")
            print(f"      Name: {p.user.get_full_name() or p.user.first_name or 'N/A'}")
            print(f"      Phone: {p.phone_number}")
            print(f"      City: {p.city}")
            print(f"      Created: {p.created_at.strftime('%Y-%m-%d %H:%M')}")
            print(f"      Selfie: {'✅' if p.selfie_image else '❌'}")
            print(f"      ID Image: {'✅' if p.id_image else '❌'}")
    
    # Check verified providers
    verified = ProviderProfile.objects.filter(is_verified=True)
    print(f"\n" + "=" * 60)
    print(f"✅ VERIFIED PROVIDERS")
    print("=" * 60)
    print(f"\nTotal verified: {verified.count()}")
    
    if verified.count() > 0:
        for p in verified[:5]:  # Show first 5
            print(f"   ✅ {p.user.username} ({p.city})")
    
    # Summary
    print(f"\n" + "=" * 60)
    print(f"📊 SUMMARY")
    print("=" * 60)
    print(f"\n✅ Admin user: {'EXISTS' if admin else 'NOT FOUND'}")
    if admin:
        print(f"✅ Admin permissions: {'CORRECT' if (admin.is_staff and admin.is_superuser) else 'INCORRECT'}")
    print(f"✅ Pending providers: {pending.count()}")
    print(f"✅ Verified providers: {verified.count()}")
    
    print(f"\n" + "=" * 60)
    print(f"🔐 ADMIN CREDENTIALS")
    print("=" * 60)
    print(f"\n   Username: admin")
    print(f"   Password: MertAdmin2024!")
    
    print(f"\n" + "=" * 60)
    print(f"🚀 NEXT STEPS")
    print("=" * 60)
    
    if not admin or not admin.is_staff or not admin.is_superuser:
        print(f"\n1. Fix admin permissions:")
        print(f"   python backend/setup_admin.py")
    else:
        print(f"\n1. ✅ Admin permissions are correct")
    
    print(f"\n2. Clear Expo cache:")
    print(f"   npx expo start -c")
    
    print(f"\n3. Log out and log in again with admin credentials")
    
    print(f"\n4. Check for 👑 Admin Dashboard button in Profile tab")
    
    if pending.count() == 0:
        print(f"\n5. Create test provider to see admin dashboard in action:")
        print(f"   python backend/create_test_provider.py")
    
    print(f"\n" + "=" * 60)

if __name__ == '__main__':
    check_admin_status()
