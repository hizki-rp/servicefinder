#!/usr/bin/env python
"""
Quick script to check the status of verification ID 19
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_api.settings')
django.setup()

from providers.models import ProviderVerification

print("=" * 60)
print("VERIFICATION ID 19 - DIAGNOSTIC REPORT")
print("=" * 60)

try:
    verification = ProviderVerification.objects.get(id=19)
    
    print(f"\n✅ Verification Record Found")
    print(f"   ID: {verification.id}")
    print(f"   User: {verification.user.username}")
    print(f"   Type: {verification.verification_type}")
    print(f"   Status: {verification.status}")
    print(f"   Uploaded: {verification.uploaded_at}")
    
    print(f"\n📁 File Information:")
    if verification.file:
        print(f"   ✅ File field has data")
        print(f"   File name: {verification.file.name}")
        print(f"   File URL: {verification.file.url}")
        print(f"   File path: {verification.file.path}")
        
        # Check if file exists on disk
        if os.path.exists(verification.file.path):
            file_size = os.path.getsize(verification.file.path)
            print(f"   ✅ File exists on disk")
            print(f"   File size: {file_size:,} bytes ({file_size / 1024:.2f} KB)")
        else:
            print(f"   ❌ File does NOT exist on disk!")
            print(f"   Expected path: {verification.file.path}")
    else:
        print(f"   ❌ File field is EMPTY!")
        print(f"   This means the file was not saved to the database")
    
    print(f"\n📊 Summary:")
    if verification.file and os.path.exists(verification.file.path):
        print(f"   ✅ Upload was SUCCESSFUL")
        print(f"   ✅ File is stored and accessible")
        print(f"   ℹ️  The null file_url in the response was a serializer context issue")
        print(f"   ℹ️  This has been fixed - next upload will show the URL")
    elif verification.file:
        print(f"   ⚠️  File field has data but file is missing from disk")
        print(f"   ℹ️  Check MEDIA_ROOT configuration and permissions")
    else:
        print(f"   ❌ Upload FAILED - file was not saved")
        print(f"   ℹ️  The FormData might not have been processed correctly")
    
except ProviderVerification.DoesNotExist:
    print(f"\n❌ Verification ID 19 not found in database")
    print(f"   This means the upload did not create a database record")

print("\n" + "=" * 60)
print("END OF REPORT")
print("=" * 60)
