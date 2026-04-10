"""
Email-based authentication system.
Replaces OTP/phone authentication with email verification codes.
Uses the existing EmailService for reliable email delivery.
"""
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
import random
import string
import logging
from .models import UserProfile

logger = logging.getLogger(__name__)


class EmailVerificationCode:
    """
    Temporary in-memory storage for email verification codes.
    In production, consider using Redis or database model.
    """
    _codes = {}  # {email: {'code': '123456', 'expires_at': datetime, 'name': 'John', 'attempts': 0}}
    
    @classmethod
    def generate_code(cls, email, name=''):
        """Generate a 6-digit verification code"""
        code = ''.join(random.choices(string.digits, k=6))
        expires_at = timezone.now() + timezone.timedelta(minutes=10)
        
        cls._codes[email] = {
            'code': code,
            'expires_at': expires_at,
            'name': name,
            'attempts': 0
        }
        
        return code
    
    @classmethod
    def verify_code(cls, email, code):
        """Verify the code for an email"""
        if email not in cls._codes:
            return False, 'Invalid verification code'
        
        data = cls._codes[email]
        
        # Check expiration
        if timezone.now() > data['expires_at']:
            del cls._codes[email]
            return False, 'Verification code has expired. Please request a new one.'
        
        # Check attempts
        data['attempts'] += 1
        if data['attempts'] > 5:
            del cls._codes[email]
            return False, 'Too many attempts. Please request a new code.'
        
        # Verify code
        if data['code'] != code:
            return False, 'Invalid verification code'
        
        # Success - clean up
        name = data.get('name', '')
        del cls._codes[email]
        return True, name
    
    @classmethod
    def cleanup_expired(cls):
        """Remove expired codes"""
        now = timezone.now()
        expired = [email for email, data in cls._codes.items() if now > data['expires_at']]
        for email in expired:
            del cls._codes[email]


def send_verification_email(email, code, name=''):
    """
    Send verification code via email using the proven EmailService.
    Returns (success: bool, message: str)
    """
    subject = 'Your Mert Service Verification Code'
    
    # Plain text version
    message = f"""
Hello{' ' + name if name else ''}!

Your verification code is: {code}

This code will expire in 10 minutes.

If you didn't request this code, please ignore this email.

Best regards,
Mert Service Team
"""
    
    # HTML version
    html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #1e3a5f 0%, #2c5282 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
        .code-box {{ background: white; border: 2px dashed #3b82f6; border-radius: 10px; padding: 20px; text-align: center; margin: 20px 0; }}
        .code {{ font-size: 32px; font-weight: bold; color: #1e3a5f; letter-spacing: 8px; }}
        .footer {{ text-align: center; margin-top: 20px; color: #64748b; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Mert Service</h1>
            <p>Email Verification</p>
        </div>
        <div class="content">
            <p>Hello{' <strong>' + name + '</strong>' if name else ''}!</p>
            <p>Your verification code is:</p>
            <div class="code-box">
                <div class="code">{code}</div>
            </div>
            <p><strong>This code will expire in 10 minutes.</strong></p>
            <p>If you didn't request this code, please ignore this email.</p>
            <div class="footer">
                <p>Best regards,<br>Mert Service Team</p>
            </div>
        </div>
    </div>
</body>
</html>
"""
    
    # 🔍 CRITICAL: Detailed logging
    logger.info(f"📧 Attempting to send verification email to: {email}")
    logger.info(f"📧 From: {settings.DEFAULT_FROM_EMAIL}")
    logger.info(f"📧 Backend: {settings.EMAIL_BACKEND}")
    logger.info(f"🔐 VERIFICATION CODE: {code} for {email}")  # Always log code
    
    try:
        # Use Django's send_mail with fail_silently=False to catch errors
        from django.core.mail import EmailMultiAlternatives
        
        email_message = EmailMultiAlternatives(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email]
        )
        email_message.attach_alternative(html_message, "text/html")
        
        result = email_message.send(fail_silently=False)
        
        if result:
            logger.info(f"✅ Email sent successfully to {email}")
            return True, "Email sent successfully"
        else:
            logger.error(f"❌ Email sending returned 0 for {email}")
            return False, "Email sending failed - no error details"
            
    except Exception as e:
        logger.error(f"❌ EMAIL ERROR: {str(e)}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        import traceback
        logger.error(traceback.format_exc())
        return False, f"SMTP Error: {str(e)}"


@api_view(['POST'])
@permission_classes([AllowAny])
def email_request(request):
    """
    Request verification code for email.
    Creates and sends a 6-digit code to the email.
    """
    email = request.data.get('email', '').strip().lower()
    name = request.data.get('name', '').strip()
    
    if not email:
        return Response(
            {'error': 'Email is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Basic email validation
    if '@' not in email or '.' not in email:
        return Response(
            {'error': 'Invalid email address'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Generate verification code
    code = EmailVerificationCode.generate_code(email, name)
    
    # Send email with detailed error handling
    email_sent, error_message = send_verification_email(email, code, name)
    
    if not email_sent:
        # Email failed - return error with code in development
        logger.error(f"Failed to send verification email to {email}: {error_message}")
        
        response_data = {
            'error': f'Failed to send verification email: {error_message}',
            'email': email,
        }
        
        # In development, still return code even if email fails (for testing)
        if settings.DEBUG:
            response_data['verification_code'] = code
            response_data['message'] = 'Email failed but code is available in development mode. Check Render logs for details.'
            logger.warning(f"Development mode: Returning code despite email failure")
        
        return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Success - email sent
    response_data = {
        'message': 'Verification code sent successfully',
        'email': email,
        'expires_in': '10 minutes',
    }
    
    # Include code in development mode
    if settings.DEBUG:
        response_data['verification_code'] = code  # REMOVE IN PRODUCTION!
        logger.info(f"Development mode: Including code in response")
    
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def email_verify(request):
    """
    Verify email code and create/login user.
    Returns JWT tokens for authenticated session.
    """
    email = request.data.get('email', '').strip().lower()
    code = request.data.get('code', '').strip()
    name = request.data.get('name', '').strip()
    
    if not email or not code:
        return Response(
            {'error': 'Email and verification code are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verify code
    verified, result = EmailVerificationCode.verify_code(email, code)
    
    if not verified:
        return Response(
            {'error': result},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Use name from verification if not provided
    if not name and result:
        name = result
    
    # Check if user exists with this email
    try:
        user = User.objects.get(email=email)
        created = False
        
        # Update user profile if exists
        if hasattr(user, 'user_profile'):
            user.user_profile.is_email_verified = True
            user.user_profile.save()
        else:
            # Create user profile if it doesn't exist
            UserProfile.objects.create(
                user=user,
                is_email_verified=True
            )
    except User.DoesNotExist:
        # Create new user
        username = email.split('@')[0]
        
        # Ensure username is unique
        counter = 1
        base_username = username
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=name or 'User',
        )
        
        # Create user profile
        UserProfile.objects.create(
            user=user,
            is_email_verified=True
        )
        created = True
    
    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    
    # Get user profile data
    user_profile = None
    if hasattr(user, 'user_profile'):
        from .serializers import UserProfileSerializer
        user_profile = UserProfileSerializer(user.user_profile).data
    
    return Response({
        'message': 'Email verified successfully',
        'created': created,
        'user': {
            'id': user.id,
            'username': user.username,
            'name': user.first_name,
            'email': email,
            'is_staff': user.is_staff,
        },
        'user_profile': user_profile,  # Include user_profile in response
        'tokens': {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        },
    }, status=status.HTTP_200_OK)
