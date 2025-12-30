from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.test import Client
from django.urls import reverse
from profiles.models import Agent
import json


class Command(BaseCommand):
    help = 'Test agent and agent manager endpoints'

    def handle(self, *args, **options):
        # Create test users
        agent_user, created = User.objects.get_or_create(
            username='testagent',
            defaults={
                'email': 'agent@test.com',
                'first_name': 'Test',
                'last_name': 'Agent'
            }
        )
        
        manager_user, created = User.objects.get_or_create(
            username='testmanager',
            defaults={
                'email': 'manager@test.com',
                'first_name': 'Test',
                'last_name': 'Manager'
            }
        )
        
        # Create agent
        agent, created = Agent.objects.get_or_create(
            user=agent_user,
            defaults={
                'phone_number': '+1234567890',
                'cbe_account_number': '1234567890'
            }
        )
        
        # Add manager to Agent Manager group
        agent_manager_group = Group.objects.get(name='Agent Manager')
        manager_user.groups.add(agent_manager_group)
        
        self.stdout.write('Test setup complete!')
        self.stdout.write(f'Agent: {agent_user.username} (ID: {agent_user.id})')
        self.stdout.write(f'Manager: {manager_user.username} (ID: {manager_user.id})')
        self.stdout.write(f'Agent referral code: {agent.referral_code}')
        
        # Test endpoints
        client = Client()
        
        # Test agent dashboard (would need authentication in real scenario)
        self.stdout.write('\n=== ENDPOINT TESTS ===')
        self.stdout.write('Agent Dashboard: /api/agent/dashboard/')
        self.stdout.write('Agent Manager Dashboard: /api/agent-manager/dashboard/')
        self.stdout.write('Agent Manager Detail: /api/agent-manager/agents/<id>/')
        
        self.stdout.write('\n=== SETUP COMPLETE ===')
        self.stdout.write('You can now:')
        self.stdout.write('1. Login as testagent to test agent dashboard')
        self.stdout.write('2. Login as testmanager to test agent manager dashboard')
        self.stdout.write('3. Visit Django Admin to assign more users to Agent Manager group')