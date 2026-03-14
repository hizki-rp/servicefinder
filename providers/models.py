from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from math import radians, cos, sin, asin, sqrt
import random
import string


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees).
    Returns distance in kilometers.
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    
    return c * r


class OTPVerification(models.Model):
    """
    OTP verification for phone-based authentication.
    Used for guest users who want to leave reviews.
    """
    phone_number = models.CharField(max_length=20)
    otp_code = models.CharField(max_length=6)
    name = models.CharField(max_length=100, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone_number', '-created_at']),
        ]
    
    def is_expired(self):
        """Check if OTP has expired (10 minutes)"""
        return timezone.now() > self.expires_at
    
    def generate_otp(self):
        """Generate a 6-digit OTP code"""
        self.otp_code = ''.join(random.choices(string.digits, k=6))
        self.expires_at = timezone.now() + timezone.timedelta(minutes=10)
        self.save()
        return self.otp_code
    
    @classmethod
    def create_otp(cls, phone_number, name=''):
        """Create new OTP for phone number"""
        otp = cls.objects.create(
            phone_number=phone_number,
            name=name,
            expires_at=timezone.now() + timezone.timedelta(minutes=10)
        )
        otp.generate_otp()
        return otp
    
    def __str__(self):
        return f"OTP for {self.phone_number} - {self.otp_code}"


class UserProfile(models.Model):
    """
    Extended profile for regular users (reviewers).
    Stores phone number for OTP-authenticated users.
    Can be upgraded to ProviderProfile.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='user_profile'
    )
    phone_number = models.CharField(max_length=20, unique=True)
    is_phone_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def can_upgrade_to_provider(self):
        """Check if user can upgrade to provider"""
        return not hasattr(self.user, 'provider_profile')
    
    def __str__(self):
        return f"{self.user.username} - {self.phone_number}"


class ProviderProfile(models.Model):
    """
    Extended profile for service providers.
    Replaces UserDashboard for provider-specific data.
    """
    SUBSCRIPTION_CHOICES = [
        ('trial', 'Trial (1 Month Free)'),
        ('active', 'Active'),
        ('expired', 'Expired'),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='provider_profile'
    )
    
    # Verification Status
    national_id_verified = models.BooleanField(
        default=False,
        help_text="National ID has been verified by admin"
    )
    payment_verified = models.BooleanField(
        default=False,
        help_text="Payment proof has been verified by admin (optional for trial)"
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Provider is fully verified and visible to clients"
    )
    
    # Admin Control
    is_active = models.BooleanField(
        default=True,
        help_text="Provider account is active (not suspended)"
    )
    suspended_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the provider was suspended"
    )
    suspension_reason = models.TextField(
        blank=True,
        help_text="Reason for suspension"
    )
    
    # Trial Period (1-Month Free)
    trial_start_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the 1-month free trial started"
    )
    trial_expiry_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the 1-month free trial expires"
    )
    trial_notification_sent = models.BooleanField(
        default=False,
        help_text="Whether expiry notification has been sent"
    )
    
    # Service Limits (Immutable Business Rule: 3-Service Cap)
    services_count = models.IntegerField(
        default=0,
        help_text="Current number of active services"
    )
    max_services_allowed = models.IntegerField(
        default=3,
        help_text="Maximum services allowed (admin can override)"
    )
    
    # KYC Images (uploaded during onboarding)
    selfie_image = models.FileField(
        upload_to='kyc/selfies/%Y/%m/',
        null=True,
        blank=True,
        help_text="Real-time selfie taken during onboarding"
    )
    id_image = models.FileField(
        upload_to='kyc/ids/%Y/%m/',
        null=True,
        blank=True,
        help_text="Government-issued ID photo"
    )

    # Contact & Location
    phone_number = models.CharField(max_length=20)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Latitude coordinate (e.g., 9.032000)"
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Longitude coordinate (e.g., 38.757800)"
    )
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='Ethiopia')
    
    # Rating & Reviews
    rating = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)]
    )
    total_reviews = models.IntegerField(default=0)
    
    # Subscription (from original UserDashboard)
    subscription_status = models.CharField(
        max_length=10,
        choices=SUBSCRIPTION_CHOICES,
        default='trial'
    )
    subscription_end_date = models.DateField(null=True, blank=True)
    total_paid = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0
    )
    months_subscribed = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Provider Profile"
        verbose_name_plural = "Provider Profiles"
        indexes = [
            models.Index(fields=['is_verified']),
            models.Index(fields=['city']),
            models.Index(fields=['subscription_status']),
            models.Index(fields=['trial_expiry_date']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - Provider"
    
    def save(self, *args, **kwargs):
        """Auto-set trial dates on creation"""
        if not self.pk and not self.trial_start_date:
            # New provider gets 1-month free trial
            from datetime import timedelta
            self.trial_start_date = timezone.now()
            self.trial_expiry_date = timezone.now() + timedelta(days=30)
            self.subscription_status = 'trial'
        super().save(*args, **kwargs)
    
    @property
    def is_trial_active(self):
        """Check if provider is in active trial period"""
        if not self.trial_start_date or not self.trial_expiry_date:
            return False
        return timezone.now() < self.trial_expiry_date
    
    @property
    def days_until_trial_expiry(self):
        """Calculate days remaining in trial"""
        if not self.trial_expiry_date:
            return None
        delta = self.trial_expiry_date - timezone.now()
        return max(0, delta.days)
    
    @property
    def is_visible_to_clients(self):
        """
        Provider is visible if:
        1. National ID verified AND
        2. (Payment verified OR in active trial)
        """
        return (
            self.national_id_verified and
            (self.payment_verified or self.is_trial_active)
        )
    
    def can_create_service(self):
        """Check if provider can create more services (3-Service Cap Rule)"""
        return self.services_count < self.max_services_allowed
    
    def update_rating(self):
        """Recalculate average rating from reviews"""
        from .models import Review
        reviews = Review.objects.filter(provider=self.user)
        if reviews.exists():
            self.rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.total_reviews = reviews.count()
            self.save(update_fields=['rating', 'total_reviews'])
    
    def distance_to(self, lat, lng):
        """Calculate distance to given coordinates in kilometers"""
        if self.latitude and self.longitude:
            return haversine_distance(
                float(self.latitude),
                float(self.longitude),
                float(lat),
                float(lng)
            )
        return None


class ProviderService(models.Model):
    """
    Individual service offering by a provider.
    Replaces University model - stripped of academic fields.
    """
    PRICE_TYPE_CHOICES = [
        ('hourly', 'Hourly Rate'),
        ('fixed', 'Fixed Price'),
    ]
    
    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    # Provider relationship
    provider = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='services'
    )
    
    # Service Details
    name = models.CharField(
        max_length=200,
        help_text="e.g., 'Professional Plumbing Services'"
    )
    service_category = models.CharField(
        max_length=100,
        help_text="e.g., 'Plumber', 'Electrician', 'Cleaner'"
    )
    description = models.TextField()
    
    # Pricing
    price_type = models.CharField(
        max_length=20,
        choices=PRICE_TYPE_CHOICES,
        default='hourly'
    )
    hourly_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Hourly rate in ETB"
    )
    base_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Fixed base price in ETB"
    )
    
    # Location
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Latitude coordinate (e.g., 9.032000)"
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Longitude coordinate (e.g., 38.757800)"
    )
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Ethiopia')
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Service is active and visible"
    )
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default='pending'
    )
    
    # Admin Control
    hidden_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the service was hidden by admin"
    )
    hidden_reason = models.TextField(
        blank=True,
        help_text="Reason for hiding service"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "Provider Service"
        verbose_name_plural = "Provider Services"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['provider', 'is_active']),
            models.Index(fields=['service_category']),
            models.Index(fields=['city']),
            models.Index(fields=['verification_status']),
        ]
    
    def __str__(self):
        return f"{self.name} by {self.provider.get_full_name() or self.provider.username}"
    
    def save(self, *args, **kwargs):
        # Update provider's service count
        if self.pk is None:  # New service
            profile = self.provider.provider_profile
            if not profile.can_create_service():
                raise ValueError(
                    f"Provider has reached maximum services limit ({profile.max_services_allowed})"
                )
            profile.services_count += 1
            profile.save(update_fields=['services_count'])
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Update provider's service count
        profile = self.provider.provider_profile
        profile.services_count = max(0, profile.services_count - 1)
        profile.save(update_fields=['services_count'])
        super().delete(*args, **kwargs)
    
    def distance_to(self, lat, lng):
        """Calculate distance to given coordinates in kilometers"""
        if self.latitude and self.longitude:
            return haversine_distance(
                float(self.latitude),
                float(self.longitude),
                float(lat),
                float(lng)
            )
        return None


class ProviderVerification(models.Model):
    """
    Provider verification documents (National ID and Payment Proof).
    Replaces DocumentSubmission model.
    """
    VERIFICATION_TYPE_CHOICES = [
        ('national_id', 'National ID'),
        ('payment_proof', 'Payment Proof'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='verifications'
    )
    
    verification_type = models.CharField(
        max_length=20,
        choices=VERIFICATION_TYPE_CHOICES
    )
    
    file = models.FileField(
        upload_to='verifications/%Y/%m/',
        help_text="Upload National ID or Payment Proof screenshot"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    rejection_reason = models.TextField(
        blank=True,
        help_text="Reason for rejection (if applicable)"
    )
    
    expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text="ID expiry date (for National ID only)"
    )
    
    # Review tracking
    uploaded_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_providers'
    )
    
    class Meta:
        verbose_name = "Provider Verification"
        verbose_name_plural = "Provider Verifications"
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['user', 'verification_type']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_verification_type_display()} ({self.status})"
    
    def approve(self, admin_user):
        """Approve verification and update provider profile"""
        self.status = 'approved'
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.save()
        
        # Update provider profile
        profile = self.user.provider_profile
        if self.verification_type == 'national_id':
            profile.national_id_verified = True
        elif self.verification_type == 'payment_proof':
            profile.payment_verified = True
        
        # Check if fully verified
        if profile.national_id_verified and profile.payment_verified:
            profile.is_verified = True
        
        profile.save()
    
    def reject(self, admin_user, reason):
        """Reject verification"""
        self.status = 'rejected'
        self.rejection_reason = reason
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.save()


class CallLog(models.Model):
    """
    Track calls made to providers (Immutable Business Rule: Call Tracking).
    Must be logged before opening device dialer.
    """
    caller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='calls_made'
    )
    provider = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='calls_received'
    )
    service = models.ForeignKey(
        ProviderService,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    timestamp = models.DateTimeField(auto_now_add=True)
    duration = models.IntegerField(
        null=True,
        blank=True,
        help_text="Call duration in seconds (future feature)"
    )
    
    class Meta:
        verbose_name = "Call Log"
        verbose_name_plural = "Call Logs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['caller', 'timestamp']),
            models.Index(fields=['provider', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.caller.username} called {self.provider.username} at {self.timestamp}"


class Review(models.Model):
    """
    Client reviews for providers.
    """
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews_given'
    )
    provider = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews_received'
    )
    service = models.ForeignKey(
        ProviderService,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    comment = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        ordering = ['-created_at']
        unique_together = ['client', 'provider', 'service']
        indexes = [
            models.Index(fields=['provider', 'rating']),
        ]
    
    def __str__(self):
        return f"{self.client.username} → {self.provider.username}: {self.rating}★"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update provider rating
        self.provider.provider_profile.update_rating()


# ============================================
# SIGNALS - Auto-sync verification states
# ============================================

@receiver(post_save, sender=ProviderProfile)
def sync_verification_documents(sender, instance, **kwargs):
    """
    Signal: When ProviderProfile.is_verified is set to True,
    automatically approve all associated ProviderVerification records.
    
    This ensures UI consistency - if the profile is verified,
    all documents are considered verified.
    """
    if instance.is_verified:
        # Auto-approve all pending verification documents
        ProviderVerification.objects.filter(
            user=instance.user,
            status='pending'
        ).update(
            status='approved',
            reviewed_at=timezone.now()
        )
        
        # Ensure individual verification flags are set
        if not instance.national_id_verified:
            instance.national_id_verified = True
            instance.save(update_fields=['national_id_verified'])
        
        # Note: payment_verified can remain False during trial
        # The is_verified flag is the single source of truth


@receiver(post_save, sender=ProviderVerification)
def auto_verify_profile_on_document_approval(sender, instance, **kwargs):
    """
    Signal: When a ProviderVerification document is approved,
    automatically update the ProviderProfile verification status.
    
    This is the "Verification Bridge" - when admin approves documents,
    the master profile is automatically updated.
    
    Logic:
    - If National ID is approved → set national_id_verified = True
    - If National ID is approved AND (Payment is approved OR in trial) → set is_verified = True
    """
    if instance.status == 'approved':
        try:
            profile = instance.user.provider_profile
            
            # Update individual verification flags
            if instance.verification_type == 'national_id':
                if not profile.national_id_verified:
                    profile.national_id_verified = True
                    profile.save(update_fields=['national_id_verified'])
                
                # Check if profile should be fully verified
                # Rule: National ID verified AND (Payment verified OR in active trial)
                if not profile.is_verified:
                    if profile.payment_verified or profile.is_trial_active:
                        profile.is_verified = True
                        profile.save(update_fields=['is_verified'])
                        print(f"✅ Auto-verified profile for {instance.user.username}")
                        
                        # Send push notification
                        try:
                            from .notifications import send_verification_approved_notification
                            result = send_verification_approved_notification(profile)
                            if result.get('success'):
                                print(f"📱 Sent verification notification to {instance.user.username}")
                            else:
                                print(f"⚠️ Failed to send push notification: {result.get('reason')}")
                        except Exception as e:
                            print(f"⚠️ Error sending push notification: {e}")
            
            elif instance.verification_type == 'payment_proof':
                if not profile.payment_verified:
                    profile.payment_verified = True
                    profile.save(update_fields=['payment_verified'])
                
                # Check if profile should be fully verified
                if not profile.is_verified and profile.national_id_verified:
                    profile.is_verified = True
                    profile.save(update_fields=['is_verified'])
                    print(f"✅ Auto-verified profile for {instance.user.username}")
                    
                    # Send push notification
                    try:
                        from .notifications import send_verification_approved_notification
                        result = send_verification_approved_notification(profile)
                        if result.get('success'):
                            print(f"📱 Sent verification notification to {instance.user.username}")
                        else:
                            print(f"⚠️ Failed to send push notification: {result.get('reason')}")
                    except Exception as e:
                        print(f"⚠️ Error sending push notification: {e}")
        
        except ProviderProfile.DoesNotExist:
            print(f"⚠️ No provider profile found for user {instance.user.username}")
            pass



# ============================================
# BROADCAST NOTIFICATION SYSTEM
# ============================================

class PushToken(models.Model):
    """
    Store Expo push notification tokens for providers.
    """
    DEVICE_TYPE_CHOICES = [
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('web', 'Web'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='push_tokens'
    )
    token = models.CharField(
        max_length=255,
        unique=True,
        help_text="Expo push token"
    )
    device_type = models.CharField(
        max_length=20,
        choices=DEVICE_TYPE_CHOICES,
        default='android'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Push Token"
        verbose_name_plural = "Push Tokens"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.device_type} - {self.token[:20]}..."


class BroadcastNotification(models.Model):
    """
    Broadcast notifications to filtered providers.
    """
    TARGET_AUDIENCE_CHOICES = [
        ('all', 'All Providers'),
        ('verified', 'Verified Providers'),
        ('pending', 'Pending Providers'),
        ('trial', 'Trial Providers'),
        ('active', 'Active Providers'),
        ('suspended', 'Suspended Providers'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='broadcasts'
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Filtering
    target_audience = models.CharField(
        max_length=20,
        choices=TARGET_AUDIENCE_CHOICES,
        default='all'
    )
    category_filter = models.CharField(
        max_length=100,
        blank=True,
        help_text="Filter by service category (optional)"
    )
    city_filter = models.CharField(
        max_length=100,
        blank=True,
        help_text="Filter by city (optional)"
    )
    
    # Delivery tracking
    sent_count = models.IntegerField(
        default=0,
        help_text="Number of notifications sent"
    )
    success_count = models.IntegerField(
        default=0,
        help_text="Number of successful deliveries"
    )
    failure_count = models.IntegerField(
        default=0,
        help_text="Number of failed deliveries"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Broadcast Notification"
        verbose_name_plural = "Broadcast Notifications"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.get_target_audience_display()} ({self.status})"
    
    def get_target_providers(self):
        """
        Get filtered list of providers based on target_audience.
        Returns queryset of ProviderProfile objects.
        """
        providers = ProviderProfile.objects.select_related('user').all()
        
        # Apply audience filter
        if self.target_audience == 'verified':
            providers = providers.filter(is_verified=True)
        elif self.target_audience == 'pending':
            providers = providers.filter(is_verified=False)
        elif self.target_audience == 'trial':
            providers = providers.filter(
                trial_expiry_date__gt=timezone.now()
            )
        elif self.target_audience == 'active':
            providers = providers.filter(is_active=True)
        elif self.target_audience == 'suspended':
            providers = providers.filter(is_active=False)
        
        # Apply category filter
        if self.category_filter:
            provider_ids = ProviderService.objects.filter(
                service_category__icontains=self.category_filter
            ).values_list('provider_id', flat=True).distinct()
            providers = providers.filter(user_id__in=provider_ids)
        
        # Apply city filter
        if self.city_filter:
            providers = providers.filter(city__icontains=self.city_filter)
        
        return providers
