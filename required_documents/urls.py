"""
URL configuration for document upload endpoints.
"""

from django.urls import path
from .views import (
    # User endpoints
    DocumentCategoryListView,
    UserDocumentsView,
    UserDocumentProfileView,
    DocumentUploadView,
    BulkDocumentUploadView,
    DocumentDownloadView,
    DocumentDeleteView,
    DocumentBatchListView,
    UserFeedbackView,
    UserDocumentRequestsView,
    # Admin endpoints
    AdminUserDocumentListView,
    AdminSubmissionListView,
    AdminSubmissionDetailView,
    AdminSendFeedbackView,
    AdminRequestDocumentView,
    AdminDocumentRequestListView,
    AdminDocumentStatsView,
)

urlpatterns = [
    # User endpoints
    path('documents/profile/', UserDocumentProfileView.as_view(), name='document-profile'),
    path('documents/categories/', DocumentCategoryListView.as_view(), name='document-categories'),
    path('documents/', UserDocumentsView.as_view(), name='user-documents'),
    path('documents/upload/', DocumentUploadView.as_view(), name='document-upload'),
    path('documents/bulk-upload/', BulkDocumentUploadView.as_view(), name='document-bulk-upload'),
    path('documents/<int:pk>/download/', DocumentDownloadView.as_view(), name='document-download'),
    path('documents/<int:pk>/', DocumentDeleteView.as_view(), name='document-delete'),
    path('documents/batches/', DocumentBatchListView.as_view(), name='document-batches'),
    path('documents/feedback/', UserFeedbackView.as_view(), name='user-feedback'),
    path('documents/requests/', UserDocumentRequestsView.as_view(), name='user-document-requests'),
    
    # Admin endpoints
    path('documents/admin/users/', AdminUserDocumentListView.as_view(), name='admin-document-users'),
    path('documents/admin/submissions/', AdminSubmissionListView.as_view(), name='admin-submissions'),
    path('documents/admin/submissions/<int:pk>/', AdminSubmissionDetailView.as_view(), name='admin-submission-detail'),
    path('documents/admin/feedback/', AdminSendFeedbackView.as_view(), name='admin-send-feedback'),
    path('documents/admin/request/', AdminRequestDocumentView.as_view(), name='admin-request-document'),
    path('documents/admin/requests/', AdminDocumentRequestListView.as_view(), name='admin-document-requests'),
    path('documents/admin/stats/', AdminDocumentStatsView.as_view(), name='admin-document-stats'),
]
