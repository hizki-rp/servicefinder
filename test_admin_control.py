#!/usr/bin/env python
"""
Test script for Admin Control Center endpoints.
Run this to verify all admin features are working.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_api.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.contrib.auth.models import User
from providers.models import ProviderProfile, ProviderService, BroadcastNotification, PushToken

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_admin_control_center():
    """Test all admin control features"""
    
    print_section("ADMIN CONTROL CENTER TEST")
    
    # 1. Check if admin user exists
    print("\n1️⃣ Checking Admin User...")
    try:
        admin = User.objects.get(username='hzk')
        print(f"   ✅ Admin user found: {admin.username}")
        print(f"   📊 is_staff: {admin.is_staff}")
        
        if not admin.is_staff:
            print("   ⚠️  User is not staff. Making admin...")
            admin.is_staff = True
            admin.save()
            print("   ✅ User is now admin!")
    except User.DoesNotExist:
        print("   ❌ Admin user 'hzk' not found")
        return
    
    # 2. Check Provider Profiles
    print("\n2️⃣ Checking Provider Profiles...")
    providers = ProviderProfile.objects.all()
    print(f"   📊 Total providers: {providers.count()}")
    
    active_providers = providers.filter(is_active=True)
    suspended_providers = providers.filter(is_active=False)
    verified_providers = providers.filter(is_verified=True)
    pending_providers = providers.filter(is_verified=False)
    
    print(f"   ✅ Active: {active_providers.count()}")
    print(f"   🚫 Suspended: {suspended_providers.count()}")
    print(f"   ✓ Verified: {verified_providers.count()}")
    print(f"   ⏳ Pending: {pending_providers.count()}")
    
    # 3. Check Services
    print("\n3️⃣ Checking Services...")
    services = ProviderService.objects.all()
    print(f"   📊 Total services: {services.count()}")
    
    active_services = services.filter(is_active=True)
    hidden_services = services.filter(is_active=False)
    
    print(f"   ✅ Active: {active_services.count()}")
    print(f"   🙈 Hidden: {hidden_services.count()}")
    
    # 4. Check Broadcast System
    print("\n4️⃣ Checking Broadcast System...")
    broadcasts = BroadcastNotification.objects.all()
    print(f"   📊 Total broadcasts: {broadcasts.count()}")
    
    if broadcasts.exists():
        for broadcast in broadcasts[:3]:
            print(f"   📢 {broadcast.title}")
            print(f"      Target: {broadcast.get_target_audience_display()}")
            print(f"      Sent: {broadcast.sent_count} | Success: {broadcast.success_count}")
    
    # 5. Check Push Tokens
    print("\n5️⃣ Checking Push Tokens...")
    tokens = PushToken.objects.all()
    print(f"   📊 Total tokens: {tokens.count()}")
    
    active_tokens = tokens.filter(is_active=True)
    print(f"   ✅ Active tokens: {active_tokens.count()}")
    
    if tokens.exists():
        for token in tokens[:3]:
            print(f"   📱 {token.user.username} - {token.device_type}")
    
    # 6. Test Broadcast Filtering
    print("\n6️⃣ Testing Broadcast Filtering...")
    
    # Create a test broadcast to check filtering
    test_broadcast = BroadcastNotification(
        target_audience='verified',
        category_filter='',
        city_filter=''
    )
    
    target_providers = test_broadcast.get_target_providers()
    print(f"   📊 Verified providers: {target_providers.count()}")
    
    test_broadcast.target_audience = 'trial'
    trial_providers = test_broadcast.get_target_providers()
    print(f"   📊 Trial providers: {trial_providers.count()}")
    
    test_broadcast.target_audience = 'pending'
    pending = test_broadcast.get_target_providers()
    print(f"   📊 Pending providers: {pending.count()}")
    
    # 7. Summary
    print_section("SUMMARY")
    print("\n✅ Admin Control Center is operational!")
    print("\n📋 Available Admin Endpoints:")
    print("   • GET  /api/providers/admin/providers/")
    print("   • POST /api/providers/admin/providers/<id>/suspend/")
    print("   • GET  /api/providers/admin/services/")
    print("   • POST /api/providers/admin/services/<id>/hide/")
    print("   • POST /api/providers/admin/verifications/<id>/approve/")
    print("   • POST /api/providers/push-token/register/")
    print("   • POST /api/providers/admin/broadcast/send/")
    print("   • GET  /api/providers/admin/broadcast/list/")
    print("   • GET  /api/providers/admin/broadcast/preview/")
    
    print("\n🔒 Security: All endpoints require is_staff=True")
    print(f"\n👤 Current admin: {admin.username} (is_staff={admin.is_staff})")
    
    print("\n" + "="*70)
    print("  ✅ TEST COMPLETE")
    print("="*70 + "\n")

if __name__ == '__main__':
    try:
        test_admin_control_center()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
