"""
Add is_email_verified field to UserProfile model.
Run this script to add the field without creating a migration.
"""
import os
import sys
import django

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_api.settings')
django.setup()

from django.db import connection

def add_email_verification_field():
    """Add is_email_verified field to providers_userprofile table"""
    with connection.cursor() as cursor:
        try:
            # Check if column exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='providers_userprofile' 
                AND column_name='is_email_verified';
            """)
            
            if cursor.fetchone():
                print("✓ is_email_verified field already exists")
                return
            
            # Add the column
            cursor.execute("""
                ALTER TABLE providers_userprofile 
                ADD COLUMN is_email_verified BOOLEAN DEFAULT FALSE NOT NULL;
            """)
            
            print("✅ Successfully added is_email_verified field to UserProfile")
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == '__main__':
    add_email_verification_field()
