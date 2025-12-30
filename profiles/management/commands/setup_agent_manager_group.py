from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from profiles.models import Agent


class Command(BaseCommand):
    help = 'Create Agent Manager group with appropriate permissions'

    def handle(self, *args, **options):
        # Create Agent Manager group
        agent_manager_group, created = Group.objects.get_or_create(name='Agent Manager')
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created Agent Manager group'))
        else:
            self.stdout.write('Agent Manager group already exists')
        
        # Get Agent content type
        agent_content_type = ContentType.objects.get_for_model(Agent)
        
        # Add view permission for Agent model
        view_agent_permission, _ = Permission.objects.get_or_create(
            codename='view_agent',
            name='Can view agent',
            content_type=agent_content_type,
        )
        
        # Add permissions to the group
        agent_manager_group.permissions.add(view_agent_permission)
        
        self.stdout.write(
            self.style.SUCCESS(
                'Agent Manager group setup complete with view permissions'
            )
        )
        
        # Show instructions
        self.stdout.write('\n' + '='*50)
        self.stdout.write('INSTRUCTIONS:')
        self.stdout.write('1. Go to Django Admin > Users')
        self.stdout.write('2. Select an agent user')
        self.stdout.write('3. Add them to the "Agent Manager" group')
        self.stdout.write('4. They will then have access to view all agents')
        self.stdout.write('='*50)