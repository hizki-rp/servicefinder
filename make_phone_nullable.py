"""
Make phone_number field nullable in UserProfile model.
Run this script to update the field constraint.
"""
import os
import sys
import django

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_api.settings')
django.setup()

from django.db import connection

def make_phone_nullable():
    """Make phone_number field nullable in providers_userprofile table"""
    with connection.cursor() as cursor:
        try:
            # Make phone_number nullable and remove unique constraint
            cursor.execute("""
                ALTER TABLE providers_userprofile 
                ALTER COLUMN phone_number DROP NOT NULL;
            """)
            
            print("✅ Successfully made phone_number nullable in UserProfile")
            
            # Try to drop unique constraint if it exists
            try:
                cursor.execute("""
                    ALTER TABLE providers_userprofile 
                    DROP CONSTRAINT providers_userprofile_phone_number_key;
                """)
                print("✅ Removed unique constraint from phone_number")
            except Exception as e:
                print(f"ℹ️  Unique constraint may not exist or already removed: {e}")
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == '__main__':
    make_phone_nullable()
