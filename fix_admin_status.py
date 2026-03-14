#!/usr/bin/env python
"""
Fix admin status for user.
Makes the specified user a staff member and superuser.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_api.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.contrib.auth.models import User

def fix_admin_status(username):
    """Make user admin"""
    print("\n" + "="*70)
    print(f"  FIXING ADMIN STATUS FOR: {username}")
    print("="*70)
    
    try:
        user = User.objects.get(username=username)
        print(f"\n✅ Found user: {user.username} (ID: {user.id})")
        
        print(f"\n📋 BEFORE:")
        print(f"   is_staff: {user.is_staff}")
        print(f"   is_superuser: {user.is_superuser}")
        print(f"   is_active: {user.is_active}")
        
        # Make admin
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()
        
        print(f"\n📋 AFTER:")
        print(f"   is_staff: {user.is_staff}")
        print(f"   is_superuser: {user.is_superuser}")
        print(f"   is_active: {user.is_active}")
        
        print("\n" + "="*70)
        print("  ✅ ADMIN STATUS FIXED!")
        print("="*70)
        print("\n💡 NEXT STEPS:")
        print("   1. Logout from the app")
        print("   2. Login again")
        print("   3. Admin tab (🛡️) should now appear")
        print("\n")
        
    except User.DoesNotExist:
        print(f"\n❌ User '{username}' not found")
        print("\nAvailable users:")
        for u in User.objects.all()[:10]:
            print(f"   - {u.username} (staff={u.is_staff}, super={u.is_superuser})")
        print("\n")

if __name__ == '__main__':
    username = sys.argv[1] if len(sys.argv) > 1 else 'admin'
    fix_admin_status(username)
