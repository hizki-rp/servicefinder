from rest_framework import serializers
from django.contrib.auth.models import User
from django.urls import reverse
from .models import UserRecommendationProfile, RecommendedUniversity, RecommendationQuestionnaireResponse
from universities.serializers import UniversitySerializer


class RecommendationProfileSerializer(serializers.ModelSerializer):
    """Serializer for user recommendation profile"""
    
    class Meta:
        model = UserRecommendationProfile
        fields = [
            'preferred_countries', 'preferred_cities', 'preferred_programs',
            'preferred_intake', 'application_fee_preference', 'completed_at',
            'updated_at', 'is_completed'
        ]
        read_only_fields = ['completed_at', 'updated_at', 'is_completed']


class RecommendedUniversitySerializer(serializers.ModelSerializer):
    """Serializer for recommended universities"""
    
    university = UniversitySerializer(read_only=True)
    detail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = RecommendedUniversity
        fields = [
            'id', 'university', 'match_score', 'recommendation_reason',
            'created_at', 'is_active', 'detail_url'
        ]

    def get_detail_url(self, obj):
        request = self.context.get('request')
        url = reverse('university-detail', args=[obj.university_id])
        if request:
            return request.build_absolute_uri(url)
        return url


class QuestionnaireResponseSerializer(serializers.ModelSerializer):
    """Serializer for questionnaire responses"""
    
    class Meta:
        model = RecommendationQuestionnaireResponse
        fields = ['responses', 'completed', 'completed_at', 'updated_at']
        read_only_fields = ['completed_at', 'updated_at']


class RecommendationQuestionnaireSerializer(serializers.Serializer):
    """Serializer for processing questionnaire submission"""
    
    countries = serializers.ListField(
        child=serializers.CharField(max_length=100),
        help_text="List of preferred countries"
    )
    cities = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        help_text="List of preferred cities"
    )
    programs = serializers.ListField(
        child=serializers.CharField(max_length=200),
        help_text="List of preferred programs/courses"
    )
    intake = serializers.CharField(
        max_length=50,
        required=False,
        help_text="Preferred intake period"
    )
    application_fee = serializers.ChoiceField(
        choices=UserRecommendationProfile.APPLICATION_FEE_CHOICES,
        help_text="Application fee preference"
    )
    
    def validate_countries(self, value):
        if not value:
            raise serializers.ValidationError("At least one country must be selected")
        return value
    
    def validate_programs(self, value):
        if not value:
            raise serializers.ValidationError("At least one program must be selected")
        return value
