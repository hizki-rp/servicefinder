from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import models
from .models import UserRecommendationProfile, RecommendedUniversity, RecommendationQuestionnaireResponse
from .serializers import (
    RecommendationProfileSerializer, RecommendedUniversitySerializer,
    QuestionnaireResponseSerializer, RecommendationQuestionnaireSerializer
)
from .services import UniversityRecommendationService
import logging

# Try to import Profile model, handle if it doesn't exist
try:
    from profiles.models import Profile
except ImportError:
    Profile = None

logger = logging.getLogger(__name__)


class RecommendationProfileView(generics.RetrieveUpdateAPIView):
    """Get or update user's recommendation profile"""
    
    serializer_class = RecommendationProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        profile, created = UserRecommendationProfile.objects.get_or_create(
            user=self.request.user
        )
        return profile


class RecommendedUniversitiesView(generics.ListAPIView):
    """List recommended universities for the authenticated user"""
    
    serializer_class = RecommendedUniversitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return RecommendedUniversity.objects.filter(
            user=self.request.user,
            is_active=True
        ).select_related('university')
    
    def list(self, request, *args, **kwargs):
        # Check if user has active subscription (skip if Profile model not available)
        if Profile:
            try:
                profile = request.user.profile
                if profile.subscription_status != 'active':
                    return Response({
                        'error': 'Active subscription required',
                        'message': 'You need an active subscription to view university recommendations.',
                        'subscription_status': profile.subscription_status
                    }, status=status.HTTP_403_FORBIDDEN)
            except Profile.DoesNotExist:
                return Response({
                    'error': 'Profile not found',
                    'message': 'User profile not found. Please complete your profile setup.'
                }, status=status.HTTP_404_NOT_FOUND)
            except AttributeError:
                # If profile doesn't have subscription_status field, skip check
                pass
        
        return super().list(request, *args, **kwargs)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_questionnaire(request):
    """Submit recommendation questionnaire and generate recommendations"""
    
    # Check subscription status (skip if Profile model not available)
    if Profile:
        try:
            profile = request.user.profile
            if profile.subscription_status != 'active':
                return Response({
                    'error': 'Active subscription required',
                    'message': 'You need an active subscription to access university recommendations.'
                }, status=status.HTTP_403_FORBIDDEN)
        except Profile.DoesNotExist:
            return Response({
                'error': 'Profile not found',
                'message': 'Please complete your profile setup first.'
            }, status=status.HTTP_404_NOT_FOUND)
        except AttributeError:
            # If profile doesn't have subscription_status field, skip check
            pass
    
    logger.info(f"Received questionnaire data: {request.data}")
    
    serializer = RecommendationQuestionnaireSerializer(data=request.data)
    if not serializer.is_valid():
        logger.error(f"Serializer validation errors: {serializer.errors}")
        return Response({
            'error': 'Invalid questionnaire data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    validated_data = serializer.validated_data
    
    try:
        # Create or update recommendation profile
        profile, created = UserRecommendationProfile.objects.get_or_create(
            user=request.user,
            defaults={
                'preferred_countries': validated_data['countries'],
                'preferred_cities': validated_data.get('cities', []),
                'preferred_programs': validated_data['programs'],
                'preferred_intake': validated_data.get('intake', ''),
                'application_fee_preference': validated_data['application_fee']
            }
        )
        
        if not created:
            # Update existing profile
            profile.preferred_countries = validated_data['countries']
            profile.preferred_cities = validated_data.get('cities', [])
            profile.preferred_programs = validated_data['programs']
            profile.preferred_intake = validated_data.get('intake', '')
            profile.application_fee_preference = validated_data['application_fee']
            profile.save()
        
        # Store questionnaire response
        questionnaire_response, _ = RecommendationQuestionnaireResponse.objects.get_or_create(
            user=request.user,
            defaults={
                'responses': request.data,
                'completed': True
            }
        )
        
        if not questionnaire_response.completed:
            questionnaire_response.responses = request.data
            questionnaire_response.completed = True
            questionnaire_response.save()
        
        # Generate recommendations
        try:
            recommendations = UniversityRecommendationService.generate_recommendations(request.user)
        except Exception as rec_error:
            logger.error(f"Error generating recommendations: {str(rec_error)}")
            # Continue without recommendations for now
            recommendations = []
        
        return Response({
            'success': True,
            'message': f'Questionnaire completed successfully. Generated {len(recommendations)} recommendations.',
            'recommendations_count': len(recommendations),
            'profile_completed': profile.is_completed
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        import traceback
        logger.error(f"Error processing questionnaire for user {request.user.username}: {str(e)}")
        return Response({
            'error': 'Failed to process questionnaire',
            'message': 'An error occurred while processing your responses. Please try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_recommendations(request):
    """Refresh university recommendations for the user"""
    
    # Check subscription status (skip if Profile model not available)
    if Profile:
        try:
            profile = request.user.profile
            if profile.subscription_status != 'active':
                return Response({
                    'error': 'Active subscription required',
                    'message': 'You need an active subscription to refresh recommendations.'
                }, status=status.HTTP_403_FORBIDDEN)
        except Profile.DoesNotExist:
            return Response({
                'error': 'Profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except AttributeError:
            # If profile doesn't have subscription_status field, skip check
            pass
    
    try:
        # Check if user has completed questionnaire
        recommendation_profile = request.user.recommendation_profile
        if not recommendation_profile.is_completed:
            return Response({
                'error': 'Questionnaire not completed',
                'message': 'Please complete the recommendation questionnaire first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate new recommendations
        recommendations = UniversityRecommendationService.generate_recommendations(request.user)
        
        return Response({
            'success': True,
            'message': f'Recommendations refreshed successfully. Found {len(recommendations)} universities.',
            'recommendations_count': len(recommendations)
        })
        
    except UserRecommendationProfile.DoesNotExist:
        return Response({
            'error': 'No recommendation profile found',
            'message': 'Please complete the recommendation questionnaire first.'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error refreshing recommendations for user {request.user.username}: {str(e)}")
        return Response({
            'error': 'Failed to refresh recommendations',
            'message': 'An error occurred while refreshing recommendations. Please try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def questionnaire_status(request):
    """Check if user has completed the recommendation questionnaire"""
    
    try:
        profile = UserRecommendationProfile.objects.get(user=request.user)
        has_recommendations = RecommendedUniversity.objects.filter(
            user=request.user, is_active=True
        ).exists()
        
        return Response({
            'completed': profile.is_completed,
            'has_recommendations': has_recommendations,
            'profile': RecommendationProfileSerializer(profile).data
        })
    except UserRecommendationProfile.DoesNotExist:
        return Response({
            'completed': False,
            'has_recommendations': False,
            'profile': None
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cities_by_country(request):
    """Get cities for selected countries"""
    
    try:
        from universities.models import University
        from django.db.models import Q
        
        countries = request.GET.getlist('countries[]')
        if not countries:
            return Response({'cities': []})
        
        cities = University.objects.filter(
            country__in=countries
        ).exclude(
            Q(city__isnull=True) | Q(city__exact='')
        ).values_list('city', flat=True).distinct().order_by('city')
        
        return Response({'cities': list(cities)})
        
    except ImportError:
        # If University model doesn't exist, return empty
        return Response({'cities': []})
    except Exception as e:
        logger.error(f"Error in cities_by_country: {str(e)}")
        return Response({'cities': []})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def questionnaire_options(request):
    """Get available options for the questionnaire from actual university data"""
    
    try:
        from universities.models import University
        from django.db.models import Q
        
        # Get unique countries from universities
        countries = University.objects.exclude(
            Q(country__isnull=True) | Q(country__exact='')
        ).values_list('country', flat=True).distinct().order_by('country')
        
        # Get unique cities from universities
        cities = University.objects.exclude(
            Q(city__isnull=True) | Q(city__exact='')
        ).values_list('city', flat=True).distinct().order_by('city')
        
        # Get unique programs from universities (flatten the JSON arrays)
        programs_set = set()
        try:
            universities_with_programs = University.objects.exclude(
                Q(programs__isnull=True) | Q(programs__exact=[])
            ).values_list('programs', flat=True)
            
            for program_list in universities_with_programs:
                if program_list and isinstance(program_list, list):
                    for program in program_list:
                        if program and program.strip():
                            programs_set.add(program.strip())
        except Exception:
            # If programs field doesn't exist or has issues, use default programs
            pass
        
        programs = sorted(list(programs_set)) if programs_set else []
        
        # Get application fee ranges based on actual data
        fee_stats = {'min_fee': None, 'max_fee': None}
        try:
            fee_stats = University.objects.exclude(
                application_fee__isnull=True
            ).aggregate(
                min_fee=models.Min('application_fee'),
                max_fee=models.Max('application_fee')
            )
        except Exception:
            # If application_fee field doesn't exist, use default
            pass
        
        return Response({
            'countries': list(countries),
            'cities': list(cities),
            'programs': programs if programs else [
                'Computer Science', 'Engineering', 'Business Administration',
                'Medicine', 'Law', 'Psychology', 'Economics', 'Mathematics'
            ],
            'intakes': [
                'Fall (September)', 'Spring (January)', 'Summer (May)',
                'Winter (December)', 'Any'
            ],
            'application_fees': [
                {'value': 'no_fee', 'label': 'No Fee'},
                {'value': 'less_than_15', 'label': 'Less than $15'},
                {'value': 'less_than_30', 'label': 'Less than $30'},
                {'value': 'less_than_50', 'label': 'Less than $50'},
                {'value': '50_or_more', 'label': '$50 or more'}
            ],
            'fee_stats': fee_stats
        })
        
    except ImportError:
        # If University model doesn't exist, return default options
        return Response({
            'countries': [
                'United States', 'Canada', 'United Kingdom', 'Australia', 
                'Germany', 'Netherlands', 'France', 'Sweden', 'Norway'
            ],
            'cities': [
                'New York', 'London', 'Toronto', 'Sydney', 'Berlin',
                'Amsterdam', 'Paris', 'Stockholm', 'Oslo'
            ],
            'programs': [
                'Computer Science', 'Engineering', 'Business Administration',
                'Medicine', 'Law', 'Psychology', 'Economics', 'Mathematics',
                'Physics', 'Chemistry', 'Biology', 'Environmental Science'
            ],
            'intakes': [
                'Fall (September)', 'Spring (January)', 'Summer (May)',
                'Winter (December)', 'Any'
            ],
            'application_fees': [
                {'value': 'no_fee', 'label': 'No Fee'},
                {'value': 'less_than_15', 'label': 'Less than $15'},
                {'value': 'less_than_30', 'label': 'Less than $30'},
                {'value': 'less_than_50', 'label': 'Less than $50'},
                {'value': '50_or_more', 'label': '$50 or more'}
            ],
            'fee_stats': {'min_fee': 0, 'max_fee': 100}
        })
    except Exception as e:
        logger.error(f"Error in questionnaire_options: {str(e)}")
        return Response({
            'error': 'Failed to load options',
            'message': 'Please try again later'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)