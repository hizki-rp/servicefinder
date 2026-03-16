from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    ProviderProfile,
    ProviderService,
    ProviderVerification,
    CallLog,
    Review,
    OTPVerification,
    UserProfile,
)


class UserSerializer(serializers.ModelSerializer):
    """Basic user information"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name']
        read_only_fields = ['id', 'username']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class ProviderProfileSerializer(serializers.ModelSerializer):
    """Provider profile with verification status"""
    user = UserSerializer(read_only=True)
    is_trial_active = serializers.ReadOnlyField()
    days_until_trial_expiry = serializers.ReadOnlyField()
    selfie_url = serializers.SerializerMethodField()
    id_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProviderProfile
        fields = [
            'id',
            'user',
            'phone_number',
            'city',
            'country',
            'latitude',
            'longitude',
            'national_id_verified',
            'payment_verified',
            'is_verified',
            'is_trial_active',
            'days_until_trial_expiry',
            'services_count',
            'max_services_allowed',
            'rating',
            'total_reviews',
            'subscription_status',
            'subscription_end_date',
            'selfie_url',
            'id_image_url',
            'created_at',
        ]
        read_only_fields = [
            'national_id_verified',
            'payment_verified',
            'is_verified',
            'is_trial_active',
            'days_until_trial_expiry',
            'services_count',
            'rating',
            'total_reviews',
        ]
    
    def get_selfie_url(self, obj):
        request = self.context.get('request')
        if obj.selfie_image and request:
            return request.build_absolute_uri(obj.selfie_image.url)
        return None
    
    def get_id_image_url(self, obj):
        request = self.context.get('request')
        if obj.id_image and request:
            return request.build_absolute_uri(obj.id_image.url)
        return None


class ProviderServiceListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for service listings"""
    provider_id = serializers.SerializerMethodField()
    provider_name = serializers.SerializerMethodField()
    provider_rating = serializers.SerializerMethodField()
    provider_reviews = serializers.SerializerMethodField()
    provider_phone = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()
    
    class Meta:
        model = ProviderService
        fields = [
            'id',
            'name',
            'service_category',
            'description',
            'price_type',
            'hourly_rate',
            'base_price',
            'city',
            'latitude',
            'longitude',
            'provider_id',
            'provider_name',
            'provider_rating',
            'provider_reviews',
            'provider_phone',
            'distance',
            'views_count',
            'created_at',
        ]
    
    def get_provider_id(self, obj):
        return obj.provider.id

    def get_provider_name(self, obj):
        return obj.provider.get_full_name() or obj.provider.username
    
    def get_provider_rating(self, obj):
        try:
            return obj.provider.provider_profile.rating
        except Exception:
            return 0.0
    
    def get_provider_reviews(self, obj):
        try:
            return obj.provider.provider_profile.total_reviews
        except Exception:
            return 0

    def get_provider_phone(self, obj):
        try:
            return obj.provider.provider_profile.phone_number
        except Exception:
            return None
    
    def get_distance(self, obj):
        """Distance in kilometers (calculated in viewset)"""
        return getattr(obj, 'distance', None)


class ProviderServiceDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single service view"""
    provider = ProviderProfileSerializer(source='provider.provider_profile', read_only=True)
    
    class Meta:
        model = ProviderService
        fields = [
            'id',
            'provider',
            'name',
            'service_category',
            'description',
            'price_type',
            'hourly_rate',
            'base_price',
            'city',
            'country',
            'latitude',
            'longitude',
            'is_active',
            'verification_status',
            'views_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['verification_status', 'views_count']


class ProviderServiceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating services"""
    
    class Meta:
        model = ProviderService
        fields = [
            'name',
            'service_category',
            'description',
            'price_type',
            'hourly_rate',
            'base_price',
            'city',
            'country',
            'latitude',
            'longitude',
        ]
    
    def validate(self, data):
        """Validate service creation"""
        # Check if provider can create more services (3-Service Cap)
        request = self.context.get('request')
        if request and hasattr(request.user, 'provider_profile'):
            profile = request.user.provider_profile
            if not profile.can_create_service():
                raise serializers.ValidationError(
                    f"You have reached the maximum service limit ({profile.max_services_allowed}). "
                    "Contact admin to increase your limit."
                )
        
        # Validate pricing
        if data['price_type'] == 'hourly' and not data.get('hourly_rate'):
            raise serializers.ValidationError("Hourly rate is required for hourly pricing")
        if data['price_type'] == 'fixed' and not data.get('base_price'):
            raise serializers.ValidationError("Base price is required for fixed pricing")
        
        # Validate coordinates
        if not data.get('latitude') or not data.get('longitude'):
            raise serializers.ValidationError("Latitude and longitude are required")
        
        return data
    
    def create(self, validated_data):
        """Create service with location"""
        validated_data['provider'] = self.context['request'].user
        return super().create(validated_data)


class ProviderVerificationSerializer(serializers.ModelSerializer):
    """Serializer for verification documents"""
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProviderVerification
        fields = [
            'id',
            'verification_type',
            'file_url',
            'status',
            'rejection_reason',
            'expiry_date',
            'uploaded_at',
            'reviewed_at',
        ]
        read_only_fields = ['status', 'reviewed_at']
    
    def get_file_url(self, obj):
        """Return full URL for file"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class CallLogSerializer(serializers.ModelSerializer):
    """Serializer for call tracking"""
    caller_name = serializers.SerializerMethodField()
    provider_name = serializers.SerializerMethodField()
    service_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CallLog
        fields = [
            'id',
            'caller_name',
            'provider_name',
            'service_name',
            'timestamp',
            'duration',
        ]
        read_only_fields = ['timestamp']
    
    def get_caller_name(self, obj):
        return obj.caller.get_full_name() or obj.caller.username
    
    def get_provider_name(self, obj):
        return obj.provider.get_full_name() or obj.provider.username
    
    def get_service_name(self, obj):
        return obj.service.name if obj.service else None


class CallLogCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating call logs"""
    provider_id = serializers.IntegerField(write_only=True)
    service_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = CallLog
        fields = ['provider_id', 'service_id']
    
    def create(self, validated_data):
        """Create call log"""
        provider_id = validated_data.pop('provider_id')
        service_id = validated_data.pop('service_id', None)
        
        try:
            provider = User.objects.get(id=provider_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("Provider not found")
        
        service = None
        if service_id:
            try:
                service = ProviderService.objects.get(id=service_id)
            except ProviderService.DoesNotExist:
                pass
        
        return CallLog.objects.create(
            caller=self.context['request'].user,
            provider=provider,
            service=service
        )


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for reviews"""
    client_name = serializers.SerializerMethodField()
    provider_name = serializers.SerializerMethodField()
    service_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id',
            'client_name',
            'provider_name',
            'service_name',
            'rating',
            'comment',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_client_name(self, obj):
        return obj.client.get_full_name() or obj.client.username
    
    def get_provider_name(self, obj):
        return obj.provider.get_full_name() or obj.provider.username
    
    def get_service_name(self, obj):
        return obj.service.name if obj.service else None


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating reviews"""
    provider_id = serializers.IntegerField(write_only=True)
    service_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = Review
        fields = ['provider_id', 'service_id', 'rating', 'comment']
    
    def validate_rating(self, value):
        """Validate rating is between 1 and 5"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value
    
    def create(self, validated_data):
        """Create review"""
        provider_id = validated_data.pop('provider_id')
        service_id = validated_data.pop('service_id', None)
        
        try:
            provider = User.objects.get(id=provider_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("Provider not found")
        
        service = None
        if service_id:
            try:
                service = ProviderService.objects.get(id=service_id)
            except ProviderService.DoesNotExist:
                pass
        
        # Check if review already exists
        if Review.objects.filter(
            client=self.context['request'].user,
            provider=provider,
            service=service
        ).exists():
            raise serializers.ValidationError("You have already reviewed this provider/service")
        
        return Review.objects.create(
            client=self.context['request'].user,
            provider=provider,
            service=service,
            **validated_data
        )


class AuthUserSerializer(serializers.ModelSerializer):
    """Extended user serializer for authentication response"""
    is_provider = serializers.SerializerMethodField()
    is_verified = serializers.SerializerMethodField()
    provider_profile = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_staff',
            'is_provider',
            'is_verified',
            'provider_profile',
        ]
    
    def get_is_provider(self, obj):
        """Check if user is a provider"""
        return hasattr(obj, 'provider_profile')
    
    def get_is_verified(self, obj):
        """Check if provider is verified"""
        if hasattr(obj, 'provider_profile'):
            return obj.provider_profile.is_verified
        return False
    
    def get_provider_profile(self, obj):
        """Return provider profile if exists"""
        if hasattr(obj, 'provider_profile'):
            return ProviderProfileSerializer(obj.provider_profile).data
        return None


class ServiceCategorySerializer(serializers.Serializer):
    """Serializer for service categories"""
    category = serializers.CharField()
    count = serializers.IntegerField()
    icon = serializers.CharField(required=False)



class OTPRequestSerializer(serializers.Serializer):
    """Serializer for OTP request"""
    phone_number = serializers.CharField(max_length=20)
    name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    def validate_phone_number(self, value):
        """Validate phone number format"""
        # Basic validation - can be enhanced
        if not value.strip():
            raise serializers.ValidationError("Phone number is required")
        return value.strip()


class OTPVerifySerializer(serializers.Serializer):
    """Serializer for OTP verification"""
    phone_number = serializers.CharField(max_length=20)
    otp_code = serializers.CharField(max_length=6)
    name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    def validate_otp_code(self, value):
        """Validate OTP code format"""
        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError("OTP must be 6 digits")
        return value


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile (reviewers)"""
    user = UserSerializer(read_only=True)
    can_upgrade = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = [
            'id',
            'user',
            'phone_number',
            'is_phone_verified',
            'can_upgrade',
            'created_at',
        ]
        read_only_fields = ['is_phone_verified', 'created_at']
    
    def get_can_upgrade(self, obj):
        """Check if user can upgrade to provider"""
        return obj.can_upgrade_to_provider()
