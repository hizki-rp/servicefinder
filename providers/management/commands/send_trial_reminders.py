"""
Management command to send trial expiry reminders
Run with: python manage.py send_trial_reminders
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from providers.models import ProviderProfile
from providers.notifications import send_trial_expiry_warning


class Command(BaseCommand):
    help = 'Send trial expiry reminders to providers'

    def handle(self, *args, **options):
        """
        Send reminders to providers whose trial is expiring in 7, 3, or 1 day
        """
        self.stdout.write(self.style.SUCCESS('🔔 Checking for trial expiry reminders...'))
        
        total_sent = 0
        
        # Check for trials expiring in 7, 3, or 1 day
        for days in [7, 3, 1]:
            target_date = timezone.now() + timedelta(days=days)
            
            # Find providers with trial expiring on target date
            providers = ProviderProfile.objects.filter(
                trial_expiry_date__date=target_date.date(),
                is_active=True,
            )
            
            self.stdout.write(f'Found {providers.count()} providers with trial expiring in {days} days')
            
            for provider in providers:
                # Send notification
                result = send_trial_expiry_warning(provider, days)
                
                if result.get('success'):
                    total_sent += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ Sent reminder to {provider.user.username} ({days} days)'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠️ Failed to send to {provider.user.username}: {result.get("reason")}'
                        )
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Trial reminder job complete. Sent {total_sent} notifications.'
            )
        )
