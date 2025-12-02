from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from payments.models import Payment
from universities.models import UserDashboard


class Command(BaseCommand):
    help = 'Update all users with successful payments to have 1 month subscription from today'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without actually updating',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Get all users with successful payments
        successful_payments = Payment.objects.filter(status='success')
        user_ids = successful_payments.values_list('user', flat=True).distinct()
        
        self.stdout.write(f'Found {user_ids.count()} users with successful payments')
        
        updated_count = 0
        created_count = 0
        errors = []
        
        for user_id in user_ids:
            try:
                user = User.objects.get(id=user_id)
                
                # Get or create user dashboard
                dashboard, created = UserDashboard.objects.get_or_create(user=user)
                
                if created:
                    created_count += 1
                    self.stdout.write(f'Created dashboard for user: {user.username}')
                
                # Update subscription to 1 month from today
                new_end_date = timezone.now().date() + timedelta(days=30)
                
                if not dry_run:
                    dashboard.subscription_end_date = new_end_date
                    dashboard.subscription_status = 'active'
                    dashboard.is_verified = True
                    dashboard.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Updated subscription for {user.username}: '
                            f'status=active, end_date={new_end_date}'
                        )
                    )
                else:
                    self.stdout.write(
                        f'Would update {user.username}: '
                        f'status=active, end_date={new_end_date}'
                    )
                
                updated_count += 1
                
            except User.DoesNotExist:
                errors.append(f'User with id {user_id} does not exist')
            except Exception as e:
                errors.append(f'Error updating user {user_id}: {str(e)}')
        
        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes were made'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} users'))
            if created_count > 0:
                self.stdout.write(self.style.SUCCESS(f'Created {created_count} new dashboards'))
        
        if errors:
            self.stdout.write(self.style.ERROR(f'Encountered {len(errors)} errors:'))
            for error in errors:
                self.stdout.write(self.style.ERROR(f'  - {error}'))
        
        self.stdout.write(self.style.SUCCESS('=' * 60))

