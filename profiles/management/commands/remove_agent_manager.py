from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from profiles.models import Agent


class Command(BaseCommand):
    help = 'Remove agent manager role from a user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username of the agent manager to demote',
            required=True
        )

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            # Get the user
            user = User.objects.get(username=username)
            
            # Get Agent Manager group
            try:
                agent_manager_group = Group.objects.get(name='Agent Manager')
            except Group.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR('Agent Manager group not found!')
                )
                return
            
            # Remove user from Agent Manager group
            if agent_manager_group in user.groups.all():
                user.groups.remove(agent_manager_group)
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Removed Agent Manager role from {username}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'{username} was not an Agent Manager!')
                )
            
            # Show current groups
            groups = user.groups.all()
            if groups:
                group_names = [group.name for group in groups]
                self.stdout.write(f'Remaining groups: {", ".join(group_names)}')
            else:
                self.stdout.write('No groups assigned')
                
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User {username} not found!')
            )