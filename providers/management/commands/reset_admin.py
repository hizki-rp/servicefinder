"""
Idempotent admin reset — run on every deploy.
Creates or updates the 'admin' superuser with a known password.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'MertAdmin2024!'
ADMIN_EMAIL = 'admin@mertservice.com'


class Command(BaseCommand):
    help = 'Create or reset the admin superuser'

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(username=ADMIN_USERNAME)
        user.set_password(ADMIN_PASSWORD)
        user.email = ADMIN_EMAIL
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()
        action = 'Created' if created else 'Reset'
        self.stdout.write(self.style.SUCCESS(
            f'{action} admin user — username: {ADMIN_USERNAME}, password: {ADMIN_PASSWORD}'
        ))
