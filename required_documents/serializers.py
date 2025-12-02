"""
Serializers for document upload API.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    DocumentCategory, 
    DocumentSubmission, 
    DocumentSubmissionBatch,
    UserDocumentProfile,
    DocumentFeedback,
    DocumentRequest
)


class UserDocumentProfileSerializer(serializers.ModelSerializer):
    """Serializer for user document profiles (onboarding data)."""
    
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    
    field_of_study_display = serializers.CharField(source='get_field_of_study_display', read_only=True)
    highest_education_display = serializers.CharField(source='get_highest_education_display', read_only=True)
    applying_to_display = serializers.CharField(source='get_applying_to_display', read_only=True)
    
    class Meta:
        model = UserDocumentProfile
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'field_of_study', 'field_of_study_display',
            'highest_education', 'highest_education_display',
            'applying_to', 'applying_to_display',
            'phone_number', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserDocumentProfileCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating user document profiles."""
    
    class Meta:
        model = UserDocumentProfile
        fields = ['field_of_study', 'highest_education', 'applying_to', 'phone_number']


class DocumentCategorySerializer(serializers.ModelSerializer):
    """Serializer for document categories."""
    
    class Meta:
        model = DocumentCategory
        fields = ['id', 'name', 'description', 'api_key', 'program_type', 'required', 'order']


class DocumentSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for individual document submissions."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    download_url = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = DocumentSubmission
        fields = [
            'id', 'username', 'program_type', 'category_key', 'category_name',
            'original_filename', 'file_size', 'content_type', 'status', 'status_display',
            'admin_notes', 'uploaded_at', 'updated_at', 'download_url',
            'reviewed_at'
        ]
        read_only_fields = ['id', 'uploaded_at', 'updated_at', 'reviewed_at']

    def get_download_url(self, obj):
        """Generate download URL for the document."""
        request = self.context.get('request')
        if request and obj.file:
            return request.build_absolute_uri(f'/api/documents/{obj.id}/download/')
        return None


class DocumentSubmissionAdminSerializer(serializers.ModelSerializer):
    """Detailed serializer for admin document management."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    download_url = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_first_name = serializers.CharField(source='user.first_name', read_only=True)
    user_last_name = serializers.CharField(source='user.last_name', read_only=True)
    reviewed_by_username = serializers.CharField(source='reviewed_by.username', read_only=True)
    user_profile = serializers.SerializerMethodField()
    feedback_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentSubmission
        fields = [
            'id', 'user', 'username', 'user_email', 'user_first_name', 'user_last_name',
            'program_type', 'category_key', 'category_name',
            'original_filename', 'file_size', 'content_type', 'status', 'status_display',
            'admin_notes', 'uploaded_at', 'updated_at', 'download_url',
            'reviewed_by', 'reviewed_by_username', 'reviewed_at',
            'user_profile', 'feedback_count'
        ]
        read_only_fields = ['id', 'uploaded_at', 'updated_at']

    def get_download_url(self, obj):
        request = self.context.get('request')
        if request and obj.file:
            return request.build_absolute_uri(f'/api/documents/{obj.id}/download/')
        return None

    def get_user_profile(self, obj):
        try:
            profile = obj.user.document_profile
            return {
                'field_of_study': profile.get_field_of_study_display(),
                'highest_education': profile.get_highest_education_display(),
                'applying_to': profile.get_applying_to_display(),
                'phone_number': profile.phone_number,
            }
        except UserDocumentProfile.DoesNotExist:
            return None

    def get_feedback_count(self, obj):
        return obj.feedback.count()


class DocumentSubmissionCreateSerializer(serializers.Serializer):
    """Serializer for creating document submissions via file upload."""
    
    program_type = serializers.ChoiceField(choices=['high-school', 'bachelor', 'master'])
    category_key = serializers.CharField(max_length=100)
    file = serializers.FileField()

    def validate_file(self, value):
        """Validate uploaded file."""
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError("File size cannot exceed 10MB.")
        
        allowed_types = [
            'application/pdf',
            'image/jpeg',
            'image/png',
            'image/gif',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        ]
        
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                "Invalid file type. Allowed types: PDF, JPEG, PNG, GIF, DOC, DOCX."
            )
        
        return value


class BulkDocumentUploadSerializer(serializers.Serializer):
    """Serializer for bulk document uploads."""
    
    program_type = serializers.ChoiceField(choices=['high-school', 'bachelor', 'master'])


class DocumentSubmissionBatchSerializer(serializers.ModelSerializer):
    """Serializer for document submission batches."""
    
    submissions = DocumentSubmissionSerializer(many=True, read_only=True)
    submission_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentSubmissionBatch
        fields = ['id', 'program_type', 'submitted_at', 'is_complete', 'submissions', 'submission_count']
        read_only_fields = ['id', 'submitted_at']

    def get_submission_count(self, obj):
        return obj.submissions.count()


class DocumentFeedbackSerializer(serializers.ModelSerializer):
    """Serializer for document feedback."""
    
    admin_username = serializers.CharField(source='admin.username', read_only=True)
    feedback_type_display = serializers.CharField(source='get_feedback_type_display', read_only=True)
    
    class Meta:
        model = DocumentFeedback
        fields = [
            'id', 'submission', 'user', 'admin', 'admin_username',
            'feedback_type', 'feedback_type_display', 'subject', 'message',
            'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DocumentFeedbackCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating document feedback."""
    
    class Meta:
        model = DocumentFeedback
        fields = ['submission', 'user', 'feedback_type', 'subject', 'message']


class DocumentRequestSerializer(serializers.ModelSerializer):
    """Serializer for document requests."""
    
    admin_username = serializers.CharField(source='admin.username', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = DocumentRequest
        fields = [
            'id', 'user', 'username', 'admin', 'admin_username',
            'document_name', 'description', 'deadline', 'status', 'status_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DocumentRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating document requests."""
    
    class Meta:
        model = DocumentRequest
        fields = ['user', 'document_name', 'description', 'deadline']


class UserDocumentSummarySerializer(serializers.Serializer):
    """Summary serializer for user documents in admin list."""
    
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    phone_number = serializers.CharField()
    field_of_study = serializers.CharField()
    highest_education = serializers.CharField()
    applying_to = serializers.CharField()
    total_documents = serializers.IntegerField()
    pending_documents = serializers.IntegerField()
    approved_documents = serializers.IntegerField()
    rejected_documents = serializers.IntegerField()
    last_upload = serializers.DateTimeField()
