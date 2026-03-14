from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProviderProfileViewSet,
    ProviderServiceViewSet,
    ProviderVerificationViewSet,
    CallLogViewSet,
    ReviewViewSet,
    track_call,
    auth_user_info,
    service_categories_list,
    register,
    otp_request,
    otp_verify,
    upgrade_to_provider,
    user_status,
    upload_kyc_images,
    admin_pending_verifications,
    admin_verify_provider,
    admin_suspend_provider,
    admin_hide_service,
    admin_approve_verification,
    admin_provider_list,
    admin_service_list,
    register_push_token,
    admin_send_broadcast,
    admin_broadcast_list,
    admin_broadcast_preview,
)

router = DefaultRouter()
router.register(r'profiles', ProviderProfileViewSet, basename='provider-profile')
router.register(r'services', ProviderServiceViewSet, basename='provider-service')
router.register(r'verifications', ProviderVerificationViewSet, basename='provider-verification')
router.register(r'call-logs', CallLogViewSet, basename='call-log')
router.register(r'reviews', ReviewViewSet, basename='review')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Custom endpoints
    path('track-call/', track_call, name='track-call'),
    path('auth/user/', auth_user_info, name='auth-user-info'),
    path('categories/', service_categories_list, name='service-categories'),
    path('register/', register, name='register'),
    
    # OTP endpoints
    path('auth/otp-request/', otp_request, name='otp-request'),
    path('auth/otp-verify/', otp_verify, name='otp-verify'),
    
    # Upgrade endpoint
    path('upgrade-to-provider/', upgrade_to_provider, name='upgrade-to-provider'),
    path('user-status/', user_status, name='user-status'),
    path('kyc/upload/', upload_kyc_images, name='kyc-upload'),
    
    # Admin endpoints
    path('admin/pending-verifications/', admin_pending_verifications, name='admin-pending-verifications'),
    path('admin/verify-provider/<int:provider_id>/', admin_verify_provider, name='admin-verify-provider'),
    
    # Admin Control Center
    path('admin/providers/', admin_provider_list, name='admin-provider-list'),
    path('admin/providers/<int:provider_id>/suspend/', admin_suspend_provider, name='admin-suspend-provider'),
    path('admin/services/', admin_service_list, name='admin-service-list'),
    path('admin/services/<int:service_id>/hide/', admin_hide_service, name='admin-hide-service'),
    path('admin/verifications/<int:verification_id>/approve/', admin_approve_verification, name='admin-approve-verification'),
    
    # Broadcast Notification System
    path('push-token/register/', register_push_token, name='register-push-token'),
    path('admin/broadcast/send/', admin_send_broadcast, name='admin-send-broadcast'),
    path('admin/broadcast/list/', admin_broadcast_list, name='admin-broadcast-list'),
    path('admin/broadcast/preview/', admin_broadcast_preview, name='admin-broadcast-preview'),
]
