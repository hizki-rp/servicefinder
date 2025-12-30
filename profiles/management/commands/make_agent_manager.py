from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from profiles.models import Agent


class Command(BaseCommand):
    help = 'Make an agent a manager by adding them to Agent Manager group'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username of the agent to make a manager',
            required=True
        )

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            # Get the user
            user = User.objects.get(username=username)
            
            # Check if user is an agent
            try:
                agent = Agent.objects.get(user=user)
                self.stdout.write(f'Found agent: {agent.referral_code}')
            except Agent.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User {username} is not an agent!')
                )
                return
            
            # Get Agent Manager group
            try:
                agent_manager_group = Group.objects.get(name='Agent Manager')
            except Group.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR('Agent Manager group not found! Run: python manage.py setup_agent_manager_group')
                )
                return
            
            # Add user to Agent Manager group
            if agent_manager_group in user.groups.all():
                self.stdout.write(
                    self.style.WARNING(f'{username} is already an Agent Manager!')
                )
            else:
                user.groups.add(agent_manager_group)
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {username} is now an Agent Manager!')
                )
            
            # Show current groups
            groups = user.groups.all()
            if groups:
                group_names = [group.name for group in groups]
                self.stdout.write(f'Current groups: {", ".join(group_names)}')
            else:
                self.stdout.write('No groups assigned')
                
            self.stdout.write('\n' + '='*50)
            self.stdout.write(f'{username} can now access:')
            self.stdout.write('- Agent Manager Dashboard: /agent-manager/dashboard')
            self.stdout.write('- View all agents and their statistics')
            self.stdout.write('='*50)
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User {username} not found!')
            )