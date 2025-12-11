from django.contrib import admin
from .models import Essay


@admin.register(Essay)
class EssayAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'is_template', 'created_at', 'updated_at']
    list_filter = ['is_template', 'created_at', 'updated_at']
    search_fields = ['title', 'description', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        """Show all essays in admin, but clearly mark templates"""
        return super().get_queryset(request)
    
    def save_model(self, request, obj, form, change):
        """Prevent accidentally marking user essays as templates in admin"""
        template_usernames = ['rakibul', 'miki', 'randall', 'seun', 'zeynep']
        if obj.user and obj.user.username not in template_usernames:
            obj.is_template = False
        super().save_model(request, obj, form, change)

