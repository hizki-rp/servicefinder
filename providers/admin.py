from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.db.models import Count, Avg
from .models import (
    ProviderProfile, 
    ProviderService, 
    ProviderVerification, 
    CallLog, 
    Review,
    ServiceCategory,
    ServiceSubCategory,
)


@admin.register(ProviderProfile)
class ProviderProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user_display',
        'phone_number',
        'city',
        'verification_badges',
        'trial_status_display',
        'rating_display',
        'services_count',
        'max_services_allowed',
        'subscription_status',
        'created_at',
    ]
    
    list_filter = [
        'is_verified',
        'national_id_verified',
        'payment_verified',
        'subscription_status',
        'city',
        'country',
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
        'phone_number',
        'city',
    ]
    
    readonly_fields = [
        'user',
        'services_count',
        'trial_start_date',
        'trial_expiry_date',
        'trial_status_display',
        'days_remaining_display',
        'rating',
        'total_reviews',
        'created_at',
        'updated_at',
        'location_display',
    ]
    
    fieldsets = (
        ('Provider Information', {
            'fields': (
                'user',
                'phone_number',
                'city',
                'country',
                'location_display',
            )
        }),
        ('Verification Status', {
            'fields': (
                'national_id_verified',
                'payment_verified',
                'is_verified',
            ),
            'classes': ('collapse',),
        }),
        ('Trial Period (1-Month Free)', {
            'fields': (
                'trial_start_date',
                'trial_expiry_date',
                'trial_status_display',
                'days_remaining_display',
                'trial_notification_sent',
            ),
            'description': 'New providers get 1 month free. Payment required after trial expires.',
        }),
        ('Service Limits', {
            'fields': (
                'services_count',
                'max_services_allowed',
            ),
            'description': 'Default limit is 3 services. Increase for high-quality providers.',
        }),
        ('Rating & Reviews', {
            'fields': (
                'rating',
                'total_reviews',
            ),
            'classes': ('collapse',),
        }),
        ('Subscription', {
            'fields': (
                'subscription_status',
                'subscription_end_date',
                'total_paid',
                'months_subscribed',
            ),
            'classes': ('collapse',),
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['increase_service_limit', 'verify_provider_manually', 'extend_trial_period']
    
    def user_display(self, obj):
        """Display user with link to user admin"""
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        name = obj.user.get_full_name() or obj.user.username
        return format_html('<a href="{}">{}</a>', url, name)
    user_display.short_description = 'Provider'
    
    def trial_status_display(self, obj):
        """Display trial status with color coding"""
        if not obj.trial_start_date:
            return format_html('<span style="color: gray;">No Trial</span>')
        
        if obj.is_trial_active:
            days_left = obj.days_until_trial_expiry
            if days_left <= 3:
                color = 'orange'
                status = f'⚠️ Expiring Soon ({days_left}d)'
            else:
                color = 'green'
                status = f'✓ Active ({days_left}d left)'
            return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, status)
        else:
            return format_html('<span style="color: red;">❌ Expired</span>')
    trial_status_display.short_description = 'Trial Status'
    
    def days_remaining_display(self, obj):
        """Display days remaining in trial"""
        if not obj.trial_expiry_date:
            return '-'
        days = obj.days_until_trial_expiry
        if days is None:
            return '-'
        if days == 0:
            return format_html('<span style="color: red; font-weight: bold;">Expires Today!</span>')
        elif days <= 3:
            return format_html('<span style="color: orange; font-weight: bold;">{} days</span>', days)
        else:
            return f'{days} days'
    days_remaining_display.short_description = 'Days Remaining'
    
    def verification_badges(self, obj):
        """Display verification status with colored badges"""
        badges = []
        
        if obj.is_verified:
            badges.append('<span style="background:#27AE60;color:white;padding:3px 8px;border-radius:3px;font-size:11px;">✓ VERIFIED</span>')
        else:
            if obj.national_id_verified:
                badges.append('<span style="background:#3498DB;color:white;padding:3px 8px;border-radius:3px;font-size:11px;">ID ✓</span>')
            else:
                badges.append('<span style="background:#E74C3C;color:white;padding:3px 8px;border-radius:3px;font-size:11px;">ID ✗</span>')
            
            if obj.payment_verified:
                badges.append('<span style="background:#3498DB;color:white;padding:3px 8px;border-radius:3px;font-size:11px;">PAY ✓</span>')
            else:
                badges.append('<span style="background:#E74C3C;color:white;padding:3px 8px;border-radius:3px;font-size:11px;">PAY ✗</span>')
        
        return format_html(' '.join(badges))
    verification_badges.short_description = 'Verification'
    
    def rating_display(self, obj):
        """Display rating with stars"""
        if obj.total_reviews == 0:
            return format_html('<span style="color:#95A5A6;">No reviews</span>')
        
        stars = '⭐' * int(obj.rating)
        rating_formatted = f'{obj.rating:.1f}'
        return format_html(
            '<span style="color:#F39C12;">{}</span> <span style="color:#7F8C8D;">({} / {})</span>',
            stars,
            rating_formatted,
            obj.total_reviews
        )
    rating_display.short_description = 'Rating'
    
    def location_display(self, obj):
        """Display location coordinates"""
        if obj.latitude and obj.longitude:
            return format_html(
                'Lat: {:.6f}, Lng: {:.6f}',
                obj.latitude,
                obj.longitude
            )
        return 'Not set'
    location_display.short_description = 'GPS Location'
    
    def increase_service_limit(self, request, queryset):
        """Admin action to increase service limit for selected providers"""
        for profile in queryset:
            profile.max_services_allowed += 1
            profile.save(update_fields=['max_services_allowed'])
        
        self.message_user(
            request,
            f'Increased service limit for {queryset.count()} provider(s)',
            messages.SUCCESS
        )
    increase_service_limit.short_description = 'Increase service limit by 1'
    
    def verify_provider_manually(self, request, queryset):
        """Admin action to manually verify providers (override)"""
        count = 0
        for profile in queryset:
            if not profile.is_verified:
                profile.national_id_verified = True
                profile.payment_verified = True
                profile.is_verified = True
                profile.save()
                count += 1
                
                # Send notification
                from notifications.models import Notification
                Notification.objects.create(
                    title='Account Verified! 🎉',
                    message='Your provider account has been verified. You can now create services and be discovered by clients.',
                    audience='custom'
                ).recipients.add(profile.user)
        
        self.message_user(
            request,
            f'Manually verified {count} provider(s)',
            messages.SUCCESS
        )
    verify_provider_manually.short_description = 'Manually verify selected providers'
    
    def extend_trial_period(self, request, queryset):
        """Admin action to extend trial period by 30 days"""
        from datetime import timedelta
        count = 0
        for profile in queryset:
            if profile.trial_expiry_date:
                profile.trial_expiry_date = profile.trial_expiry_date + timedelta(days=30)
                profile.trial_notification_sent = False
                profile.save()
                count += 1
                
                # Send notification
                from notifications.models import Notification
                Notification.objects.create(
                    title='Trial Extended! 🎁',
                    message=f'Your trial period has been extended by 30 days. New expiry: {profile.trial_expiry_date.strftime("%B %d, %Y")}',
                    audience='custom'
                ).recipients.add(profile.user)
        
        self.message_user(
            request,
            f'Extended trial period for {count} provider(s)',
            messages.SUCCESS
        )
    extend_trial_period.short_description = 'Extend trial period by 30 days'


@admin.register(ProviderService)
class ProviderServiceAdmin(admin.ModelAdmin):  # Changed from GISModelAdmin for SQLite
    list_display = [
        'name',
        'provider_display',
        'service_category',
        'price_display',
        'city',
        'verification_badge',
        'is_active',
        'views_count',
        'created_at',
    ]
    
    list_filter = [
        'service_category',
        'price_type',
        'verification_status',
        'is_active',
        'city',
        'created_at',
    ]
    
    search_fields = [
        'name',
        'description',
        'service_category',
        'provider__username',
        'provider__email',
        'city',
    ]
    
    readonly_fields = [
        'provider',
        'views_count',
        'created_at',
        'updated_at',
        'location_map',
    ]
    
    fieldsets = (
        ('Service Information', {
            'fields': (
                'provider',
                'name',
                'service_category',
                'description',
            )
        }),
        ('Pricing', {
            'fields': (
                'price_type',
                'hourly_rate',
                'base_price',
            )
        }),
        ('Location', {
            'fields': (
                'location',
                'city',
                'country',
                'location_map',
            )
        }),
        ('Status', {
            'fields': (
                'is_active',
                'verification_status',
            )
        }),
        ('Metadata', {
            'fields': (
                'views_count',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['approve_services', 'reject_services', 'activate_services', 'deactivate_services']
    
    def provider_display(self, obj):
        """Display provider with link"""
        url = reverse('admin:providers_providerprofile_change', args=[obj.provider.provider_profile.id])
        name = obj.provider.get_full_name() or obj.provider.username
        return format_html('<a href="{}">{}</a>', url, name)
    provider_display.short_description = 'Provider'
    
    def price_display(self, obj):
        """Display price based on type"""
        if obj.price_type == 'hourly' and obj.hourly_rate:
            return format_html(
                '<span style="color:#27AE60;font-weight:bold;">{} ETB/hr</span>',
                obj.hourly_rate
            )
        elif obj.price_type == 'fixed' and obj.base_price:
            return format_html(
                '<span style="color:#27AE60;font-weight:bold;">{} ETB</span>',
                obj.base_price
            )
        return 'Not set'
    price_display.short_description = 'Price'
    
    def verification_badge(self, obj):
        """Display verification status badge"""
        colors = {
            'pending': '#F39C12',
            'approved': '#27AE60',
            'rejected': '#E74C3C',
        }
        color = colors.get(obj.verification_status, '#95A5A6')
        return format_html(
            '<span style="background:{};color:white;padding:3px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_verification_status_display().upper()
        )
    verification_badge.short_description = 'Status'
    
    def location_map(self, obj):
        """Display location on map (if available)"""
        if obj.latitude and obj.longitude:
            # Google Maps link
            maps_url = f"https://www.google.com/maps?q={obj.latitude},{obj.longitude}"
            return format_html(
                '<a href="{}" target="_blank" style="color:#3498DB;">📍 View on Map (Lat: {:.6f}, Lng: {:.6f})</a>',
                maps_url,
                obj.latitude,
                obj.longitude
            )
        return 'Location not set'
    location_map.short_description = 'Map Location'
    
    def approve_services(self, request, queryset):
        """Approve selected services"""
        updated = queryset.update(verification_status='approved')
        
        # Notify providers
        from notifications.models import Notification
        for service in queryset:
            Notification.objects.create(
                title='Service Approved! ✅',
                message=f'Your service "{service.name}" has been approved and is now visible to clients.',
                audience='custom'
            ).recipients.add(service.provider)
        
        self.message_user(
            request,
            f'Approved {updated} service(s)',
            messages.SUCCESS
        )
    approve_services.short_description = 'Approve selected services'
    
    def reject_services(self, request, queryset):
        """Reject selected services"""
        updated = queryset.update(verification_status='rejected')
        
        # Notify providers
        from notifications.models import Notification
        for service in queryset:
            Notification.objects.create(
                title='Service Rejected ❌',
                message=f'Your service "{service.name}" has been rejected. Please review and resubmit with corrections.',
                audience='custom'
            ).recipients.add(service.provider)
        
        self.message_user(
            request,
            f'Rejected {updated} service(s)',
            messages.WARNING
        )
    reject_services.short_description = 'Reject selected services'
    
    def activate_services(self, request, queryset):
        """Activate selected services"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'Activated {updated} service(s)',
            messages.SUCCESS
        )
    activate_services.short_description = 'Activate selected services'
    
    def deactivate_services(self, request, queryset):
        """Deactivate selected services"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'Deactivated {updated} service(s)',
            messages.WARNING
        )
    deactivate_services.short_description = 'Deactivate selected services'


@admin.register(ProviderVerification)
class ProviderVerificationAdmin(admin.ModelAdmin):
    list_display = [
        'user_display',
        'verification_type_badge',
        'status_badge',
        'file_preview',
        'uploaded_at',
        'reviewed_by',
        'quick_actions',
    ]
    
    list_filter = [
        'verification_type',
        'status',
        'uploaded_at',
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
    ]
    
    readonly_fields = [
        'user',
        'verification_type',
        'file_preview_large',
        'uploaded_at',
        'reviewed_at',
        'reviewed_by',
    ]
    
    fieldsets = (
        ('Verification Details', {
            'fields': (
                'user',
                'verification_type',
                'file_preview_large',
                'status',
                'rejection_reason',
                'expiry_date',
            )
        }),
        ('Review Information', {
            'fields': (
                'uploaded_at',
                'reviewed_at',
                'reviewed_by',
            ),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['approve_verifications', 'reject_verifications']
    
    def user_display(self, obj):
        """Display user with link"""
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        name = obj.user.get_full_name() or obj.user.username
        return format_html('<a href="{}">{}</a>', url, name)
    user_display.short_description = 'Provider'
    
    def verification_type_badge(self, obj):
        """Display verification type with icon"""
        icons = {
            'national_id': '🪪',
            'payment_proof': '💳',
        }
        icon = icons.get(obj.verification_type, '📄')
        return format_html(
            '{} {}',
            icon,
            obj.get_verification_type_display()
        )
    verification_type_badge.short_description = 'Type'
    
    def status_badge(self, obj):
        """Display status with colored badge"""
        colors = {
            'pending': '#F39C12',
            'approved': '#27AE60',
            'rejected': '#E74C3C',
        }
        color = colors.get(obj.status, '#95A5A6')
        return format_html(
            '<span style="background:{};color:white;padding:5px 12px;border-radius:3px;font-weight:bold;">{}</span>',
            color,
            obj.get_status_display().upper()
        )
    status_badge.short_description = 'Status'
    
    def file_preview(self, obj):
        """Display small file preview"""
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="max-width:50px;max-height:50px;border-radius:3px;"/></a>',
                obj.file.url,
                obj.file.url
            )
        return 'No file'
    file_preview.short_description = 'Preview'
    
    def file_preview_large(self, obj):
        """Display large file preview in detail view"""
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="max-width:600px;border:1px solid #ddd;border-radius:5px;"/></a><br><br><a href="{}" target="_blank" style="color:#3498DB;">Open in new tab</a>',
                obj.file.url,
                obj.file.url,
                obj.file.url
            )
        return 'No file uploaded'
    file_preview_large.short_description = 'Document Preview'
    
    def quick_actions(self, obj):
        """Display quick action buttons"""
        if obj.status == 'pending':
            return format_html(
                '<a class="button" href="{}?action=approve" style="background:#27AE60;color:white;padding:5px 10px;border-radius:3px;text-decoration:none;margin-right:5px;">✓ Approve</a>'
                '<a class="button" href="{}?action=reject" style="background:#E74C3C;color:white;padding:5px 10px;border-radius:3px;text-decoration:none;">✗ Reject</a>',
                reverse('admin:providers_providerverification_change', args=[obj.id]),
                reverse('admin:providers_providerverification_change', args=[obj.id])
            )
        return '-'
    quick_actions.short_description = 'Actions'
    
    def approve_verifications(self, request, queryset):
        """Approve selected verifications"""
        count = 0
        for verification in queryset.filter(status='pending'):
            verification.approve(request.user)
            count += 1
            
            # Send notification
            from notifications.models import Notification
            Notification.objects.create(
                title=f'{verification.get_verification_type_display()} Approved! ✅',
                message=f'Your {verification.get_verification_type_display()} has been verified and approved.',
                audience='custom'
            ).recipients.add(verification.user)
        
        self.message_user(
            request,
            f'Approved {count} verification(s)',
            messages.SUCCESS
        )
    approve_verifications.short_description = 'Approve selected verifications'
    
    def reject_verifications(self, request, queryset):
        """Reject selected verifications"""
        count = 0
        for verification in queryset.filter(status='pending'):
            verification.reject(request.user, 'Rejected by admin')
            count += 1
            
            # Send notification
            from notifications.models import Notification
            Notification.objects.create(
                title=f'{verification.get_verification_type_display()} Rejected ❌',
                message=f'Your {verification.get_verification_type_display()} has been rejected. Please upload a clearer image.',
                audience='custom'
            ).recipients.add(verification.user)
        
        self.message_user(
            request,
            f'Rejected {count} verification(s)',
            messages.WARNING
        )
    reject_verifications.short_description = 'Reject selected verifications'


@admin.register(CallLog)
class CallLogAdmin(admin.ModelAdmin):
    list_display = [
        'caller_display',
        'provider_display',
        'service_display',
        'timestamp',
        'duration_display',
    ]
    
    list_filter = [
        'timestamp',
    ]
    
    search_fields = [
        'caller__username',
        'caller__email',
        'provider__username',
        'provider__email',
        'service__name',
    ]
    
    readonly_fields = [
        'caller',
        'provider',
        'service',
        'timestamp',
        'duration',
    ]
    
    date_hierarchy = 'timestamp'
    
    def caller_display(self, obj):
        """Display caller with link"""
        url = reverse('admin:auth_user_change', args=[obj.caller.id])
        name = obj.caller.get_full_name() or obj.caller.username
        return format_html('<a href="{}">{}</a>', url, name)
    caller_display.short_description = 'Caller (Client)'
    
    def provider_display(self, obj):
        """Display provider with link"""
        url = reverse('admin:auth_user_change', args=[obj.provider.id])
        name = obj.provider.get_full_name() or obj.provider.username
        return format_html('<a href="{}">{}</a>', url, name)
    provider_display.short_description = 'Provider'
    
    def service_display(self, obj):
        """Display service with link"""
        if obj.service:
            url = reverse('admin:providers_providerservice_change', args=[obj.service.id])
            return format_html('<a href="{}">{}</a>', url, obj.service.name)
        return '-'
    service_display.short_description = 'Service'
    
    def duration_display(self, obj):
        """Display call duration"""
        if obj.duration:
            minutes = obj.duration // 60
            seconds = obj.duration % 60
            return f'{minutes}m {seconds}s'
        return 'Not tracked'
    duration_display.short_description = 'Duration'
    
    def has_add_permission(self, request):
        """Disable manual creation of call logs"""
        return False


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        'client_display',
        'provider_display',
        'service_display',
        'rating_display',
        'created_at',
    ]
    
    list_filter = [
        'rating',
        'created_at',
    ]
    
    search_fields = [
        'client__username',
        'provider__username',
        'service__name',
        'comment',
    ]
    
    readonly_fields = [
        'client',
        'provider',
        'service',
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('Review Details', {
            'fields': (
                'client',
                'provider',
                'service',
                'rating',
                'comment',
            )
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )
    
    def client_display(self, obj):
        """Display client with link"""
        url = reverse('admin:auth_user_change', args=[obj.client.id])
        name = obj.client.get_full_name() or obj.client.username
        return format_html('<a href="{}">{}</a>', url, name)
    client_display.short_description = 'Client'
    
    def provider_display(self, obj):
        """Display provider with link"""
        url = reverse('admin:auth_user_change', args=[obj.provider.id])
        name = obj.provider.get_full_name() or obj.provider.username
        return format_html('<a href="{}">{}</a>', url, name)
    provider_display.short_description = 'Provider'
    
    def service_display(self, obj):
        """Display service with link"""
        if obj.service:
            url = reverse('admin:providers_providerservice_change', args=[obj.service.id])
            return format_html('<a href="{}">{}</a>', url, obj.service.name)
        return '-'
    service_display.short_description = 'Service'
    
    def rating_display(self, obj):
        """Display rating with stars"""
        stars = '⭐' * obj.rating
        return format_html('<span style="color:#F39C12;font-size:16px;">{}</span>', stars)
    rating_display.short_description = 'Rating'


# Customize admin site header and title
admin.site.site_header = 'Mert Service Admin'
admin.site.site_title = 'Mert Service Admin Portal'
admin.site.index_title = 'Welcome to Mert Service Administration'


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'order', 'subcategory_count']
    ordering = ['order']

    def subcategory_count(self, obj):
        return obj.subcategories.count()
    subcategory_count.short_description = 'Sub-categories'


@admin.register(ServiceSubCategory)
class ServiceSubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'slug', 'icon']
    list_filter = ['category']
    search_fields = ['name', 'category__name']
    ordering = ['category__order', 'name']
