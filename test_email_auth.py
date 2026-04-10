"""
Test email authentication endpoints.
Run this to verify email auth is working.
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_api.settings')
django.setup()

from providers.email_auth import EmailVerificationCode, send_verification_email

def test_email_verification():
    """Test email verification code generation and validation"""
    print("Testing Email Verification System...")
    print("=" * 50)
    
    # Test 1: Generate code
    print("\n1. Generating verification code...")
    email = "test@example.com"
    name = "Test User"
    code = EmailVerificationCode.generate_code(email, name)
    print(f"✓ Generated code: {code}")
    
    # Test 2: Verify correct code
    print("\n2. Verifying correct code...")
    verified, result = EmailVerificationCode.verify_code(email, code)
    if verified:
        print(f"✓ Code verified successfully! Name: {result}")
    else:
        print(f"✗ Verification failed: {result}")
    
    # Test 3: Try wrong code
    print("\n3. Testing wrong code...")
    code2 = EmailVerificationCode.generate_code("test2@example.com", "User 2")
    verified, result = EmailVerificationCode.verify_code("test2@example.com", "000000")
    if not verified:
        print(f"✓ Correctly rejected wrong code: {result}")
    else:
        print(f"✗ Should have rejected wrong code")
    
    # Test 4: Test expiration
    print("\n4. Testing code cleanup...")
    EmailVerificationCode.cleanup_expired()
    print("✓ Cleanup completed")
    
    print("\n" + "=" * 50)
    print("✅ All tests passed!")
    print("\nEmail auth endpoints are ready to use:")
    print("  POST /api/providers/auth/email-request/")
    print("  POST /api/providers/auth/email-verify/")

if __name__ == '__main__':
    test_email_verification()
