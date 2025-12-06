# h:\Django2\UNI-FINDER-GIT\backend\profiles\models.py
from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
import logging
import random
import string

logger = logging.getLogger(__name__)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    preferred_intakes = models.JSONField(default=list, blank=True)
    # Referral code - 4 digit code entered by user during registration (e.g. "1234")
    referred_by = models.CharField(max_length=10, blank=True, null=True, 
                                   help_text="Referral code used during registration")

    def __str__(self):
        return f'{self.user.username} Profile'


class Agent(models.Model):
    """
    Agent model for users who can refer other users to the platform.
    Agents have their own registration, dashboard, and referral tracking.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='agent_profile')
    phone_number = models.CharField(max_length=20)
    referral_code = models.CharField(max_length=10, unique=True, blank=True,
                                     help_text="Unique referral code generated from initials + random digits")
    referrals_count = models.PositiveIntegerField(default=0, 
                                                   help_text="Number of users who registered using this agent's referral code")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'Agent: {self.user.username} ({self.referral_code})'

    def generate_referral_code(self):
        """
        Generate a unique referral code using agent's name initials + 4 random digits.
        Example: AB1234
        """
        first_initial = self.user.first_name[0].upper() if self.user.first_name else 'X'
        last_initial = self.user.last_name[0].upper() if self.user.last_name else 'X'
        
        # Generate unique code
        while True:
            random_digits = ''.join(random.choices(string.digits, k=4))
            code = f"{first_initial}{last_initial}{random_digits}"
            if not Agent.objects.filter(referral_code=code).exists():
                return code

    def save(self, *args, **kwargs):
        # Generate referral code if not set
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        super().save(*args, **kwargs)

    def get_referral_link(self):
        """
        Returns the full referral link for this agent.
        Example: https://addistemari.com/register?ref=AB1234
        """
        return f"https://addistemari.com/register?ref={self.referral_code}"

    def increment_referral_count(self):
        """Increment the referral count when a user registers with this agent's code."""
        self.referrals_count += 1
        self.save(update_fields=['referrals_count'])

# These signals automatically create a Profile when a new User is created.
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def send_welcome_email_on_registration(sender, instance, created, **kwargs):
    """
    Send welcome email to new users upon registration
    """
    if created:
        try:
            # Get user's first name or username for personalization
            user_name = instance.first_name if instance.first_name else instance.username
            
            # Welcome message for new users
            subject = "Welcome to Addis Temari - Complete Your Account Setup"
            message = f"""Dear {user_name},

Welcome to Addis Temari! We're excited to have you join our community of ambitious students pursuing their dreams of studying abroad.

Thank you for creating your account! To get the most out of your Addis Temari experience, you must complete your account by subscribing to our premium services. This will unlock:

🎓 Access to our comprehensive university database
📋 Personalized application guidance  
💼 Scholarship opportunities
📊 Application tracking tools
🎯 Expert support throughout your journey

Complete your account activation today and take the first step towards your international education goals!

Best regards,
The Addis Temari Team"""

            # Send email
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.email],
                fail_silently=False,
            )
            
            logger.info(f"Welcome email sent to {instance.email}")
            
        except Exception as e:
            logger.error(f"Failed to send welcome email to {instance.email}: {str(e)}")
