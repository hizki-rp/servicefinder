from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Essay(models.Model):
    """Essay model for scholarship essays - each essay belongs to a specific user"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='essays', help_text="Owner of the essay")
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=1000, blank=True, help_text="Short description or preview")
    # Content stored as JSON from TipTap editor
    # Structure: {"json": {...}, "html": "...", "text": "..."}
    content = models.JSONField(default=dict, help_text="Rich text content from TipTap editor")
    is_template = models.BooleanField(default=False, help_text="Whether this is a template")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']  # Show most recently edited first
        verbose_name = "Essay"
        verbose_name_plural = "Essays"
    
    def save(self, *args, **kwargs):
        # SAFETY: Never allow user essays to be templates
        # Only allow templates for system/seeded essays (no user or specific template users)
        template_usernames = ['rakibul', 'miki', 'randall', 'seun', 'zeynep']
        if self.user and self.user.username not in template_usernames:
            self.is_template = False
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title} by {self.user.username}"

