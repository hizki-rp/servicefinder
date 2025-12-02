"""
Models for storing user document submissions and onboarding data.

This module defines the database models for:
- UserDocumentProfile: Stores user's onboarding answers
- DocumentCategory: Predefined categories of documents
- DocumentSubmission: User's uploaded documents with metadata
- DocumentFeedback: Admin feedback on user documents
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os
import uuid


def document_upload_path(instance, filename):
    """Generate unique file path for uploaded documents."""
    ext = filename.split('.')[-1]
    unique_name = f"{uuid.uuid4()}.{ext}"
    return os.path.join('documents', str(instance.user.id), instance.program_type, unique_name)


class UserDocumentProfile(models.Model):
    """
    Stores user's onboarding answers for document submission.
    """
    FIELD_OF_STUDY_CHOICES = [
        ('computer-science', 'Computer Science & IT'),
        ('engineering', 'Engineering'),
        ('business', 'Business & Management'),
        ('medicine', 'Medicine & Health Sciences'),
        ('law', 'Law'),
        ('arts', 'Arts & Humanities'),
        ('social-sciences', 'Social Sciences'),
        ('natural-sciences', 'Natural Sciences'),
        ('education', 'Education'),
        ('architecture', 'Architecture & Design'),
        ('agriculture', 'Agriculture & Environmental'),
        ('media', 'Media & Communications'),
        ('hospitality', 'Hospitality & Tourism'),
        ('other', 'Other'),
    ]

    EDUCATION_LEVEL_CHOICES = [
        ('high-school', 'High School / Secondary School'),
        ('some-college', 'Some College (No Degree)'),
        ('associate', 'Associate Degree'),
        ('bachelor', "Bachelor's Degree"),
        ('master', "Master's Degree"),
        ('doctorate', 'Doctorate / PhD'),
    ]

    APPLYING_TO_CHOICES = [
        ('high-school', 'High School Program'),
        ('bachelor', "Bachelor's Degree"),
        ('master', "Master's Degree"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='document_profile')
    field_of_study = models.CharField(max_length=50, choices=FIELD_OF_STUDY_CHOICES, blank=True)
    highest_education = models.CharField(max_length=20, choices=EDUCATION_LEVEL_CHOICES, blank=True)
    applying_to = models.CharField(max_length=20, choices=APPLYING_TO_CHOICES, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Document Profile"
        verbose_name_plural = "User Document Profiles"

    def __str__(self):
        return f"{self.user.username} - {self.get_field_of_study_display()}"


class DocumentCategory(models.Model):
    """
    Predefined categories of documents that users can upload.
    """
    PROGRAM_CHOICES = [
        ('high-school', "High School Program"),
        ('bachelor', "Bachelor's Program"),
        ('master', "Master's Program"),
        ('all', 'All Programs'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    api_key = models.CharField(max_length=100, unique=True, help_text="Unique key used in API calls")
    program_type = models.CharField(max_length=20, choices=PROGRAM_CHOICES, default='all')
    required = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Document Category"
        verbose_name_plural = "Document Categories"
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_program_type_display()})"


class DocumentSubmission(models.Model):
    """
    Stores user's uploaded documents with associated metadata.
    """
    PROGRAM_CHOICES = [
        ('high-school', "High School Program"),
        ('bachelor', "Bachelor's Program"),
        ('master', "Master's Program"),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('resubmit', 'Resubmission Required'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document_submissions')
    program_type = models.CharField(max_length=20, choices=PROGRAM_CHOICES)
    category = models.ForeignKey(
        DocumentCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='submissions'
    )
    category_key = models.CharField(max_length=100, help_text="API key for the document category")
    original_filename = models.CharField(max_length=255)
    file = models.FileField(upload_to=document_upload_path)
    file_size = models.PositiveIntegerField(default=0, help_text="File size in bytes")
    content_type = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, help_text="Internal admin notes")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reviewed_documents'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Document Submission"
        verbose_name_plural = "Document Submissions"
        ordering = ['-uploaded_at']
        unique_together = ['user', 'category_key', 'program_type']

    def __str__(self):
        return f"{self.user.username} - {self.category_key} ({self.program_type})"

    @property
    def file_extension(self):
        """Return the file extension."""
        return self.original_filename.split('.')[-1].lower() if '.' in self.original_filename else ''

    def delete(self, *args, **kwargs):
        """Delete the file when the model instance is deleted."""
        if self.file:
            self.file.delete(save=False)
        super().delete(*args, **kwargs)


class DocumentFeedback(models.Model):
    """
    Stores admin feedback on user documents.
    """
    FEEDBACK_TYPE_CHOICES = [
        ('general', 'General Feedback'),
        ('improvement', 'Improvement Suggestion'),
        ('issue', 'Issue Found'),
        ('approval', 'Approval Note'),
        ('request', 'Document Request'),
    ]

    submission = models.ForeignKey(
        DocumentSubmission, 
        on_delete=models.CASCADE, 
        related_name='feedback',
        null=True,
        blank=True
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='document_feedback'
    )
    admin = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='given_feedback'
    )
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPE_CHOICES, default='general')
    subject = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Document Feedback"
        verbose_name_plural = "Document Feedback"
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback for {self.user.username}: {self.subject}"


class DocumentRequest(models.Model):
    """
    Admin requests for additional documents from users.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document_requests')
    admin = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='sent_document_requests'
    )
    document_name = models.CharField(max_length=255)
    description = models.TextField(help_text="Describe what document is needed and why")
    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Document Request"
        verbose_name_plural = "Document Requests"
        ordering = ['-created_at']

    def __str__(self):
        return f"Request for {self.user.username}: {self.document_name}"


class DocumentSubmissionBatch(models.Model):
    """
    Groups multiple document submissions into a single batch.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document_batches')
    program_type = models.CharField(max_length=20, choices=DocumentSubmission.PROGRAM_CHOICES)
    submissions = models.ManyToManyField(DocumentSubmission, related_name='batches')
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_complete = models.BooleanField(default=False, help_text="Whether all required documents are submitted")

    class Meta:
        verbose_name = "Document Submission Batch"
        verbose_name_plural = "Document Submission Batches"
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.user.username} - {self.program_type} batch ({self.submitted_at.strftime('%Y-%m-%d')})"
