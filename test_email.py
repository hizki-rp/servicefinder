"""
Quick email test script for Render shell.
Run this to test if SMTP is configured correctly.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_api.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email(recipient_email):
    """Send a test email"""
    print(f"\n📧 Testing email configuration...")
    print(f"Backend: {settings.EMAIL_BACKEND}")
    print(f"Host: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
    print(f"Port: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
    print(f"User: {getattr(settings, 'EMAIL_HOST_USER', 'Not set')}")
    print(f"From: {settings.DEFAULT_FROM_EMAIL}")
    print(f"To: {recipient_email}\n")
    
    try:
        result = send_mail(
            subject='🔍 Mert Service - Email Test',
            message='This is a test email from Mert Service.\n\nIf you received this, your SMTP configuration is working correctly!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        
        if result:
            print(f"✅ Email sent successfully to {recipient_email}")
            print(f"✅ Check your inbox (and spam folder!)")
            return True
        else:
            print(f"❌ Email sending returned 0")
            return False
            
    except Exception as e:
        print(f"❌ Email error: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        email = sys.argv[1]
    else:
        email = input("Enter recipient email: ")
    
    test_email(email)
