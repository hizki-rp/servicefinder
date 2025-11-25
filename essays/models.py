from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Essay(models.Model):
    """Essay model for scholarship essays - shared templates that everyone can view and edit"""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='essays', help_text="Original creator (optional for templates)")
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=1000, blank=True, help_text="Short description or preview")
    # Content stored as JSON from TipTap editor
    # Structure: {"json": {...}, "html": "...", "text": "..."}
    content = models.JSONField(default=dict, help_text="Rich text content from TipTap editor")
    is_template = models.BooleanField(default=True, help_text="Whether this is a shared template")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Essay"
        verbose_name_plural = "Essays"
    
    def __str__(self):
        creator = self.user.username if self.user else "System"
        return f"{self.title} by {creator}"

