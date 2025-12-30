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
        ('User Groups & Permissions', {
            'fields': ('user_groups',),
            'description': 'Manage user roles and permissions'
        }),
    )
    
    def get_user_groups(self, obj):
        """Display user groups in list view"""
        return ', '.join([group.name for group in obj.user.groups.all()]) or 'None'
    get_user_groups.short_description = 'User Groups'
    
    def user_groups(self, obj):
        """Allow editing user groups in the form"""
        return obj.user.groups.all()
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            # Add a custom field for managing groups
            from django import forms
            from django.contrib.auth.models import Group
            
            class ProfileForm(form):
                user_groups = forms.ModelMultipleChoiceField(
                    queryset=Group.objects.all(),
                    widget=admin.widgets.FilteredSelectMultiple('Groups', False),
                    required=False,
                    initial=obj.user.groups.all(),
                    help_text='Select groups to assign roles like "Agent Manager"'
                )
                
                def save(self, commit=True):
                    instance = super().save(commit)
                    if commit and 'user_groups' in self.cleaned_data:
                        instance.user.groups.set(self.cleaned_data['user_groups'])
                    return instance
            
            return ProfileForm
        return form


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ('user', 'referral_code', 'phone_number', 'cbe_account_number', 'referrals_count', 'is_active', 'created_at', 'get_user_groups')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'referral_code', 'phone_number', 'cbe_account_number')
    list_filter = ('is_active', 'created_at', 'user__groups')
    raw_id_fields = ('user',)
    readonly_fields = ('referral_code', 'referrals_count', 'created_at')
    list_editable = ('cbe_account_number',)
    
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
        ('User Groups & Permissions', {
            'fields': ('user_groups',),
            'description': 'Manage agent roles (e.g., Agent Manager)'
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
    
    def get_readonly_fields(self, request, obj=None):
        # Make referral_code readonly for existing objects
        if obj:
            return self.readonly_fields + ('user',)
        return self.readonly_fields
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            # Add a custom field for managing groups
            from django import forms
            from django.contrib.auth.models import Group
            
            class AgentForm(form):
                user_groups = forms.ModelMultipleChoiceField(
                    queryset=Group.objects.all(),
                    widget=admin.widgets.FilteredSelectMultiple('Groups', False),
                    required=False,
                    initial=obj.user.groups.all(),
                    help_text='Select "Agent Manager" to give this agent management permissions'
                )
                
                def save(self, commit=True):
                    instance = super().save(commit)
                    if commit and 'user_groups' in self.cleaned_data:
                        instance.user.groups.set(self.cleaned_data['user_groups'])
                    return instance
            
            return AgentForm
        return form
