from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile, Agent


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('referred_by', 'phone_number', 'bio')


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_groups')
    list_filter = BaseUserAdmin.list_filter + ('groups',)
    
    def get_groups(self, obj):
        return ', '.join([group.name for group in obj.groups.all()]) or 'None'
    get_groups.short_description = 'Groups'


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'referred_by', 'get_user_groups')
    search_fields = ('user__username', 'user__email', 'phone_number', 'referred_by')
    raw_id_fields = ('user',)
    list_filter = ('referred_by', 'user__groups')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Profile Details', {
            'fields': ('phone_number', 'bio', 'referred_by')
        }),
    )
    
    def get_user_groups(self, obj):
        """Display user groups in list view"""
        return ', '.join([group.name for group in obj.user.groups.all()]) or 'None'
    get_user_groups.short_description = 'User Groups'


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ('user', 'referral_code', 'phone_number', 'cbe_account_number', 'referrals_count', 'is_active', 'created_at', 'get_user_groups', 'is_manager')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'referral_code', 'phone_number', 'cbe_account_number')
    list_filter = ('is_active', 'created_at', 'user__groups')
    raw_id_fields = ('user',)
    readonly_fields = ('referral_code', 'referrals_count', 'created_at')
    list_editable = ('cbe_account_number',)
    actions = ['make_agent_manager', 'remove_agent_manager']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Agent Details', {
            'fields': ('referral_code', 'phone_number', 'cbe_account_number')
        }),
        ('Statistics', {
            'fields': ('referrals_count', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def get_user_groups(self, obj):
        """Display user groups in list view"""
        groups = obj.user.groups.all()
        if groups:
            group_list = []
            for group in groups:
                if group.name == 'Agent Manager':
                    group_list.append(f'🎯 {group.name}')
                else:
                    group_list.append(group.name)
            return ', '.join(group_list)
        return 'Regular Agent'
    get_user_groups.short_description = 'Role'
    
    def is_manager(self, obj):
        """Display manager status with icon"""
        is_manager = obj.user.groups.filter(name='Agent Manager').exists()
        return '🎯 Manager' if is_manager else '👤 Agent'
    is_manager.short_description = 'Manager Status'
    
    def make_agent_manager(self, request, queryset):
        """Admin action to make selected agents into Agent Managers"""
        from django.contrib.auth.models import Group
        
        agent_manager_group, created = Group.objects.get_or_create(name='Agent Manager')
        updated_count = 0
        
        for agent in queryset:
            if not agent.user.groups.filter(name='Agent Manager').exists():
                agent.user.groups.add(agent_manager_group)
                updated_count += 1
        
        if updated_count == 1:
            message = f"1 agent was promoted to Agent Manager."
        else:
            message = f"{updated_count} agents were promoted to Agent Manager."
        
        self.message_user(request, message)
    make_agent_manager.short_description = "🎯 Promote selected agents to Agent Manager"
    
    def remove_agent_manager(self, request, queryset):
        """Admin action to remove Agent Manager role from selected agents"""
        from django.contrib.auth.models import Group
        
        try:
            agent_manager_group = Group.objects.get(name='Agent Manager')
            updated_count = 0
            
            for agent in queryset:
                if agent.user.groups.filter(name='Agent Manager').exists():
                    agent.user.groups.remove(agent_manager_group)
                    updated_count += 1
            
            if updated_count == 1:
                message = f"1 agent was demoted from Agent Manager."
            else:
                message = f"{updated_count} agents were demoted from Agent Manager."
            
            self.message_user(request, message)
        except Group.DoesNotExist:
            self.message_user(request, "Agent Manager group does not exist.", level='ERROR')
    remove_agent_manager.short_description = "👤 Remove Agent Manager role from selected agents"
    
    def get_readonly_fields(self, request, obj=None):
        # Make referral_code readonly for existing objects
        if obj:
            return self.readonly_fields + ('user',)
        return self.readonly_fields
