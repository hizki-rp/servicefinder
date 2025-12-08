from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender='payments.Payment')
def update_agent_referral_on_payment(sender, instance, created, **kwargs):
    """
    Update agent referral count when a payment is marked as successful.
    Only counts as a successful referral if the user has paid.
    """
    if instance.status == 'success':
        try:
            from .models import Profile, Agent
            
            # Get the user's profile to check if they were referred
            profile = Profile.objects.filter(user=instance.user).first()
            if profile and profile.referred_by:
                # Find the agent who referred this user
                agent = Agent.objects.filter(
                    referral_code__iexact=profile.referred_by,
                    is_active=True
                ).first()
                if agent:
                    # Update the agent's referral count to reflect only paid users
                    agent.update_paid_referrals_count()
                    logger.info(f"Updated agent {agent.user.username}'s referral count to {agent.referrals_count}")
        except Exception as e:
            logger.error(f"Error updating agent referral count for payment {instance.id}: {e}")


@receiver(post_save, sender='universities.UserDashboard')
def update_agent_referral_on_subscription_active(sender, instance, created, **kwargs):
    """
    Update agent referral count when a user's subscription becomes active.
    This handles cases where subscription is activated without a Payment record
    (e.g., admin manually activating subscription, or updating via dashboard).
    """
    # Only process if subscription status is 'active' and not a new dashboard
    if not created and instance.subscription_status == 'active':
        try:
            from .models import Profile, Agent
            
            # Get the user's profile to check if they were referred
            profile = Profile.objects.filter(user=instance.user).first()
            if profile and profile.referred_by:
                # Find the agent who referred this user
                agent = Agent.objects.filter(
                    referral_code__iexact=profile.referred_by,
                    is_active=True
                ).first()
                if agent:
                    # Update the agent's referral count to reflect only paid/active users
                    agent.update_paid_referrals_count()
                    logger.info(f"Updated agent {agent.user.username}'s referral count to {agent.referrals_count} (subscription activated)")
        except Exception as e:
            logger.error(f"Error updating agent referral count for dashboard {instance.id}: {e}")

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
