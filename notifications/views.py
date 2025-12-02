from django.utils import timezone
from django.db.models import Exists, OuterRef, Q, BooleanField, ExpressionWrapper
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import api_view, permission_classes
from datetime import timedelta

from .models import Notification, NotificationRead
from .serializers import NotificationSerializer


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # status param: active (default), unread, all
        status_filter = request.query_params.get('status', 'active')
        now = timezone.now()
        base_qs = Notification.objects.filter(is_active=True).exclude(
            Q(expires_at__isnull=False) & Q(expires_at__lt=now)
        )
        # audience scoping: ALL or CUSTOM recipients includes user
        qs = base_qs.filter(
            Q(audience=Notification.AUDIENCE_ALL) |
            Q(audience=Notification.AUDIENCE_CUSTOM, recipients=request.user)
        ).distinct()

        # annotate read status
        read_subq = NotificationRead.objects.filter(
            notification=OuterRef('pk'), user=request.user
        )
        qs = qs.annotate(
            is_read=ExpressionWrapper(
                Exists(read_subq), output_field=BooleanField()
            )
        )

        if status_filter == 'unread':
            qs = qs.filter(is_read=False)
        elif status_filter == 'all':
            pass  # no extra filter
        else:
            # active is default (already filtered by is_active and expiry)
            pass

        serializer = NotificationSerializer(qs[:50], many=True)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_read(request):
    # mark as read the notifications visible to this user
    now = timezone.now()
    visible = Notification.objects.filter(is_active=True).exclude(
        Q(expires_at__isnull=False) & Q(expires_at__lt=now)
    ).filter(
        Q(audience=Notification.AUDIENCE_ALL) |
        Q(audience=Notification.AUDIENCE_CUSTOM, recipients=request.user)
    )
    # bulk create read rows ignoring duplicates
    to_create = []
    existing = set(
        NotificationRead.objects.filter(user=request.user, notification__in=visible)
        .values_list('notification_id', flat=True)
    )
    for nid in visible.values_list('id', flat=True):
        if nid not in existing:
            to_create.append(NotificationRead(user=request.user, notification_id=nid))
    if to_create:
        NotificationRead.objects.bulk_create(to_create, ignore_conflicts=True)
    return Response({'status': 'ok'})


class AdminNotificationCreateView(APIView):
    """
    POST /api/notifications/admin/create/
    
    Create a notification for selected users or all users.
    
    Request body:
    - title: Notification title
    - message: Notification message
    - user_ids: List of user IDs (optional if send_to_all is true)
    - send_to_all: Boolean to send to all users
    - expires_in_days: Number of days until notification expires (optional)
    """
    permission_classes = [IsAdminUser]

    def post(self, request):
        title = request.data.get('title', '')
        message = request.data.get('message', '')
        user_ids = request.data.get('user_ids', [])
        send_to_all = request.data.get('send_to_all', False)
        expires_in_days = request.data.get('expires_in_days')
        
        if not title or not message:
            return Response(
                {'error': 'Title and message are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not send_to_all and not user_ids:
            return Response(
                {'error': 'Either send_to_all must be true or user_ids must be provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate expiry
        expires_at = None
        if expires_in_days:
            try:
                expires_at = timezone.now() + timedelta(days=int(expires_in_days))
            except (ValueError, TypeError):
                pass
        
        # Create notification
        notification = Notification.objects.create(
            title=title,
            message=message,
            audience=Notification.AUDIENCE_ALL if send_to_all else Notification.AUDIENCE_CUSTOM,
            expires_at=expires_at,
            is_active=True
        )
        
        # If custom audience, add recipients
        if not send_to_all and user_ids:
            users = User.objects.filter(id__in=user_ids, is_active=True)
            notification.recipients.set(users)
            recipient_count = users.count()
        else:
            recipient_count = User.objects.filter(is_active=True).count()
        
        return Response({
            'message': f'Notification created and sent to {recipient_count} users',
            'notification_id': notification.id,
            'recipient_count': recipient_count
        }, status=status.HTTP_201_CREATED)


class AdminNotificationListView(APIView):
    """
    GET /api/notifications/admin/list/
    
    List all notifications (admin view).
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        notifications = Notification.objects.all().order_by('-created_at')[:50]
        data = []
        for notif in notifications:
            recipient_count = (
                User.objects.filter(is_active=True).count() 
                if notif.audience == Notification.AUDIENCE_ALL 
                else notif.recipients.count()
            )
            read_count = notif.reads.count()
            
            data.append({
                'id': notif.id,
                'title': notif.title,
                'message': notif.message,
                'audience': notif.audience,
                'recipient_count': recipient_count,
                'read_count': read_count,
                'is_active': notif.is_active,
                'is_expired': notif.is_expired(),
                'created_at': notif.created_at,
                'expires_at': notif.expires_at,
            })
        
        return Response({
            'notifications': data,
            'total_count': len(data)
        })
