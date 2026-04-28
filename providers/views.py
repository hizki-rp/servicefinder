from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
import logging

logger = logging.getLogger(__name__)
from .models import (
    ProviderProfile,
    ProviderService,
    ProviderVerification,
    CallLog,
    Review,
    haversine_distance,
    OTPVerification,
    UserProfile,
    ServiceCategory,
    ServiceSubCategory,
)
from .serializers import (
    ProviderProfileSerializer,
    ProviderServiceListSerializer,
    ProviderServiceDetailSerializer,
    ProviderServiceCreateSerializer,
    ProviderVerificationSerializer,
    CallLogSerializer,
    CallLogCreateSerializer,
    ReviewSerializer,
    ReviewCreateSerializer,
    AuthUserSerializer,
    ServiceCategorySerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    UserProfileSerializer,
)


class ProviderProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for provider profiles.
    """
    queryset = ProviderProfile.objects.select_related('user').all()
    serializer_class = ProviderProfileSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'city']
    filterset_fields = ['is_verified', 'city', 'subscription_status']
    
    def get_queryset(self):
        """Filter to show only verified providers to non-owners"""
        queryset = super().get_queryset()
        
        # If user is viewing their own profile, show it regardless of verification
        if self.action == 'retrieve':
            return queryset
        
        # Otherwise, only show verified providers
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_verified=True)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's provider profile"""
        try:
            profile = request.user.provider_profile
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except ProviderProfile.DoesNotExist:
            return Response(
                {'detail': 'Provider profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        """Register as a provider"""
        if hasattr(request.user, 'provider_profile'):
            return Response(
                {'detail': 'You are already registered as a provider'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create provider profile
        profile = ProviderProfile.objects.create(
            user=request.user,
            phone_number=request.data.get('phone_number'),
            city=request.data.get('city', ''),
            country=request.data.get('country', 'Ethiopia'),
            latitude=request.data.get('latitude'),
            longitude=request.data.get('longitude')
        )
        
        return Response(
            ProviderProfileSerializer(profile).data,
            status=status.HTTP_201_CREATED
        )


class ProviderServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for provider services with geo-discovery.
    Only shows services from providers who are:
    1. National ID verified AND
    2. (Payment verified OR in active trial)
    
    Public read access (list, retrieve) - no authentication required
    Write access (create, update, delete) - authentication required
    """
    queryset = ProviderService.objects.select_related(
        'provider',
        'provider__provider_profile'
    ).filter(
        is_active=True,
        verification_status='approved'
    )
    permission_classes = [AllowAny]  # Allow public read access
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['name', 'description', 'service_category', 'city']
    filterset_fields = ['service_category', 'price_type', 'city']
    ordering_fields = ['created_at', 'views_count', 'provider__provider_profile__rating']
    ordering = ['-created_at']
    
    def get_permissions(self):
        """
        Allow public read access (list, retrieve, nearby, categories)
        Require authentication for write operations (create, update, delete)
        """
        if self.action in ['list', 'retrieve', 'nearby', 'categories']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'retrieve':
            return ProviderServiceDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProviderServiceCreateSerializer
        return ProviderServiceListSerializer
    
    def get_queryset(self):
        """
        Filter services with geo-discovery using Python-based Haversine.
        Applies trial logic: shows providers with National ID verified AND
        (payment verified OR active trial).
        """
        queryset = super().get_queryset()
        
        # Filter by trial/payment status
        visible_provider_ids = []
        for service in queryset:
            try:
                profile = service.provider.provider_profile
                if profile.is_visible_to_clients:
                    visible_provider_ids.append(service.provider.id)
            except Exception:
                pass
        
        queryset = queryset.filter(provider_id__in=visible_provider_ids)
        
        # Geo-discovery: Nearby search using Haversine formula
        lat = self.request.query_params.get('lat')
        lng = self.request.query_params.get('lng')
        radius = float(self.request.query_params.get('radius', 10))  # Default 10km
        
        if lat and lng:
            try:
                user_lat = float(lat)
                user_lng = float(lng)
                
                # Calculate distance for each service in Python
                services_with_distance = []
                for service in queryset:
                    if service.latitude and service.longitude:
                        distance = haversine_distance(
                            user_lat, user_lng,
                            float(service.latitude), float(service.longitude)
                        )
                        if distance <= radius:
                            service.distance = round(distance, 2)
                            services_with_distance.append(service)
                
                # Sort by distance
                services_with_distance.sort(key=lambda x: x.distance)
                
                # Return filtered queryset with distance annotation
                service_ids = [s.id for s in services_with_distance]
                queryset = queryset.filter(id__in=service_ids)
                
                # Preserve the distance attribute for serialization
                distance_map = {s.id: s.distance for s in services_with_distance}
                for service in queryset:
                    service.distance = distance_map.get(service.id)
                
            except (ValueError, TypeError):
                pass
        
        # Price range filter
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        
        if min_price:
            queryset = queryset.filter(
                Q(hourly_rate__gte=min_price) | Q(base_price__gte=min_price)
            )
        
        if max_price:
            queryset = queryset.filter(
                Q(hourly_rate__lte=max_price) | Q(base_price__lte=max_price)
            )
        
        # Rating filter
        min_rating = self.request.query_params.get('min_rating')
        if min_rating:
            queryset = queryset.filter(
                provider__provider_profile__rating__gte=float(min_rating)
            )
        
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """Increment view count on retrieve"""
        instance = self.get_object()
        instance.views_count += 1
        instance.save(update_fields=['views_count'])
        return super().retrieve(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """
        Get nearby services based on user location.
        Query params: lat, lng, radius (km)
        """
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        
        if not lat or not lng:
            return Response(
                {'detail': 'lat and lng parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Use the filtered queryset which already handles geo-discovery
        queryset = self.get_queryset()
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get list of service categories with counts"""
        categories = ProviderService.objects.filter(
            is_active=True,
            verification_status='approved',
            provider__provider_profile__is_verified=True
        ).values('service_category').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Map categories to icons (can be customized)
        category_icons = {
            'Plumber': '🔧',
            'Electrician': '💡',
            'Cleaner': '🧹',
            'Handyman': '🔨',
            'Visa Help': '✈️',
            'Essay Writing': '📝',
            'Translation': '🌐',
            'Tutoring': '🎓',
            'Consulting': '💼',
            'Design': '🎨',
            'Tech Support': '💻',
            'Legal Aid': '⚖️',
        }
        
        data = [
            {
                'category': cat['service_category'],
                'count': cat['count'],
                'icon': category_icons.get(cat['service_category'], '📋')
            }
            for cat in categories
        ]
        
        serializer = ServiceCategorySerializer(data, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_services(self, request):
        """Get current provider's services"""
        if not hasattr(request.user, 'provider_profile'):
            return Response(
                {'detail': 'You are not registered as a provider'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = ProviderService.objects.filter(
            provider=request.user
        ).order_by('-created_at')
        
        serializer = ProviderServiceDetailSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        """Create service for current user"""
        if not hasattr(self.request.user, 'provider_profile'):
            raise serializers.ValidationError('You must be a provider to create services')
        
        serializer.save(provider=self.request.user)


class ProviderVerificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for provider verifications.
    """
    queryset = ProviderVerification.objects.all()
    serializer_class = ProviderVerificationSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)  # Explicitly handle file uploads
    
    def get_queryset(self):
        """Filter to show only user's own verifications"""
        if self.request.user.is_staff:
            return super().get_queryset()
        return super().get_queryset().filter(user=self.request.user)
    
    def get_serializer_context(self):
        """Ensure request is in serializer context for file_url generation"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def create(self, request, *args, **kwargs):
        """Create verification with explicit file handling"""
        try:
            # Debug logging
            logger.info(f"📤 Verification upload request from user: {request.user.username}")
            logger.info(f"📤 FILES: {list(request.FILES.keys())}")
            logger.info(f"📤 DATA: {dict(request.data)}")
            
            # Validate file presence
            file = request.FILES.get('file')
            if not file:
                logger.error("❌ No file in request.FILES")
                return Response(
                    {'error': 'File is required', 'detail': 'No file was uploaded'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate verification type
            verification_type = request.data.get('verification_type')
            if not verification_type:
                logger.error("❌ No verification_type in request.data")
                return Response(
                    {'error': 'verification_type is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            logger.info(f"✅ File received: {file.name}, size: {file.size}, type: {verification_type}")
        except Exception as e:
            logger.error(f"❌ Error in create method: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        # Validate file size (10MB max)
        if file.size > 10 * 1024 * 1024:
            return Response(
                {'error': 'File too large', 'detail': 'Maximum file size is 10MB'},
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            )
        
        # Create verification with file
        verification = ProviderVerification.objects.create(
            user=request.user,
            verification_type=verification_type,
            file=file
        )
        
        # Serialize with request context for file_url
        serializer = self.get_serializer(verification)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def perform_create(self, serializer):
        """Create verification for current user (fallback method)"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """Get verification status for current user"""
        verifications = ProviderVerification.objects.filter(
            user=request.user
        ).order_by('-uploaded_at')
        
        id_verification = verifications.filter(verification_type='national_id').first()
        payment_verification = verifications.filter(verification_type='payment_proof').first()
        
        return Response({
            'national_id': {
                'status': id_verification.status if id_verification else 'not_uploaded',
                'uploaded_at': id_verification.uploaded_at if id_verification else None,
                'rejection_reason': id_verification.rejection_reason if id_verification else None,
            },
            'payment_proof': {
                'status': payment_verification.status if payment_verification else 'not_uploaded',
                'uploaded_at': payment_verification.uploaded_at if payment_verification else None,
                'rejection_reason': payment_verification.rejection_reason if payment_verification else None,
            },
            'is_fully_verified': (
                hasattr(request.user, 'provider_profile') and 
                request.user.provider_profile.is_verified
            )
        })


class CallLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for call logs (read-only for users).
    """
    queryset = CallLog.objects.all()
    serializer_class = CallLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter to show user's calls"""
        return super().get_queryset().filter(
            Q(caller=self.request.user) | Q(provider=self.request.user)
        ).order_by('-timestamp')


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for reviews.
    """
    queryset = Review.objects.select_related('client', 'provider', 'service').all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['provider', 'rating']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer"""
        if self.action == 'create':
            return ReviewCreateSerializer
        return ReviewSerializer
    
    def get_queryset(self):
        """Filter reviews"""
        queryset = super().get_queryset()
        
        # Filter by provider
        provider_id = self.request.query_params.get('provider_id')
        if provider_id:
            queryset = queryset.filter(provider_id=provider_id)
        
        # Filter by service
        service_id = self.request.query_params.get('service_id')
        if service_id:
            queryset = queryset.filter(service_id=service_id)
        
        return queryset


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def track_call(request):
    """
    Track a call to a provider (Immutable Business Rule: Call Tracking).
    Must be called before opening device dialer.
    """
    serializer = CallLogCreateSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    call_log = serializer.save()
    
    return Response(
        CallLogSerializer(call_log).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def auth_user_info(request):
    """
    Get authenticated user info with provider status.
    Returns is_provider and is_verified for dashboard routing.
    """
    serializer = AuthUserSerializer(request.user)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def service_categories_list(request):
    """
    Get list of all service categories (public endpoint).
    """
    categories = ProviderService.objects.filter(
        is_active=True,
        verification_status='approved',
        provider__provider_profile__is_verified=True
    ).values('service_category').annotate(
        count=Count('id')
    ).order_by('-count')
    
    category_icons = {
        'Plumber': '🔧',
        'Electrician': '💡',
        'Cleaner': '🧹',
        'Handyman': '🔨',
        'Visa Help': '✈️',
        'Essay Writing': '📝',
        'Translation': '🌐',
        'Tutoring': '🎓',
        'Consulting': '💼',
        'Design': '🎨',
        'Tech Support': '💻',
        'Legal Aid': '⚖️',
    }
    
    data = [
        {
            'category': cat['service_category'],
            'count': cat['count'],
            'icon': category_icons.get(cat['service_category'], '📋')
        }
        for cat in categories
    ]
    
    return Response(data)


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user and return JWT tokens.
    Creates user account and returns tokens for immediate login.
    """
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    
    # Validation
    if not username or not password:
        return Response(
            {'error': 'Username and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if User.objects.filter(username=username).exists():
        return Response(
            {'error': 'Username already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if email and User.objects.filter(email=email).exists():
        return Response(
            {'error': 'Email already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create user
    user = User.objects.create_user(
        username=username,
        email=email or '',
        password=password
    )
    
    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    
    # Return user data and tokens
    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
        },
        'tokens': {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    """
    Request password reset code via email.
    POST /api/auth/forgot-password/
    Body: { "email": "user@example.com" }
    """
    email = request.data.get('email', '').strip().lower()
    
    if not email:
        return Response(
            {'error': 'Email is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if user exists with this email
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Don't reveal if email exists (security best practice)
        return Response({
            'success': True,
            'message': 'If an account exists with this email, a reset code has been sent.'
        }, status=status.HTTP_200_OK)
    
    # Create reset code
    from .models import PasswordResetCode
    reset_code = PasswordResetCode.create_reset_code(user)
    
    # Send email with code
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        
        subject = "Password Reset Code - Mert Service"
        message = f"""Hello {user.first_name or user.username},

You requested to reset your password for Mert Service.

Your verification code is: {reset_code.code}

This code will expire in 10 minutes.

If you didn't request this, please ignore this email.

Best regards,
The Mert Service Team"""
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        
        logger.info(f"Password reset code sent to {email}")
        
    except Exception as e:
        logger.error(f"Failed to send reset email to {email}: {str(e)}")
        # Don't fail the request if email fails
    
    return Response({
        'success': True,
        'message': 'If an account exists with this email, a reset code has been sent.',
        'code': reset_code.code  # REMOVE IN PRODUCTION! Only for testing
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_reset_code(request):
    """
    Verify password reset code.
    POST /api/auth/verify-reset-code/
    Body: { "email": "user@example.com", "code": "123456" }
    """
    email = request.data.get('email', '').strip().lower()
    code = request.data.get('code', '').strip()
    
    if not email or not code:
        return Response(
            {'error': 'Email and code are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Find the reset code
    from .models import PasswordResetCode
    try:
        reset = PasswordResetCode.objects.filter(
            email=email,
            code=code,
            is_used=False
        ).latest('created_at')
    except PasswordResetCode.DoesNotExist:
        return Response(
            {'error': 'Invalid or expired code'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if expired
    if reset.is_expired():
        return Response(
            {'error': 'Code has expired. Please request a new one.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check attempts
    reset.attempts += 1
    if reset.attempts > 5:
        reset.is_used = True
        reset.save()
        return Response(
            {'error': 'Too many attempts. Please request a new code.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    reset.save()
    
    return Response({
        'success': True,
        'message': 'Code verified successfully',
        'email': email
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """
    Reset password with verified code.
    POST /api/auth/reset-password/
    Body: { "email": "user@example.com", "code": "123456", "new_password": "newpass123" }
    """
    email = request.data.get('email', '').strip().lower()
    code = request.data.get('code', '').strip()
    new_password = request.data.get('new_password', '').strip()
    
    if not email or not code or not new_password:
        return Response(
            {'error': 'Email, code, and new password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(new_password) < 6:
        return Response(
            {'error': 'Password must be at least 6 characters'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Find and verify the reset code
    from .models import PasswordResetCode
    try:
        reset = PasswordResetCode.objects.filter(
            email=email,
            code=code,
            is_used=False
        ).latest('created_at')
    except PasswordResetCode.DoesNotExist:
        return Response(
            {'error': 'Invalid or expired code'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if expired
    if reset.is_expired():
        return Response(
            {'error': 'Code has expired. Please request a new one.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Update user password
    user = reset.user
    user.set_password(new_password)
    user.save()
    
    # Mark code as used
    reset.is_used = True
    reset.save()
    
    logger.info(f"Password reset successful for {email}")
    
    return Response({
        'success': True,
        'message': 'Password reset successfully. You can now login with your new password.'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def otp_request(request):
    """
    Request OTP for phone number.
    Creates or updates OTP for the given phone number.
    """
    serializer = OTPRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    phone_number = serializer.validated_data['phone_number']
    name = serializer.validated_data.get('name', '')
    
    # Create new OTP
    otp = OTPVerification.create_otp(phone_number, name)
    
    # In production, send OTP via SMS
    # For development, return OTP in response (REMOVE IN PRODUCTION!)
    return Response({
        'message': 'OTP sent successfully',
        'phone_number': phone_number,
        'otp_code': otp.otp_code,  # REMOVE IN PRODUCTION!
        'expires_in': '10 minutes',
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def otp_verify(request):
    """
    Verify OTP and create/login user.
    Returns JWT tokens for authenticated session.
    """
    serializer = OTPVerifySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    phone_number = serializer.validated_data['phone_number']
    otp_code = serializer.validated_data['otp_code']
    name = serializer.validated_data.get('name', '')
    
    # Find latest OTP for this phone number
    try:
        otp = OTPVerification.objects.filter(
            phone_number=phone_number,
            otp_code=otp_code,
            is_verified=False
        ).latest('created_at')
    except OTPVerification.DoesNotExist:
        return Response(
            {'error': 'Invalid OTP code'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if expired
    if otp.is_expired():
        return Response(
            {'error': 'OTP has expired. Please request a new one.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check attempts
    otp.attempts += 1
    if otp.attempts > 5:
        return Response(
            {'error': 'Too many attempts. Please request a new OTP.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    otp.save()
    
    # Mark OTP as verified
    otp.is_verified = True
    otp.save()
    
    # Check if user exists with this phone number
    try:
        user_profile = UserProfile.objects.get(phone_number=phone_number)
        user = user_profile.user
        created = False
    except UserProfile.DoesNotExist:
        # Create new user
        username = f"user_{phone_number[-8:]}"  # Use last 8 digits
        
        # Ensure username is unique
        counter = 1
        base_username = username
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1
        
        # Create user
        user = User.objects.create_user(
            username=username,
            first_name=name or 'User',
        )
        
        # Create user profile
        user_profile = UserProfile.objects.create(
            user=user,
            phone_number=phone_number,
            is_phone_verified=True
        )
        created = True
    
    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'message': 'Phone verified successfully',
        'created': created,
        'user': {
            'id': user.id,
            'username': user.username,
            'name': user.first_name,
            'phone_number': phone_number,
        },
        'tokens': {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }
    }, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upgrade_to_provider(request):
    """
    Upgrade current user to provider status.
    Creates ProviderProfile for existing user.
    """
    import traceback
    
    try:
        # Debug logging
        logger.info(f"🔄 Upgrade to provider request from user: {request.user.username}")
        logger.info(f"📦 Request data: {dict(request.data)}")
        logger.info(f"👤 User has provider_profile: {hasattr(request.user, 'provider_profile')}")
        logger.info(f"👤 User has user_profile: {hasattr(request.user, 'user_profile')}")
        
        # Check if already a provider (use get_or_create pattern)
        if hasattr(request.user, 'provider_profile'):
            logger.info(f"✅ User already has provider_profile")
            return Response(
                {
                    'message': 'You are already a provider',
                    'profile': ProviderProfileSerializer(request.user.provider_profile).data
                },
                status=status.HTTP_200_OK
            )
        
        # Get required data
        city = request.data.get('city', 'Addis Ababa')
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        
        # Get phone number from multiple sources
        phone_number = None
        if hasattr(request.user, 'user_profile') and request.user.user_profile.phone_number:
            phone_number = request.user.user_profile.phone_number
            logger.info(f"📞 Using phone from user_profile: {phone_number}")
        elif request.data.get('phone_number'):
            phone_number = request.data.get('phone_number')
            logger.info(f"📞 Using phone from request: {phone_number}")
        else:
            # Fallback: use a placeholder if no phone available
            phone_number = '0000000000'
            logger.warning(f"⚠️ No phone number found, using placeholder: {phone_number}")
        
        logger.info(f"🏗️ Creating ProviderProfile with: city={city}, phone={phone_number}, lat={latitude}, lon={longitude}")
        
        # Create provider profile with get_or_create for safety
        provider_profile, created = ProviderProfile.objects.get_or_create(
            user=request.user,
            defaults={
                'phone_number': phone_number,
                'city': city,
                'latitude': latitude,
                'longitude': longitude,
            }
        )
        
        if not created:
            # Update existing profile
            logger.info(f"📝 Updating existing provider_profile")
            provider_profile.city = city
            if latitude:
                provider_profile.latitude = latitude
            if longitude:
                provider_profile.longitude = longitude
            provider_profile.save()
        
        logger.info(f"✅ Provider profile {'created' if created else 'updated'} successfully")
        
        return Response({
            'message': f"Successfully {'upgraded to' if created else 'updated'} provider",
            'profile': ProviderProfileSerializer(provider_profile).data
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"❌ UPGRADE TO PROVIDER ERROR: {str(e)}")
        logger.error(traceback.format_exc())
        return Response(
            {
                'error': str(e),
                'detail': 'Failed to create provider profile. Please contact support.'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_kyc_images(request):
    """
    Upload selfie and/or ID image for KYC verification.
    POST /api/providers/kyc/upload/
    Multipart form: selfie (file), id_image (file)
    """
    if not hasattr(request.user, 'provider_profile'):
        return Response(
            {'error': 'Provider profile not found'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    profile = request.user.provider_profile
    updated = []
    
    selfie = request.FILES.get('selfie')
    id_image = request.FILES.get('id_image')
    
    if not selfie and not id_image:
        return Response(
            {'error': 'At least one file (selfie or id_image) is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if selfie:
        if selfie.size > 10 * 1024 * 1024:
            return Response({'error': 'Selfie too large (max 10MB)'}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        profile.selfie_image = selfie
        updated.append('selfie')
    
    if id_image:
        if id_image.size > 10 * 1024 * 1024:
            return Response({'error': 'ID image too large (max 10MB)'}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        profile.id_image = id_image
        updated.append('id_image')
    
    profile.save(update_fields=updated if updated else ['selfie_image', 'id_image'])
    
    serializer = ProviderProfileSerializer(profile, context={'request': request})
    return Response({
        'success': True,
        'updated': updated,
        'profile': serializer.data,
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_status(request):
    """
    Get current user's status (reviewer, provider, or both).
    """
    user = request.user
    
    is_reviewer = hasattr(user, 'user_profile')
    is_provider = hasattr(user, 'provider_profile')
    
    data = {
        'user': {
            'id': user.id,
            'username': user.username,
            'name': user.get_full_name() or user.first_name or user.username,
            'is_staff': user.is_staff,  # Add is_staff field
        },
        'is_reviewer': is_reviewer,
        'is_provider': is_provider,
        'can_upgrade': is_reviewer and not is_provider,
    }
    
    if is_reviewer:
        data['reviewer_profile'] = UserProfileSerializer(user.user_profile).data
    
    if is_provider:
        data['provider_profile'] = ProviderProfileSerializer(user.provider_profile).data
    
    return Response(data)


# ============================================
# ADMIN ENDPOINTS
# ============================================

@api_view(['GET'])
@permission_classes([AllowAny])
def test_endpoint(request):
    """Test endpoint to verify deployment"""
    return Response({
        'status': 'ok',
        'message': 'Backend is running',
        'timestamp': timezone.now().isoformat(),
        'version': 'bulletproof-v2'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_pending_verifications(request):
    """
    Get all provider verification documents pending review (admin only).
    Returns ProviderVerification records with status='pending'.
    
    PRODUCTION-SAFE: Handles missing files, missing profiles, and null relations.
    """
    if not request.user.is_staff:
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        # SAFE QUERY: Filter out records with missing critical relations
        pending_verifications = ProviderVerification.objects.filter(
            status='pending',
            user__isnull=False  # Must have a user
        ).select_related('user').order_by('-uploaded_at')
        
        total_found = pending_verifications.count()
        logger.info(f"📋 Found {total_found} pending verifications")
        
        data = []
        skipped = 0
        
        for verification in pending_verifications:
            try:
                # SAFE: Check user exists
                if not verification.user:
                    logger.warning(f"⚠️ Skipping verification {verification.id} - No user")
                    skipped += 1
                    continue
                
                user = verification.user
                
                # SAFE: Get provider profile (may not exist)
                provider_profile = None
                try:
                    provider_profile = user.provider_profile
                except Exception:
                    logger.warning(f"⚠️ No provider profile for user {user.username} (verification {verification.id})")
                
                # SAFE: Get file URL (may not exist)
                file_url = None
                if verification.file:
                    try:
                        file_url = request.build_absolute_uri(verification.file.url)
                    except Exception as e:
                        logger.warning(f"⚠️ Cannot build file URL for verification {verification.id}: {str(e)}")
                
                # SAFE: Build response with all null checks
                data.append({
                    'id': verification.id,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'name': user.get_full_name() or user.first_name or user.username or 'Unknown',
                    },
                    'verification_type': verification.verification_type,
                    'verification_type_display': verification.get_verification_type_display(),
                    'file_url': file_url,
                    'status': verification.status,
                    'uploaded_at': verification.uploaded_at,
                    'expiry_date': verification.expiry_date,
                    # Provider profile info (may be null)
                    'provider_profile': {
                        'id': provider_profile.id if provider_profile else None,
                        'phone_number': provider_profile.phone_number if provider_profile else None,
                        'city': provider_profile.city if provider_profile else 'Unknown',
                        'is_verified': provider_profile.is_verified if provider_profile else False,
                        'national_id_verified': provider_profile.national_id_verified if provider_profile else False,
                        'payment_verified': provider_profile.payment_verified if provider_profile else False,
                    } if provider_profile else None,
                })
                
            except Exception as e:
                logger.error(f"❌ Error processing verification {verification.id}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                skipped += 1
                continue
        
        logger.info(f"✅ Returning {len(data)} pending verifications ({skipped} skipped)")
        
        # ALWAYS return 200 with data (even if empty)
        return Response({
            'count': len(data),
            'results': data,
            'total_found': total_found,
            'skipped': skipped
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        # CRITICAL ERROR: Log and return safe error response
        logger.error(f"❌ CRITICAL ERROR in admin_pending_verifications: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Return JSON error (not HTML)
        return Response({
            'error': 'Internal server error',
            'detail': str(e),
            'count': 0,
            'results': []
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_verify_document(request, verification_id):
    """
    Approve or reject a verification document (admin only).
    POST /api/providers/admin/verify-document/<verification_id>/
    Body: { "action": "approve" | "reject", "reason": "..." }
    """
    if not request.user.is_staff:
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    action_type = request.data.get('action')  # 'approve' or 'reject'
    reason = request.data.get('reason', '')
    
    if action_type not in ['approve', 'reject']:
        return Response(
            {'error': 'Invalid action. Must be "approve" or "reject"'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        verification = ProviderVerification.objects.get(id=verification_id)
    except ProviderVerification.DoesNotExist:
        return Response(
            {'error': 'Verification document not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if action_type == 'approve':
        verification.approve(request.user)
        
        return Response({
            'success': True,
            'message': f'{verification.get_verification_type_display()} approved for {verification.user.username}',
            'verification': ProviderVerificationSerializer(verification, context={'request': request}).data
        })
    
    else:  # reject
        if not reason or len(reason.strip()) < 10:
            return Response(
                {'error': 'Rejection reason must be at least 10 characters'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        verification.reject(request.user, reason)
        verification.save()
        
        return Response({
            'success': True,
            'message': f'{verification.get_verification_type_display()} rejected for {verification.user.username}',
            'verification': ProviderVerificationSerializer(verification, context={'request': request}).data
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_verify_provider(request, provider_id):
    """
    Approve or reject a provider (admin only).
    """
    if not request.user.is_staff:
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    action_type = request.data.get('action')  # 'approve' or 'reject'
    
    if action_type not in ['approve', 'reject']:
        return Response(
            {'error': 'Invalid action. Must be "approve" or "reject"'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        provider = ProviderProfile.objects.get(id=provider_id)
    except ProviderProfile.DoesNotExist:
        return Response(
            {'error': 'Provider not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if action_type == 'approve':
        provider.is_verified = True
        provider.save()
        
        return Response({
            'success': True,
            'message': f'Provider {provider.user.username} has been verified',
            'provider': ProviderProfileSerializer(provider).data
        })
    
    else:  # reject
        # Mark verifications as rejected
        provider.verifications.all().update(is_verified=False)
        
        return Response({
            'success': True,
            'message': f'Provider {provider.user.username} has been rejected',
            'provider': ProviderProfileSerializer(provider).data
        })


# ============================================
# ADMIN CONTROL CENTER - Provider Management
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_suspend_provider(request, provider_id):
    """
    Suspend or reactivate a provider account (admin only).
    POST /api/providers/admin/providers/<id>/suspend/
    Body: { "suspend": true/false, "reason": "..." }
    """
    if not request.user.is_staff:
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        profile = ProviderProfile.objects.get(id=provider_id)
    except ProviderProfile.DoesNotExist:
        return Response(
            {'error': 'Provider not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    suspend = request.data.get('suspend', True)
    reason = request.data.get('reason', '')
    
    if suspend:
        # Suspend provider
        profile.is_active = False
        profile.suspended_at = timezone.now()
        profile.suspension_reason = reason
        profile.save()
        
        # Also deactivate all their services
        ProviderService.objects.filter(provider=profile.user).update(
            is_active=False,
            hidden_at=timezone.now(),
            hidden_reason=f"Provider suspended: {reason}"
        )
        
        message = f"Provider {profile.user.username} suspended successfully"
    else:
        # Reactivate provider
        profile.is_active = True
        profile.suspended_at = None
        profile.suspension_reason = ''
        profile.save()
        
        # Reactivate their services
        ProviderService.objects.filter(provider=profile.user).update(
            is_active=True,
            hidden_at=None,
            hidden_reason=''
        )
        
        message = f"Provider {profile.user.username} reactivated successfully"
    
    return Response({
        'success': True,
        'message': message,
        'provider': ProviderProfileSerializer(profile).data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_hide_service(request, service_id):
    """
    Hide or unhide a service (soft delete) (admin only).
    POST /api/providers/admin/services/<id>/hide/
    Body: { "hide": true/false, "reason": "..." }
    """
    if not request.user.is_staff:
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        service = ProviderService.objects.get(id=service_id)
    except ProviderService.DoesNotExist:
        return Response(
            {'error': 'Service not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    hide = request.data.get('hide', True)
    reason = request.data.get('reason', '')
    
    if hide:
        # Hide service
        service.is_active = False
        service.hidden_at = timezone.now()
        service.hidden_reason = reason
        service.save()
        message = f"Service '{service.name}' hidden successfully"
    else:
        # Unhide service
        service.is_active = True
        service.hidden_at = None
        service.hidden_reason = ''
        service.save()
        message = f"Service '{service.name}' restored successfully"
    
    return Response({
        'success': True,
        'message': message,
        'service': ProviderServiceDetailSerializer(service, context={'request': request}).data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_approve_verification(request, verification_id):
    """
    Approve or reject a verification document (admin only).
    POST /api/providers/admin/verifications/<id>/approve/
    Body: { "approve": true/false, "reason": "..." }
    """
    if not request.user.is_staff:
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        verification = ProviderVerification.objects.get(id=verification_id)
    except ProviderVerification.DoesNotExist:
        return Response(
            {'error': 'Verification not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    approve = request.data.get('approve', True)
    reason = request.data.get('reason', '')
    
    if approve:
        # Approve verification
        verification.status = 'approved'
        verification.reviewed_by = request.user
        verification.reviewed_at = timezone.now()
        verification.rejection_reason = ''
        verification.save()
        
        # The signal will auto-update the provider profile
        message = f"{verification.get_verification_type_display()} approved for {verification.user.username}"
    else:
        # Reject verification
        verification.status = 'rejected'
        verification.reviewed_by = request.user
        verification.reviewed_at = timezone.now()
        verification.rejection_reason = reason
        verification.save()
        
        message = f"{verification.get_verification_type_display()} rejected for {verification.user.username}"
    
    return Response({
        'success': True,
        'message': message,
        'verification': ProviderVerificationSerializer(verification, context={'request': request}).data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_provider_list(request):
    """
    Get list of all providers with filtering (admin only).
    GET /api/providers/admin/providers/
    Query params: status (all/active/suspended/verified/pending), search, category
    """
    if not request.user.is_staff:
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Start with all providers
    providers = ProviderProfile.objects.select_related('user').all()
    
    # Filter by status
    status_filter = request.query_params.get('status', 'all')
    if status_filter == 'active':
        providers = providers.filter(is_active=True)
    elif status_filter == 'suspended':
        providers = providers.filter(is_active=False)
    elif status_filter == 'verified':
        providers = providers.filter(is_verified=True)
    elif status_filter == 'pending':
        providers = providers.filter(is_verified=False)
    
    # Search by username or phone
    search = request.query_params.get('search', '')
    if search:
        from django.db.models import Q
        providers = providers.filter(
            Q(user__username__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(phone_number__icontains=search)
        )
    
    # Serialize
    data = []
    for provider in providers:
        services_count = ProviderService.objects.filter(provider=provider.user).count()
        active_services = ProviderService.objects.filter(provider=provider.user, is_active=True).count()
        
        data.append({
            'id': provider.id,
            'user': {
                'id': provider.user.id,
                'username': provider.user.username,
                'name': provider.user.get_full_name() or provider.user.username,
            },
            'phone_number': provider.phone_number,
            'city': provider.city,
            'is_verified': provider.is_verified,
            'is_active': provider.is_active,
            'suspended_at': provider.suspended_at,
            'suspension_reason': provider.suspension_reason,
            'services_count': services_count,
            'active_services': active_services,
            'rating': provider.rating,
            'total_reviews': provider.total_reviews,
            'created_at': provider.created_at,
            'trial_expiry_date': provider.trial_expiry_date,
            'days_until_trial_expiry': provider.days_until_trial_expiry,
        })
    
    return Response({
        'count': len(data),
        'results': data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_service_list(request):
    """
    Get list of all services with filtering (admin only).
    GET /api/providers/admin/services/
    Query params: status (all/active/hidden), search, category
    """
    if not request.user.is_staff:
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Start with all services
    services = ProviderService.objects.select_related('provider__provider_profile').all()
    
    # Filter by status
    status_filter = request.query_params.get('status', 'all')
    if status_filter == 'active':
        services = services.filter(is_active=True)
    elif status_filter == 'hidden':
        services = services.filter(is_active=False)
    
    # Filter by category
    category = request.query_params.get('category', '')
    if category:
        services = services.filter(service_category__icontains=category)
    
    # Search by name or provider
    search = request.query_params.get('search', '')
    if search:
        from django.db.models import Q
        services = services.filter(
            Q(name__icontains=search) |
            Q(provider__username__icontains=search) |
            Q(service_category__icontains=search)
        )
    
    # Serialize
    data = []
    for service in services:
        data.append({
            'id': service.id,
            'name': service.name,
            'service_category': service.service_category,
            'provider': {
                'id': service.provider.id,
                'username': service.provider.username,
                'name': service.provider.get_full_name() or service.provider.username,
            },
            'is_active': service.is_active,
            'hidden_at': service.hidden_at,
            'hidden_reason': service.hidden_reason,
            'verification_status': service.verification_status,
            'views_count': service.views_count,
            'created_at': service.created_at,
            'city': service.city,
        })
    
    return Response({
        'count': len(data),
        'results': data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_stats(request):
    """
    Get admin dashboard statistics.
    GET /api/providers/admin/stats/
    """
    try:
        logger.info(f"📊 Admin stats requested by user: {request.user.username} (is_staff: {request.user.is_staff})")
        
        if not request.user.is_staff:
            logger.warning(f"⚠️ Non-admin user {request.user.username} attempted to access admin stats")
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from django.db.models import Count, Q, Avg
        from datetime import timedelta
        
        # User statistics
        try:
            total_users = User.objects.count()
            active_users = User.objects.filter(is_active=True).count()
            logger.info(f"✅ User stats: total={total_users}, active={active_users}")
        except Exception as e:
            logger.error(f"❌ Error getting user stats: {e}")
            total_users = 0
            active_users = 0
        
        # Provider statistics
        try:
            total_providers = ProviderProfile.objects.count()
            verified_providers = ProviderProfile.objects.filter(is_verified=True).count()
            pending_providers = ProviderProfile.objects.filter(is_verified=False).count()
            logger.info(f"✅ Provider stats: total={total_providers}, verified={verified_providers}, pending={pending_providers}")
        except Exception as e:
            logger.error(f"❌ Error getting provider stats: {e}")
            total_providers = 0
            verified_providers = 0
            pending_providers = 0
        
        # Service statistics
        try:
            total_services = ProviderService.objects.count()
            active_services = ProviderService.objects.filter(is_active=True).count()
            hidden_services = ProviderService.objects.filter(is_active=False).count()
            logger.info(f"✅ Service stats: total={total_services}, active={active_services}, hidden={hidden_services}")
        except Exception as e:
            logger.error(f"❌ Error getting service stats: {e}")
            total_services = 0
            active_services = 0
            hidden_services = 0
        
        # Verification statistics
        try:
            pending_verifications = ProviderVerification.objects.filter(status='pending').count()
            approved_verifications = ProviderVerification.objects.filter(status='approved').count()
            rejected_verifications = ProviderVerification.objects.filter(status='rejected').count()
            logger.info(f"✅ Verification stats: pending={pending_verifications}, approved={approved_verifications}, rejected={rejected_verifications}")
        except Exception as e:
            logger.error(f"❌ Error getting verification stats: {e}")
            pending_verifications = 0
            approved_verifications = 0
            rejected_verifications = 0
        
        # Review statistics
        try:
            total_reviews = Review.objects.count()
            average_rating = Review.objects.aggregate(Avg('rating'))['rating__avg'] or 0
            logger.info(f"✅ Review stats: total={total_reviews}, avg_rating={average_rating}")
        except Exception as e:
            logger.error(f"❌ Error getting review stats: {e}")
            total_reviews = 0
            average_rating = 0
        
        # Call log statistics
        try:
            total_calls = CallLog.objects.count()
            logger.info(f"✅ Call stats: total={total_calls}")
        except Exception as e:
            logger.error(f"❌ Error getting call stats: {e}")
            total_calls = 0
        
        # Recent activity (last 7 days)
        try:
            seven_days_ago = timezone.now() - timedelta(days=7)
            
            recent_users = User.objects.filter(date_joined__gte=seven_days_ago).count()
            recent_providers = ProviderProfile.objects.filter(created_at__gte=seven_days_ago).count()
            recent_services = ProviderService.objects.filter(created_at__gte=seven_days_ago).count()
            recent_reviews = Review.objects.filter(created_at__gte=seven_days_ago).count()
            logger.info(f"✅ Recent activity: users={recent_users}, providers={recent_providers}, services={recent_services}, reviews={recent_reviews}")
        except Exception as e:
            logger.error(f"❌ Error getting recent activity: {e}")
            recent_users = 0
            recent_providers = 0
            recent_services = 0
            recent_reviews = 0
        
        stats_data = {
            'users': {
                'total': total_users,
                'active': active_users,
                'recent_7_days': recent_users,
            },
            'providers': {
                'total': total_providers,
                'verified': verified_providers,
                'pending': pending_providers,
                'recent_7_days': recent_providers,
            },
            'services': {
                'total': total_services,
                'active': active_services,
                'hidden': hidden_services,
                'recent_7_days': recent_services,
            },
            'verifications': {
                'pending': pending_verifications,
                'approved': approved_verifications,
                'rejected': rejected_verifications,
            },
            'reviews': {
                'total': total_reviews,
                'average_rating': round(average_rating, 2),
                'recent_7_days': recent_reviews,
            },
            'calls': {
                'total': total_calls,
            },
        }
        
        logger.info(f"✅ Admin stats generated successfully for {request.user.username}")
        return Response(stats_data)
        
    except Exception as e:
        logger.error(f"❌ Critical error generating admin stats: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response(
            {'error': 'Failed to generate statistics', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================
# BROADCAST NOTIFICATION SYSTEM
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_push_token(request):
    """
    Register or update push notification token for current user.
    POST /api/providers/push-token/register/
    Body: { "token": "ExponentPushToken[...]", "device_type": "android" }
    """
    from .models import PushToken
    
    token = request.data.get('token')
    device_type = request.data.get('device_type', 'android')
    
    if not token:
        return Response(
            {'error': 'Token is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create or update token — use only `token` as lookup key since it's unique
    push_token, created = PushToken.objects.update_or_create(
        token=token,
        defaults={
            'user': request.user,
            'device_type': device_type,
            'is_active': True
        }
    )
    
    return Response({
        'success': True,
        'message': 'Push token registered successfully',
        'token': {
            'id': push_token.id,
            'token': push_token.token,
            'device_type': push_token.device_type,
            'created': created
        }
    }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_send_broadcast(request):
    """
    Send broadcast notification to filtered providers (admin only).
    POST /api/providers/admin/broadcast/send/
    Body: {
        "title": "Important Update",
        "message": "Your message here",
        "target_audience": "all|verified|pending|trial|active|suspended",
        "category_filter": "Plumber" (optional),
        "city_filter": "Addis Ababa" (optional)
    }
    """
    from .models import BroadcastNotification, PushToken
    
    if not request.user.is_staff:
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Validate input
    title = request.data.get('title')
    message = request.data.get('message')
    target_audience = request.data.get('target_audience', 'all')
    
    if not title or not message:
        return Response(
            {'error': 'Title and message are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create broadcast record
    broadcast = BroadcastNotification.objects.create(
        created_by=request.user,
        title=title,
        message=message,
        target_audience=target_audience,
        category_filter=request.data.get('category_filter', ''),
        city_filter=request.data.get('city_filter', ''),
        status='sending'
    )
    
    # Get target providers
    target_providers = broadcast.get_target_providers()
    provider_user_ids = target_providers.values_list('user_id', flat=True)
    
    # Get push tokens for target providers
    push_tokens = PushToken.objects.filter(
        user_id__in=provider_user_ids,
        is_active=True
    )
    
    # Send push notifications using Expo
    success_count = 0
    failure_count = 0
    
    try:
        from exponent_server_sdk import (
            DeviceNotRegisteredError,
            PushClient,
            PushMessage,
            PushServerError,
            PushTicketError,
        )
        
        # Initialize Expo push client
        push_client = PushClient()
        
        # Prepare messages
        messages = []
        for token in push_tokens:
            try:
                messages.append(PushMessage(
                    to=token.token,
                    title=title,
                    body=message,
                    data={'type': 'broadcast', 'broadcast_id': broadcast.id},
                    sound='default',
                    priority='high'
                ))
            except Exception as e:
                print(f"Error preparing message for token {token.id}: {e}")
                failure_count += 1
        
        # Send messages in chunks
        chunk_size = 100
        for i in range(0, len(messages), chunk_size):
            chunk = messages[i:i + chunk_size]
            try:
                tickets = push_client.publish_multiple(chunk)
                
                # Check tickets for errors
                for ticket in tickets:
                    if ticket.is_success():
                        success_count += 1
                    else:
                        failure_count += 1
                        print(f"Push ticket error: {ticket.message}")
            
            except PushServerError as e:
                print(f"Push server error: {e}")
                failure_count += len(chunk)
            except Exception as e:
                print(f"Unexpected error sending push: {e}")
                failure_count += len(chunk)
    
    except ImportError:
        # Expo SDK not installed - log warning
        print("⚠️ exponent_server_sdk not installed. Install with: pip install exponent_server_sdk")
        print(f"📢 Would send to {push_tokens.count()} devices: {title}")
        success_count = push_tokens.count()  # Simulate success for development
    
    # Update broadcast record
    broadcast.sent_count = len(push_tokens)
    broadcast.success_count = success_count
    broadcast.failure_count = failure_count
    broadcast.status = 'sent' if failure_count == 0 else 'failed'
    broadcast.sent_at = timezone.now()
    broadcast.save()
    
    # ── Email broadcast (optional) ──────────────────────────────────────────
    include_email = request.data.get('include_email', False)
    email_success = 0
    email_failure = 0

    if include_email:
        from django.core.mail import send_mail
        from django.conf import settings

        # Collect emails of target provider users
        provider_users = User.objects.filter(id__in=provider_user_ids).exclude(email='')
        for u in provider_users:
            try:
                send_mail(
                    subject=title,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[u.email],
                    fail_silently=True,
                )
                email_success += 1
            except Exception as e:
                print(f"Email failed for {u.email}: {e}")
                email_failure += 1

    return Response({
        'success': True,
        'message': 'Broadcast sent successfully',
        'broadcast': {
            'id': broadcast.id,
            'title': broadcast.title,
            'target_audience': broadcast.get_target_audience_display(),
            'sent_count': broadcast.sent_count,
            'success_count': broadcast.success_count,
            'failure_count': broadcast.failure_count,
            'status': broadcast.status,
            'sent_at': broadcast.sent_at,
            'email_success': email_success,
            'email_failure': email_failure,
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_broadcast_list(request):
    """
    Get list of all broadcast notifications (admin only).
    GET /api/providers/admin/broadcast/list/
    """
    from .models import BroadcastNotification
    
    if not request.user.is_staff:
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    broadcasts = BroadcastNotification.objects.select_related('created_by').all()
    
    data = []
    for broadcast in broadcasts:
        data.append({
            'id': broadcast.id,
            'title': broadcast.title,
            'message': broadcast.message,
            'target_audience': broadcast.get_target_audience_display(),
            'category_filter': broadcast.category_filter,
            'city_filter': broadcast.city_filter,
            'sent_count': broadcast.sent_count,
            'success_count': broadcast.success_count,
            'failure_count': broadcast.failure_count,
            'status': broadcast.status,
            'created_by': broadcast.created_by.username,
            'created_at': broadcast.created_at,
            'sent_at': broadcast.sent_at,
        })
    
    return Response({
        'count': len(data),
        'results': data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_broadcast_preview(request):
    """
    Preview how many providers will receive a broadcast (admin only).
    GET /api/providers/admin/broadcast/preview/
    Query params: target_audience, category_filter, city_filter
    """
    from .models import BroadcastNotification, PushToken
    
    if not request.user.is_staff:
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Create temporary broadcast to use filtering logic
    temp_broadcast = BroadcastNotification(
        target_audience=request.query_params.get('target_audience', 'all'),
        category_filter=request.query_params.get('category_filter', ''),
        city_filter=request.query_params.get('city_filter', '')
    )
    
    # Get target providers
    target_providers = temp_broadcast.get_target_providers()
    provider_count = target_providers.count()
    
    # Get push token count
    provider_user_ids = target_providers.values_list('user_id', flat=True)
    token_count = PushToken.objects.filter(
        user_id__in=provider_user_ids,
        is_active=True
    ).count()
    
    return Response({
        'target_providers': provider_count,
        'devices_with_tokens': token_count,
        'filters': {
            'target_audience': temp_broadcast.get_target_audience_display(),
            'category_filter': temp_broadcast.category_filter or 'None',
            'city_filter': temp_broadcast.city_filter or 'None',
        }
    })


# ============================================
# TAXONOMY ENDPOINTS
# ============================================

@api_view(['GET'])
@permission_classes([AllowAny])
def taxonomy_list(request):
    """
    GET /api/providers/taxonomy/
    Returns all 8 master categories with their sub-categories.
    """
    try:
        categories = ServiceCategory.objects.prefetch_related('subcategories').all()
        data = []
        for cat in categories:
            data.append({
                'id': cat.id,
                'name': cat.name,
                'slug': cat.slug,
                'icon': cat.icon,
                'subcategories': [
                    {
                        'id': sub.id,
                        'name': sub.name,
                        'slug': sub.slug,
                        'icon': sub.icon,
                    }
                    for sub in cat.subcategories.all()
                ]
            })
        return Response(data)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_send_email(request):
    """
    Send a custom email to one or all provider users (admin only).
    POST /api/providers/admin/email/send/
    Body: {
        "subject": "...",
        "body": "...",
        "recipient": "specific@email.com" | null  (null = all providers with emails)
        "target_audience": "all|verified|pending"
    }
    """
    from django.core.mail import send_mail
    from django.conf import settings

    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)

    subject = request.data.get('subject', '').strip()
    body = request.data.get('body', '').strip()
    recipient = request.data.get('recipient', '').strip()
    target_audience = request.data.get('target_audience', 'all')

    if not subject or not body:
        return Response({'error': 'Subject and body are required'}, status=status.HTTP_400_BAD_REQUEST)

    # Build recipient list
    if recipient:
        recipients = [recipient]
    else:
        # All provider users with emails based on audience filter
        qs = ProviderProfile.objects.select_related('user').exclude(user__email='')
        if target_audience == 'verified':
            qs = qs.filter(is_verified=True)
        elif target_audience == 'pending':
            qs = qs.filter(is_verified=False)
        recipients = list(qs.values_list('user__email', flat=True).distinct())

    if not recipients:
        return Response({'error': 'No recipients found'}, status=status.HTTP_400_BAD_REQUEST)

    success, failure = 0, 0
    for email in recipients:
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            success += 1
        except Exception as e:
            print(f'Email failed for {email}: {e}')
            failure += 1

    return Response({
        'success': True,
        'sent': success,
        'failed': failure,
        'total': len(recipients),
    })
