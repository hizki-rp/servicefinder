from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from profiles.models import Agent


class Command(BaseCommand):
    help = 'List all agents and their manager status'

    def handle(self, *args, **options):
        agents = Agent.objects.select_related('user').all()
        
        if not agents:
            self.stdout.write(self.style.WARNING('No agents found!'))
            return
        
        self.stdout.write(f'Found {agents.count()} agents:\n')
        
        # Table header
        self.stdout.write(f"{'Username':<15} {'Name':<25} {'Referral Code':<12} {'Manager Status':<15} {'Referrals':<10}")
        self.stdout.write('-' * 80)
        
        for agent in agents:
            user = agent.user
            is_manager = user.groups.filter(name='Agent Manager').exists()
            manager_status = '✅ Manager' if is_manager else '👤 Agent'
            full_name = f"{user.first_name} {user.last_name}".strip() or 'N/A'
            
            self.stdout.write(
                f"{user.username:<15} {full_name:<25} {agent.referral_code:<12} "
                f"{manager_status:<15} {agent.referrals_count:<10}"
            )
        
        # Summary
        total_agents = agents.count()
        manager_agents = sum(1 for agent in agents if agent.user.groups.filter(name='Agent Manager').exists())
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'Summary:')
        self.stdout.write(f'  Total Agents: {total_agents}')
        self.stdout.write(f'  Agent Managers: {manager_agents}')
        self.stdout.write(f'  Regular Agents: {total_agents - manager_agents}')
        self.stdout.write('='*50)
        
        if manager_agents == 0:
            self.stdout.write('\n💡 To make an agent a manager, run:')
            self.stdout.write('   python manage.py make_agent_manager --username <username>')
        else:
            self.stdout.write('\n🎯 Agent Managers can access: /agent-manager/dashboard')