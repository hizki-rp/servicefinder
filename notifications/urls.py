from django.urls import path
from .views import (
    NotificationListView, 
    mark_all_read,
    AdminNotificationCreateView,
    AdminNotificationListView
)

urlpatterns = [
    path('notifications/', NotificationListView.as_view(), name='notifications-list'),
    path('notifications/mark-all-read/', mark_all_read, name='notifications-mark-all-read'),
    # Admin endpoints
    path('notifications/admin/create/', AdminNotificationCreateView.as_view(), name='admin-notification-create'),
    path('notifications/admin/list/', AdminNotificationListView.as_view(), name='admin-notification-list'),
]
