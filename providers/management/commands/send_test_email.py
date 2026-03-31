"""
Send a test email to verify SMTP configuration.
Run: python manage.py send_test_email <recipient>
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Send a test email to verify SMTP is working'

    def add_arguments(self, parser):
        parser.add_argument('recipient', type=str, help='Email address to send test to')

    def handle(self, *args, **options):
        recipient = options['recipient']
        self.stdout.write(f'Email backend: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'From: {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'Sending to: {recipient}...')

        try:
            send_mail(
                subject='✅ MertService Email Test',
                message=(
                    'This is a test email from MertService.\n\n'
                    'If you received this, your SMTP configuration is working correctly.\n\n'
                    '— The MertService Team'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f'✅ Test email sent to {recipient}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Failed: {e}'))
