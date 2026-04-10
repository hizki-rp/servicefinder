"""
Manually add missing columns to providers tables.
Run: python fix_is_active_column.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_api.settings')
os.environ['USE_LOCAL_DB'] = 'false'
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    print("Fixing ProviderProfile table...")
    
    # Add is_active column
    try:
        cursor.execute("""
            ALTER TABLE providers_providerprofile 
            ADD COLUMN is_active BOOLEAN DEFAULT TRUE NOT NULL;
        """)
        print("✅ Added is_active column")
    except Exception as e:
        if 'already exists' in str(e):
            print("✓ is_active already exists")
        else:
            print(f"❌ Error: {e}")
    
    # Add suspended_at column
    try:
        cursor.execute("""
            ALTER TABLE providers_providerprofile 
            ADD COLUMN suspended_at TIMESTAMP WITH TIME ZONE NULL;
        """)
        print("✅ Added suspended_at column")
    except Exception as e:
        if 'already exists' in str(e):
            print("✓ suspended_at already exists")
        else:
            print(f"❌ Error: {e}")
    
    # Add suspension_reason column
    try:
        cursor.execute("""
            ALTER TABLE providers_providerprofile 
            ADD COLUMN suspension_reason TEXT DEFAULT '' NOT NULL;
        """)
        print("✅ Added suspension_reason column")
    except Exception as e:
        if 'already exists' in str(e):
            print("✓ suspension_reason already exists")
        else:
            print(f"❌ Error: {e}")
    
    print("\nFixing ProviderService table...")
    
    # Add is_active column to ProviderService
    try:
        cursor.execute("""
            ALTER TABLE providers_providerservice 
            ADD COLUMN is_active BOOLEAN DEFAULT TRUE NOT NULL;
        """)
        print("✅ Added is_active column")
    except Exception as e:
        if 'already exists' in str(e):
            print("✓ is_active already exists")
        else:
            print(f"❌ Error: {e}")
    
    # Add hidden_at column
    try:
        cursor.execute("""
            ALTER TABLE providers_providerservice 
            ADD COLUMN hidden_at TIMESTAMP WITH TIME ZONE NULL;
        """)
        print("✅ Added hidden_at column")
    except Exception as e:
        if 'already exists' in str(e):
            print("✓ hidden_at already exists")
        else:
            print(f"❌ Error: {e}")
    
    # Add hidden_reason column
    try:
        cursor.execute("""
            ALTER TABLE providers_providerservice 
            ADD COLUMN hidden_reason TEXT DEFAULT '' NOT NULL;
        """)
        print("✅ Added hidden_reason column")
    except Exception as e:
        if 'already exists' in str(e):
            print("✓ hidden_reason already exists")
        else:
            print(f"❌ Error: {e}")

print("\n✅ Done! Now run: python manage.py seed_test_data")


