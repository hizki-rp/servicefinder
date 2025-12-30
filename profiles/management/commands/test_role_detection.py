from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.test import Client
from profiles.models import Agent
import json


class Command(BaseCommand):
    help = 'Test role detection for agent manager functionality'

    def handle(self, *args, **options):
        # Get test users
        try:
            agent_user = User.objects.get(username='testagent')
            manager_group = Group.objects.get(name='Agent Manager')
            
            self.stdout.write('=== ROLE DETECTION TEST ===')
            self.stdout.write(f'User: {agent_user.username}')
            self.stdout.write(f'Groups: {[g.name for g in agent_user.groups.all()]}')
            
            # Check if user is in Agent Manager group
            is_manager = agent_user.groups.filter(name='Agent Manager').exists()
            self.stdout.write(f'Is Agent Manager: {is_manager}')
            
            # Check agent details
            try:
                agent = Agent.objects.get(user=agent_user)
                self.stdout.write(f'Agent Code: {agent.referral_code}')
                self.stdout.write(f'Referrals: {agent.referrals_count}')
            except Agent.DoesNotExist:
                self.stdout.write('❌ User is not an agent!')
                return
            
            self.stdout.write('\n=== EXPECTED BEHAVIOR ===')
            if is_manager:
                self.stdout.write('✅ User should be redirected to /agent-manager/dashboard')
                self.stdout.write('✅ User should see "Manager Dashboard" button in agent dashboard')
                self.stdout.write('✅ User can access both dashboards')
            else:
                self.stdout.write('👤 User should see regular agent dashboard')
                self.stdout.write('👤 User should NOT see manager dashboard button')
            
            self.stdout.write('\n=== DJANGO ADMIN LINKS ===')
            self.stdout.write(f'Profile: http://localhost:8000/admin/profiles/profile/{agent_user.profile.id}/change/')
            self.stdout.write(f'Agent: http://localhost:8000/admin/profiles/agent/{agent.id}/change/')
            self.stdout.write(f'User: http://localhost:8000/admin/auth/user/{agent_user.id}/change/')
            
        except User.DoesNotExist:
            self.stdout.write('❌ testagent user not found!')
            self.stdout.write('Run: python manage.py test_agent_endpoints')
        except Group.DoesNotExist:
            self.stdout.write('❌ Agent Manager group not found!')
            self.stdout.write('Run: python manage.py setup_agent_manager_group')