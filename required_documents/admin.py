"""
Admin configuration for document upload models.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    DocumentCategory, 
    DocumentSubmission, 
    DocumentSubmissionBatch,
    UserDocumentProfile,
    DocumentFeedback,
    DocumentRequest
)


@admin.register(UserDocumentProfile)
class UserDocumentProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'field_of_study', 'highest_education', 
        'applying_to', 'phone_number', 'created_at'
    ]
    list_filter = ['field_of_study', 'highest_education', 'applying_to']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name', 'phone_number']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'phone_number')
        }),
        ('Program Preferences', {
            'fields': ('field_of_study', 'highest_education', 'applying_to')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'api_key', 'program_type', 'required', 'order', 'is_active']
    list_filter = ['program_type', 'required', 'is_active']
    search_fields = ['name', 'api_key', 'description']
    ordering = ['order', 'name']
    list_editable = ['order', 'is_active', 'required']


@admin.register(DocumentSubmission)
class DocumentSubmissionAdmin(admin.ModelAdmin):
    list_display = [
        'user_link', 'category_key', 'program_type', 
        'original_filename', 'status_badge', 'file_size_display',
        'uploaded_at', 'reviewed_by'
    ]
    list_filter = ['program_type', 'status', 'uploaded_at', 'category_key']
    search_fields = [
        'user__username', 'user__email', 'user__first_name', 
        'user__last_name', 'category_key', 'original_filename'
    ]
    readonly_fields = ['uploaded_at', 'updated_at', 'file_size', 'content_type']
    ordering = ['-uploaded_at']
    date_hierarchy = 'uploaded_at'
    actions = ['mark_approved', 'mark_rejected', 'mark_pending', 'mark_resubmit']
    
    fieldsets = (
        ('User & Document', {
            'fields': ('user', 'program_type', 'category', 'category_key')
        }),
        ('File Information', {
            'fields': ('file', 'original_filename', 'file_size', 'content_type')
        }),
        ('Review', {
            'fields': ('status', 'admin_notes', 'reviewed_by', 'reviewed_at')
        }),
        ('Timestamps', {
            'fields': ('uploaded_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'category', 'reviewed_by')
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__username'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'under_review': '#3b82f6',
            'approved': '#10b981',
            'rejected': '#ef4444',
            'resubmit': '#8b5cf6',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 4px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def file_size_display(self, obj):
        if obj.file_size < 1024:
            return f"{obj.file_size} B"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.1f} KB"
        else:
            return f"{obj.file_size / (1024 * 1024):.1f} MB"
    file_size_display.short_description = 'Size'
    
    @admin.action(description='Mark selected as Approved')
    def mark_approved(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='approved', reviewed_by=request.user, reviewed_at=timezone.now())
        self.message_user(request, f'{queryset.count()} documents marked as approved.')
    
    @admin.action(description='Mark selected as Rejected')
    def mark_rejected(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='rejected', reviewed_by=request.user, reviewed_at=timezone.now())
        self.message_user(request, f'{queryset.count()} documents marked as rejected.')
    
    @admin.action(description='Mark selected as Pending')
    def mark_pending(self, request, queryset):
        queryset.update(status='pending', reviewed_by=None, reviewed_at=None)
        self.message_user(request, f'{queryset.count()} documents marked as pending.')
    
    @admin.action(description='Request Resubmission')
    def mark_resubmit(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='resubmit', reviewed_by=request.user, reviewed_at=timezone.now())
        self.message_user(request, f'{queryset.count()} documents marked for resubmission.')


@admin.register(DocumentFeedback)
class DocumentFeedbackAdmin(admin.ModelAdmin):
    list_display = ['user', 'subject', 'feedback_type', 'admin', 'is_read', 'created_at']
    list_filter = ['feedback_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'subject', 'message']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Feedback Details', {
            'fields': ('user', 'submission', 'admin', 'feedback_type')
        }),
        ('Content', {
            'fields': ('subject', 'message')
        }),
        ('Status', {
            'fields': ('is_read', 'created_at')
        }),
    )


@admin.register(DocumentRequest)
class DocumentRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'document_name', 'status', 'deadline', 'admin', 'created_at']
    list_filter = ['status', 'deadline', 'created_at']
    search_fields = ['user__username', 'document_name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Request Details', {
            'fields': ('user', 'admin', 'document_name', 'description')
        }),
        ('Status', {
            'fields': ('status', 'deadline')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DocumentSubmissionBatch)
class DocumentSubmissionBatchAdmin(admin.ModelAdmin):
    list_display = ['user', 'program_type', 'is_complete', 'submitted_at', 'submission_count']
    list_filter = ['program_type', 'is_complete', 'submitted_at']
    search_fields = ['user__username']
    readonly_fields = ['submitted_at']
    filter_horizontal = ['submissions']
    
    def submission_count(self, obj):
        return obj.submissions.count()
    submission_count.short_description = 'Documents'
