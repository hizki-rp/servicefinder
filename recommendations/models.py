from django.db import models
from django.contrib.auth.models import User
from universities.models import University


class UserRecommendationProfile(models.Model):
    """Store user's preferences for university recommendations"""
    
    APPLICATION_FEE_CHOICES = [
        ('no_fee', 'No Fee'),
        ('less_than_15', 'Less than $15'),
        ('less_than_30', 'Less than $30'),
        ('less_than_50', 'Less than $50'),
        ('50_or_more', '$50 or more'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='recommendation_profile')
    
    # User preferences
    preferred_countries = models.JSONField(default=list, help_text="List of preferred country codes")
    preferred_cities = models.JSONField(default=list, help_text="List of preferred cities")
    preferred_programs = models.JSONField(default=list, help_text="List of preferred program/course names")
    preferred_intake = models.CharField(max_length=50, blank=True, help_text="Preferred intake period")
    application_fee_preference = models.CharField(
        max_length=20, 
        choices=APPLICATION_FEE_CHOICES,
        blank=True,
        help_text="Application fee preference"
    )
    
    # Metadata
    completed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Recommendation Profile"
        verbose_name_plural = "User Recommendation Profiles"
    
    def __str__(self):
        return f"Recommendation Profile for {self.user.username}"
    
    @property
    def is_completed(self):
        """Check if user has completed the recommendation questionnaire"""
        return bool(
            self.preferred_countries and 
            self.preferred_programs and 
            self.application_fee_preference
        )


class RecommendedUniversity(models.Model):
    """Store recommended universities for each user"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommended_universities')
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    
    # Recommendation metadata
    match_score = models.FloatField(default=0.0, help_text="Match score (0-100)")
    recommendation_reason = models.TextField(blank=True, help_text="Why this university was recommended")
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, help_text="Whether this recommendation is still active")
    
    class Meta:
        unique_together = ['user', 'university']
        ordering = ['-match_score', '-created_at']
        verbose_name = "Recommended University"
        verbose_name_plural = "Recommended Universities"
    
    def __str__(self):
        return f"{self.university.name} recommended to {self.user.username} (Score: {self.match_score})"


class RecommendationQuestionnaireResponse(models.Model):
    """Store user responses to recommendation questionnaire"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='questionnaire_response')
    
    # Store the full questionnaire response as JSON
    responses = models.JSONField(default=dict, help_text="Complete questionnaire responses")
    
    # Quick access fields
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Questionnaire Response"
        verbose_name_plural = "Questionnaire Responses"
    
    def __str__(self):
        status = "Completed" if self.completed else "Incomplete"
        return f"Questionnaire for {self.user.username} - {status}"