from django.contrib import admin
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Q
from django.utils.html import format_html
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import path
from django import forms
from datetime import datetime, timedelta
from .models import Payment
from universities.models import UserDashboard

def extend_subscription_by_month(modeladmin, request, queryset):
    """
    Admin action to extend subscription by 1 month for users with successful payments.
    Extends from current subscription_end_date if it exists and is in the future, otherwise from today.
    Only processes payments with status='success' (paid users).
    """
    # Filter to only successful payments
    successful_payments = queryset.filter(status='success')
    
    if not successful_payments.exists():
        modeladmin.message_user(
            request,
            "No successful payments found in selection. Only payments with status='success' will be processed.",
            level=messages.WARNING
        )
        return
    
    # Get unique users from successful payments
    users = successful_payments.values_list('user', flat=True).distinct()
    
    extended_count = 0
    errors = []
    today = timezone.now().date()
    
    for user_id in users:
        try:
            user = User.objects.get(id=user_id)
            
            # Get or create user dashboard
            dashboard, created = UserDashboard.objects.get_or_create(user=user)
            
            # Determine the start date for extension
            # If user has a subscription_end_date that's in the future, extend from that date
            # Otherwise, extend from today
            if dashboard.subscription_end_date and dashboard.subscription_end_date > today:
                # Extend from existing end date
                new_end_date = dashboard.subscription_end_date + timedelta(days=30)
            else:
                # Extend from today
                new_end_date = today + timedelta(days=30)
            
            dashboard.subscription_end_date = new_end_date
            
            # Set user as verified and active
            dashboard.is_verified = True
            dashboard.subscription_status = 'active'
            dashboard.save()
            
            extended_count += 1
            
        except Exception as e:
            errors.append(f"Error extending subscription for user {user_id}: {str(e)}")
    
    # Show success message
    if extended_count > 0:
        modeladmin.message_user(
            request,
            f"Successfully extended subscription by 1 month for {extended_count} user(s). "
            f"Subscriptions extended from current end date (or today if no active subscription).",
            level=messages.SUCCESS
        )
    
    # Show errors if any
    if errors:
        for error in errors:
            modeladmin.message_user(request, error, level=messages.ERROR)

extend_subscription_by_month.short_description = "Extend subscription by 1 month for selected paid users"

class SetSubscriptionDateForm(forms.Form):
    subscription_end_date = forms.DateField(
        label='Subscription End Date',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'vDateField'}),
        help_text='Set subscription end date for all paid users (users with successful payments)'
    )

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'status', 'payment_date', 'subscription_end_date', 'tx_ref']
    list_filter = ['status', 'payment_date']
    search_fields = ['user__username', 'user__email', 'tx_ref']
    readonly_fields = ['payment_date']
    ordering = ['-payment_date']
    actions = [extend_subscription_by_month]
    
    def get_queryset(self, request):
        """Optimize query by prefetching related dashboard data"""
        qs = super().get_queryset(request)
        return qs.select_related('user', 'user__dashboard')
    
    def get_urls(self):
        """Add custom URL for setting subscription dates"""
        urls = super().get_urls()
        custom_urls = [
            path(
                'set-subscription-date/',
                self.admin_site.admin_view(self.set_subscription_date_view),
                name='payments_payment_set_subscription_date',
            ),
        ]
        return custom_urls + urls
    
    def set_subscription_date_view(self, request):
        """Custom admin view to set subscription end date for all paid users"""
        if request.method == 'POST':
            form = SetSubscriptionDateForm(request.POST)
            if form.is_valid():
                subscription_end_date = form.cleaned_data['subscription_end_date']
                
                # Get all users with successful payments
                successful_payments = Payment.objects.filter(status='success')
                user_ids = successful_payments.values_list('user', flat=True).distinct()
                
                updated_count = 0
                created_count = 0
                errors = []
                
                for user_id in user_ids:
                    try:
                        user = User.objects.get(id=user_id)
                        dashboard, created = UserDashboard.objects.get_or_create(user=user)
                        
                        dashboard.subscription_end_date = subscription_end_date
                        dashboard.subscription_status = 'active'
                        dashboard.is_verified = True
                        dashboard.save()
                        
                        if created:
                            created_count += 1
                        updated_count += 1
                    except Exception as e:
                        errors.append(f"Error updating user {user_id}: {str(e)}")
                
                if updated_count > 0:
                    self.message_user(
                        request,
                        f"Successfully set subscription end date to {subscription_end_date} for {updated_count} user(s). "
                        f"{f'Created {created_count} new dashboard(s).' if created_count > 0 else ''}",
                        level=messages.SUCCESS
                    )
                
                if errors:
                    for error in errors:
                        self.message_user(request, error, level=messages.ERROR)
                
                return redirect('admin:payments_payment_changelist')
        else:
            form = SetSubscriptionDateForm()
            # Set default date to 2025-12-27 as example
            form.fields['subscription_end_date'].initial = '2025-12-27'
        
        # Get count of paid users
        paid_users_count = Payment.objects.filter(status='success').values('user').distinct().count()
        
        context = {
            **self.admin_site.each_context(request),
            'title': 'Set Subscription End Date for All Paid Users',
            'form': form,
            'paid_users_count': paid_users_count,
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        }
        
        return render(request, 'admin/payments/set_subscription_date.html', context)
    
    def subscription_end_date(self, obj):
        """Display the subscription end date from user's dashboard"""
        try:
            dashboard = obj.user.dashboard
            if dashboard.subscription_end_date:
                # Add color coding based on status
                if dashboard.subscription_status == 'active':
                    if dashboard.subscription_end_date >= timezone.now().date():
                        return format_html(
                            '<span style="color: green; font-weight: bold;">{}</span>',
                            dashboard.subscription_end_date.strftime('%Y-%m-%d')
                        )
                    else:
                        return format_html(
                            '<span style="color: red; font-weight: bold;">{} (Expired)</span>',
                            dashboard.subscription_end_date.strftime('%Y-%m-%d')
                        )
                elif dashboard.subscription_status == 'expired':
                    return format_html(
                        '<span style="color: red;">{}</span>',
                        dashboard.subscription_end_date.strftime('%Y-%m-%d')
                    )
                else:
                    return dashboard.subscription_end_date.strftime('%Y-%m-%d')
            else:
                return format_html('<span style="color: gray;">No subscription</span>')
        except UserDashboard.DoesNotExist:
            return format_html('<span style="color: gray;">No dashboard</span>')
    
    subscription_end_date.short_description = 'Subscription End Date'
    subscription_end_date.admin_order_field = 'user__dashboard__subscription_end_date'
    
    def changelist_view(self, request, extra_context=None):
        # Calculate earnings statistics
        now = timezone.now()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        
        # Current month earnings
        current_month_payments = Payment.objects.filter(
            status='success',
            payment_date__gte=current_month_start
        )
        current_month_total = current_month_payments.aggregate(Sum('amount'))['amount__sum'] or 0
        current_month_count = current_month_payments.count()
        
        # Last month earnings
        last_month_payments = Payment.objects.filter(
            status='success',
            payment_date__gte=last_month_start,
            payment_date__lt=current_month_start
        )
        last_month_total = last_month_payments.aggregate(Sum('amount'))['amount__sum'] or 0
        last_month_count = last_month_payments.count()
        
        # Total earnings
        total_earnings = Payment.objects.filter(status='success').aggregate(Sum('amount'))['amount__sum'] or 0
        total_payments = Payment.objects.filter(status='success').count()
        
        # Active subscribers (paid in last 30 days)
        thirty_days_ago = now - timedelta(days=30)
        active_subscribers = Payment.objects.filter(
            status='success',
            payment_date__gte=thirty_days_ago
        ).values('user').distinct().count()
        
        extra_context = extra_context or {}
        extra_context.update({
            'earnings_stats': {
                'current_month_total': current_month_total,
                'current_month_count': current_month_count,
                'last_month_total': last_month_total,
                'last_month_count': last_month_count,
                'total_earnings': total_earnings,
                'total_payments': total_payments,
                'active_subscribers': active_subscribers,
                'current_month_name': current_month_start.strftime('%B %Y'),
                'last_month_name': last_month_start.strftime('%B %Y'),
            },
            'set_subscription_date_url': 'set-subscription-date/',
        })
        
        return super().changelist_view(request, extra_context=extra_context)