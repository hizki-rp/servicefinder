"""
Fix script to create UserProfile for existing users who don't have one.
Run this on Render to fix the user 'hz' and any other users without profiles.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_api.settings')
django.setup()

from django.contrib.auth.models import User
from providers.models import UserProfile

def fix_user_profiles():
    """Create UserProfile for all users who don't have one"""
    users_without_profile = []
    
    for user in User.objects.all():
        if not hasattr(user, 'user_profile'):
            users_without_profile.append(user)
            # Create UserProfile with email verified if they have an email
            UserProfile.objects.create(
                user=user,
                is_email_verified=bool(user.email),  # True if they have an email
            )
            print(f"✅ Created UserProfile for user: {user.username} (email: {user.email})")
    
    if not users_without_profile:
        print("✅ All users already have UserProfile")
    else:
        print(f"\n✅ Fixed {len(users_without_profile)} users")

if __name__ == '__main__':
    fix_user_profiles()
