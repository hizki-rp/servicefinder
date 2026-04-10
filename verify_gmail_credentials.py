"""
Verify Gmail SMTP credentials directly.
This will tell you exactly what's wrong with your Gmail setup.
"""
import os
import sys
import django
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_api.settings')
django.setup()

from django.conf import settings
import smtplib

def verify_gmail_credentials():
    """Verify Gmail SMTP credentials"""
    print("=" * 60)
    print("GMAIL CREDENTIALS VERIFICATION")
    print("=" * 60)
    
    # Show current settings
    email_user = settings.EMAIL_HOST_USER
    email_pass = settings.EMAIL_HOST_PASSWORD
    email_host = settings.EMAIL_HOST
    email_port = settings.EMAIL_PORT
    
    print(f"\n📧 Current Settings:")
    print(f"   EMAIL_HOST: {email_host}")
    print(f"   EMAIL_PORT: {email_port}")
    print(f"   EMAIL_HOST_USER: {email_user}")
    print(f"   EMAIL_HOST_PASSWORD: {email_pass[:4]}{'*' * (len(email_pass) - 4) if len(email_pass) > 4 else '****'}")
    print(f"   Password Length: {len(email_pass)} characters")
    
    # Check for spaces
    if ' ' in email_pass:
        print(f"\n❌ ERROR: Password contains {email_pass.count(' ')} space(s)!")
        print(f"   Gmail app passwords should be 16 characters with NO spaces")
        print(f"   Current: '{email_pass}'")
        print(f"   Should be: '{email_pass.replace(' ', '')}'")
        return False
    
    # Check password length
    if len(email_pass) != 16:
        print(f"\n⚠️  WARNING: Password length is {len(email_pass)}, expected 16")
        print(f"   Gmail app passwords are always 16 characters")
    
    # Test SMTP connection
    print(f"\n🔍 Testing SMTP connection...")
    try:
        server = smtplib.SMTP(email_host, email_port, timeout=10)
        print(f"   ✅ Connected to {email_host}:{email_port}")
        
        server.starttls()
        print(f"   ✅ TLS enabled")
        
        server.login(email_user, email_pass)
        print(f"   ✅ Authentication successful!")
        
        server.quit()
        print(f"\n✅ ALL CHECKS PASSED!")
        print(f"   Gmail credentials are correct and working")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ AUTHENTICATION FAILED!")
        print(f"   Error: {str(e)}")
        print(f"\n🔧 Possible fixes:")
        print(f"   1. Generate a NEW app password at:")
        print(f"      https://myaccount.google.com/apppasswords")
        print(f"   2. Make sure you're signed in as: {email_user}")
        print(f"   3. Make sure 2FA is enabled on the account")
        print(f"   4. Copy the new password WITHOUT spaces")
        print(f"   5. Update Render environment variable:")
        print(f"      EMAIL_HOST_PASSWORD=your_new_password_no_spaces")
        return False
        
    except smtplib.SMTPConnectError as e:
        print(f"\n❌ CONNECTION FAILED!")
        print(f"   Error: {str(e)}")
        print(f"   Cannot connect to {email_host}:{email_port}")
        return False
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR!")
        print(f"   Error: {str(e)}")
        print(f"   Type: {type(e).__name__}")
        return False

if __name__ == '__main__':
    print("\n")
    success = verify_gmail_credentials()
    print("\n" + "=" * 60)
    
    if success:
        print("✅ You can now send emails!")
        print("   Test it: python test_email.py your@email.com")
    else:
        print("❌ Fix the issues above and try again")
        print("   Then redeploy and run this script again")
    
    print("=" * 60 + "\n")
