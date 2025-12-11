from django.core.management.base import BaseCommand
from essays.models import Essay
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Fix user essays that were incorrectly marked as templates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Find essays that are marked as templates but belong to real users
        # (excluding the seeded template users)
        template_usernames = ['rakibul', 'miki', 'randall', 'seun', 'zeynep']
        
        problematic_essays = Essay.objects.filter(
            is_template=True,
            user__isnull=False
        ).exclude(
            user__username__in=template_usernames
        )
        
        self.stdout.write(f"Found {problematic_essays.count()} user essays incorrectly marked as templates:")
        
        for essay in problematic_essays:
            self.stdout.write(f"  - Essay ID {essay.id}: '{essay.title}' by {essay.user.username}")
            
            if not dry_run:
                essay.is_template = False
                essay.save()
                self.stdout.write(f"    ✅ Fixed: Changed is_template to False")
            else:
                self.stdout.write(f"    🔍 Would change is_template to False")
        
        if dry_run:
            self.stdout.write(f"\nDry run complete. Run without --dry-run to apply changes.")
        else:
            self.stdout.write(f"\n✅ Fixed {problematic_essays.count()} essays.")
            
        # Also show summary of all essays
        self.stdout.write("\n📊 Essay Summary:")
        total_essays = Essay.objects.count()
        user_essays = Essay.objects.filter(is_template=False).count()
        template_essays = Essay.objects.filter(is_template=True).count()
        
        self.stdout.write(f"  Total essays: {total_essays}")
        self.stdout.write(f"  User essays (is_template=False): {user_essays}")
        self.stdout.write(f"  Template essays (is_template=True): {template_essays}")