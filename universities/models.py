from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Create your models here.

class University(models.Model):
    name = models.CharField(max_length=200)
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100, blank=True)
    course_offered = models.CharField(max_length=200, blank=True, default='')
    application_fee = models.DecimalField(max_digits=6, decimal_places=2)
    tuition_fee = models.DecimalField(max_digits=8, decimal_places=2)
    # This field will store a list of intake objects, e.g.,
    # [{"name": "September 2025", "deadline": "2025-06-30"}]
    intakes = models.JSONField(default=list, blank=True, help_text="List of intake periods and their deadlines.")
    bachelor_programs = models.JSONField(default=list)
    masters_programs = models.JSONField(default=list)
    scholarships = models.JSONField(default=list)
    university_link = models.URLField()
    application_link = models.URLField()
    description = models.TextField(default="")
    # image_url = models.URLField(blank=True, null=True, help_text="Optional URL to university image")

    def __str__(self):
        return self.name

class UserDashboard(models.Model):
    SUBSCRIPTION_CHOICES = [
        ('none', 'None'),
        ('active', 'Active'),
        ('expired', 'Expired'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='dashboard')
    favorites = models.ManyToManyField(University, related_name='favorited_by', blank=True)
    planning_to_apply = models.ManyToManyField(University, related_name='planned_by', blank=True)
    applied = models.ManyToManyField(University, related_name='applied_by', blank=True)
    accepted = models.ManyToManyField(University, related_name='accepted_by', blank=True)
    visa_approved = models.ManyToManyField(University, related_name='visa_approved_for', blank=True)
    subscription_status = models.CharField(
        max_length=10, choices=SUBSCRIPTION_CHOICES, default='none'
    )
    subscription_end_date = models.DateField(null=True, blank=True)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    months_subscribed = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    
    def update_subscription(self, amount_paid, monthly_price=600):
        from django.utils import timezone
        from datetime import timedelta
        
        self.total_paid += amount_paid
        months_to_add = int(amount_paid // monthly_price)
        
        if months_to_add > 0:
            self.months_subscribed += months_to_add
            self.is_verified = True
            self.subscription_status = 'active'
            
            if self.subscription_end_date and self.subscription_end_date > timezone.now().date():
                self.subscription_end_date += timedelta(days=30 * months_to_add)
            else:
                self.subscription_end_date = timezone.now().date() + timedelta(days=30 * months_to_add)
        
        self.save()
        return months_to_add

    def __str__(self):
        return f"{self.user.username}'s Dashboard"

@receiver(post_save, sender=User)
def create_user_dashboard(sender, instance, created, **kwargs):
    """
    Automatically create a UserDashboard when a new User is created.
    """
    if created:
        UserDashboard.objects.create(user=instance)

class UniversityJSONImport(models.Model):
    """
    A model to facilitate importing University data via JSON in the Django admin.
    Each instance represents a single import action, storing the raw JSON.
    """
    json_data = models.TextField(help_text="Paste a single JSON object or a list of JSON objects here.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "University JSON Import"
        verbose_name_plural = "University JSON Imports"
        ordering = ['-created_at']

class ScholarshipResult(models.Model):
    country = models.CharField(max_length=100, blank=True)
    scholarships_data = models.JSONField(default=list)
    fetched_at = models.DateTimeField(auto_now_add=True)
    total_count = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "Scholarship Result"
        verbose_name_plural = "Scholarship Results"
        ordering = ['-fetched_at']

@receiver(post_save, sender=UserDashboard)
def send_payment_completion_email(sender, instance, created, **kwargs):
    """
    Send welcome email to users when they complete payment (subscription becomes active)
    """
    if not created and instance.subscription_status == 'active':
        try:
            # Get user's first name or username for personalization
            user_name = instance.user.first_name if instance.user.first_name else instance.user.username
            
            # Welcome message for paid users
            subject = "Welcome to Addis Temari Premium - Your Next Steps"
            message = f"""Dear {user_name},

Thank you for completing your account creation and being a valued member! We're thrilled to support you on your journey to international education.

Here's what you need to do next:

📋 REQUIRED DOCUMENTS FOR UNIVERSITY APPLICATION:

For Bachelor's Degree:
• High school transcripts (translated and certified)
• English proficiency test (IELTS/TOEFL) - minimum 6.0 IELTS or 80 TOEFL - Note that some universities accept Proficiency letter or medium of instruction
• Personal statement/essay
• Letters of recommendation (2-3)
• Passport copy
• Financial documents (bank statements, sponsorship letters)
• Application fee payment proof

For Master's Degree:
• Bachelor's degree certificate and transcripts (translated and certified)
• English proficiency test (IELTS/TOEFL) - minimum 6.5 IELTS or 90 TOEFL
• Statement of purpose
• Letters of recommendation (2-3 academic references)
• CV/Resume
• Research proposal (for research-based programs)
• Passport copy
• Financial documents
• Application fee payment proof

🎯 NEXT STEPS:
1. Complete your profile with accurate information
2. Browse our university database to find your ideal programs
3. Start preparing your application documents
4. Use our application tracking tools to stay organized

Obtain these documents for your future success! Our team is here to support you every step of the way.

Best regards,
The Addis Temari Team"""

            # Send email
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.user.email],
                fail_silently=False,
            )
            
            logger.info(f"Payment completion email sent to {instance.user.email}")
            
        except Exception as e:
            logger.error(f"Failed to send payment completion email to {instance.user.email}: {str(e)}")
