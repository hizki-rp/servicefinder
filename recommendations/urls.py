from django.urls import path
from . import views

urlpatterns = [
    path('recommendations/', views.RecommendedUniversitiesView.as_view(), name='recommended-universities'),
    path('recommendations/profile/', views.RecommendationProfileView.as_view(), name='recommendation-profile'),
    path('recommendations/questionnaire/submit/', views.submit_questionnaire, name='submit-questionnaire'),
    path('recommendations/questionnaire/status/', views.questionnaire_status, name='questionnaire-status'),
    path('recommendations/questionnaire/options/', views.questionnaire_options, name='questionnaire-options'),
    path('recommendations/questionnaire/cities/', views.cities_by_country, name='cities-by-country'),
    path('recommendations/refresh/', views.refresh_recommendations, name='refresh-recommendations'),
]