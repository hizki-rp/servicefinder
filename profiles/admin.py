from django.contrib import admin
from .models import Profile, Agent

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'referred_by')
    search_fields = ('user__username', 'user__email', 'phone_number', 'referred_by')
    raw_id_fields = ('user',)
    list_filter = ('referred_by',)


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ('user', 'referral_code', 'phone_number', 'referrals_count', 'is_active', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'referral_code', 'phone_number')
    list_filter = ('is_active', 'created_at')
    raw_id_fields = ('user',)
    readonly_fields = ('referral_code', 'referrals_count', 'created_at')
