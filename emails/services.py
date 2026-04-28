from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from .models import EmailLog, EmailTemplate
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service class for handling email operations"""
    
    @staticmethod
    def send_single_email(recipient, subject, body, template=None, sent_by=None):
        """
        Send a single email and log it
        """
        try:
            # Create email log entry
            email_log = EmailLog.objects.create(
                recipient=recipient,
                subject=subject,
                body=body,
                template=template,
                sent_by=sent_by,
                status='pending'
            )
            
            # Send email with detailed error handling
            try:
                result = send_mail(
                    subject=subject,
                    message=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient.email],
                    fail_silently=False,
                )
                
                if result:
                    # Update log on success
                    email_log.status = 'sent'
                    email_log.sent_at = timezone.now()
                    email_log.save()
                    
                    logger.info(f"Email sent successfully to {recipient.email}")
                    return True, "Email sent successfully"
                else:
                    # Update log on failure
                    email_log.status = 'failed'
                    email_log.error_message = "Email sending returned False"
                    email_log.save()
                    
                    logger.error(f"Email sending returned False for {recipient.email}")
                    return False, "Email sending failed - no error details"
                    
            except Exception as email_error:
                # Update log on failure
                email_log.status = 'failed'
                email_log.error_message = str(email_error)
                email_log.save()
                
                logger.error(f"SMTP error sending email to {recipient.email}: {str(email_error)}")
                return False, f"SMTP Error: {str(email_error)}"
            
        except Exception as e:
            # Update log on failure
            if 'email_log' in locals():
                email_log.status = 'failed'
                email_log.error_message = str(e)
                email_log.save()
            
            logger.error(f"Failed to send email to {recipient.email}: {str(e)}")
            return False, str(e)
    
    @staticmethod
    def send_bulk_email(recipients, subject, body, template=None, sent_by=None):
        """
        Send bulk emails and log each one
        """
        results = {
            'sent': 0,
            'failed': 0,
            'errors': []
        }
        
        for recipient in recipients:
            success, message = EmailService.send_single_email(
                recipient, subject, body, template, sent_by
            )
            
            if success:
                results['sent'] += 1
            else:
                results['failed'] += 1
                results['errors'].append(f"{recipient.email}: {message}")
        
        return results
    
    @staticmethod
    def send_template_email(recipient, template_name, context=None, sent_by=None):
        """
        Send email using a template
        """
        try:
            template = EmailTemplate.objects.get(name=template_name, is_active=True)
            
            # Prepare context
            if context is None:
                context = {}
            
            # Add user information to context
            context.update({
                'user_name': recipient.first_name or recipient.username,
                'user_email': recipient.email,
                'user_username': recipient.username,
            })
            
            # Render subject and body with context
            subject = template.subject.format(**context)
            body = template.body.format(**context)
            
            return EmailService.send_single_email(
                recipient, subject, body, template, sent_by
            )
            
        except EmailTemplate.DoesNotExist:
            return False, f"Template '{template_name}' not found"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def get_user_emails(user_ids=None, active_only=True):
        """
        Get users for email sending
        """
        queryset = User.objects.all()
        
        if active_only:
            queryset = queryset.filter(is_active=True)
        
        if user_ids:
            queryset = queryset.filter(id__in=user_ids)
        
        return queryset.select_related('profile')
    
    @staticmethod
    def create_default_templates():
        """
        Create default email templates
        """
        templates = [
            {
                'name': 'welcome',
                'subject': 'Welcome to Mert Service!',
                'body': '''Dear {user_name},

Welcome to Mert Service! We're excited to have you join our community connecting service providers with clients across Ethiopia.

Your account has been successfully created and you can now:
- Browse trusted service providers in your area
- Contact providers directly and get instant quotes
- Read reviews from real customers
- Discover services near you with location-based search

Whether you need home services, professional help, or want to become a provider yourself, Mert Service makes it easy!

If you have any questions, feel free to contact our support team.

Best regards,
The Mert Service Team'''
            },
            {
                'name': 'provider_welcome',
                'subject': 'Welcome to Mert Service - Start Growing Your Business',
                'body': '''Dear {user_name},

Congratulations on becoming a Mert Service provider! You're now part of a growing network of trusted service professionals across Ethiopia.

Next steps to get started:
- Complete your provider profile
- Upload verification documents (National ID)
- Add your services with detailed descriptions
- Set your pricing and availability

Once verified, your services will be visible to thousands of potential clients in your area!

Best regards,
The Mert Service Team'''
            },
            {
                'name': 'verification_approved',
                'subject': 'Your Mert Service verification has been approved!',
                'body': '''Dear {user_name},

Great news! Your verification documents have been approved and your provider account is now active.

Your services are now visible to clients and you can start receiving inquiries. Make sure to:
- Keep your profile updated
- Respond promptly to client inquiries
- Maintain high service quality
- Collect positive reviews

Welcome to the Mert Service provider community!

Best regards,
The Mert Service Team'''
            },
            {
                'name': 'verification_rejected',
                'subject': 'Action Required: Mert Service verification needs attention',
                'body': '''Dear {user_name},

We've reviewed your verification documents and unfortunately we need you to resubmit them.

Reason: {rejection_reason}

Please upload clear, valid documents to complete your verification. Once approved, you'll be able to start offering your services to clients.

If you have questions, contact our support team.

Best regards,
The Mert Service Team'''
            }
        ]
        
        for template_data in templates:
            EmailTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults=template_data
            )



