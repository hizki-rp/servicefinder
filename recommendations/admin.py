from django.contrib import admin
from .models import UserRecommendationProfile, RecommendedUniversity, RecommendationQuestionnaireResponse


@admin.register(UserRecommendationProfile)
class UserRecommendationProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_completed', 'completed_at', 'updated_at']
    list_filter = ['completed_at', 'updated_at', 'application_fee_preference']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['completed_at', 'updated_at', 'is_completed']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Preferences', {
            'fields': (
                'preferred_countries', 'preferred_cities', 'preferred_programs',
                'preferred_intake', 'application_fee_preference'
            )
        }),
        ('Metadata', {
            'fields': ('is_completed', 'completed_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(RecommendedUniversity)
class RecommendedUniversityAdmin(admin.ModelAdmin):
    list_display = ['user', 'university', 'match_score', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'match_score']
    search_fields = ['user__username', 'university__name', 'university__country']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Recommendation', {
            'fields': ('user', 'university', 'match_score', 'is_active')
        }),
        ('Details', {
            'fields': ('recommendation_reason',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )


@admin.register(RecommendationQuestionnaireResponse)
class RecommendationQuestionnaireResponseAdmin(admin.ModelAdmin):
    list_display = ['user', 'completed', 'completed_at', 'updated_at']
    list_filter = ['completed', 'completed_at', 'updated_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['completed_at', 'updated_at']