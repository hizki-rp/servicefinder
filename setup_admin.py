#!/usr/bin/env python
"""
Quick script to set up admin user with proper permissions.
Run: python setup_admin.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_api.settings')
django.setup()

from django.contrib.auth.models import User

def setup_admin():
    """Create or update admin user with proper permissions"""
    
    username = 'admin'
    password = 'MertAdmin2024!'
    email = 'admin@mertservice.com'
    
    try:
        # Try to get existing admin
        admin = User.objects.get(username=username)
        print(f"✅ Found existing admin user: {username}")
        
        # Update permissions
        admin.is_staff = True
        admin.is_superuser = True
        admin.is_active = True
        admin.email = email
        admin.set_password(password)
        admin.save()
        
        print(f"✅ Updated admin permissions:")
        print(f"   - is_staff: {admin.is_staff}")
        print(f"   - is_superuser: {admin.is_superuser}")
        print(f"   - is_active: {admin.is_active}")
        
    except User.DoesNotExist:
        # Create new admin
        admin = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print(f"✅ Created new admin user: {username}")
        print(f"   - is_staff: {admin.is_staff}")
        print(f"   - is_superuser: {admin.is_superuser}")
    
    print(f"\n📋 Admin Credentials:")
    print(f"   Username: {username}")
    print(f"   Password: {password}")
    print(f"\n🔐 Next Steps:")
    print(f"   1. Restart Expo: npx expo start -c")
    print(f"   2. Log out of app")
    print(f"   3. Log in with admin credentials")
    print(f"   4. Go to Profile tab")
    print(f"   5. Look for '👑 Admin Dashboard' button")

if __name__ == '__main__':
    setup_admin()
