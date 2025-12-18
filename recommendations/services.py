from django.db.models import Q
from universities.models import University
from .models import UserRecommendationProfile, RecommendedUniversity
import logging

logger = logging.getLogger(__name__)


class UniversityRecommendationService:
    """Service for generating university recommendations based on user preferences"""
    
    @staticmethod
    def generate_recommendations(user):
        """Generate university recommendations for a user based on their profile"""
        
        try:
            profile = user.recommendation_profile
        except UserRecommendationProfile.DoesNotExist:
            logger.warning(f"No recommendation profile found for user {user.username}")
            return []
        
        if not profile.is_completed:
            logger.warning(f"Incomplete recommendation profile for user {user.username}")
            return []
        
        # Clear existing recommendations
        RecommendedUniversity.objects.filter(user=user).delete()
        
        # Build query based on user preferences
        query = Q()
        
        # Filter by countries
        if profile.preferred_countries:
            query &= Q(country__in=profile.preferred_countries)
        
        # Filter by cities (if specified)
        if profile.preferred_cities:
            query &= Q(city__in=profile.preferred_cities)
        
        # Filter by application fee preference
        fee_filters = UniversityRecommendationService._get_fee_filter(profile.application_fee_preference)
        if fee_filters:
            query &= fee_filters
        
        # Get matching universities
        universities = University.objects.filter(query).distinct()
        
        recommendations = []
        for university in universities:
            # Calculate match score
            match_score = UniversityRecommendationService._calculate_match_score(
                university, profile
            )
            
            # Generate recommendation reason
            reason = UniversityRecommendationService._generate_recommendation_reason(
                university, profile
            )
            
            # Create recommendation
            recommendation = RecommendedUniversity.objects.create(
                user=user,
                university=university,
                match_score=match_score,
                recommendation_reason=reason
            )
            recommendations.append(recommendation)
        
        # Sort by match score and limit to top 20
        recommendations = sorted(recommendations, key=lambda x: x.match_score, reverse=True)[:20]
        
        logger.info(f"Generated {len(recommendations)} recommendations for user {user.username}")
        return recommendations
    
    @staticmethod
    def _get_fee_filter(fee_preference):
        """Get database filter for application fee preference"""
        
        if fee_preference == 'no_fee':
            return Q(application_fee=0) | Q(application_fee__isnull=True)
        elif fee_preference == 'less_than_15':
            return Q(application_fee__lt=15) | Q(application_fee__isnull=True)
        elif fee_preference == 'less_than_30':
            return Q(application_fee__lt=30) | Q(application_fee__isnull=True)
        elif fee_preference == 'less_than_50':
            return Q(application_fee__lt=50) | Q(application_fee__isnull=True)
        elif fee_preference == '50_or_more':
            return Q(application_fee__gte=50)
        
        return Q()  # No filter if preference not specified
    
    @staticmethod
    def _calculate_match_score(university, profile):
        """Calculate match score between university and user profile"""
        
        score = 0.0
        max_score = 100.0
        
        # Country match (40 points)
        if university.country in profile.preferred_countries:
            score += 40
        
        # City match (20 points)
        if profile.preferred_cities and university.city in profile.preferred_cities:
            score += 20
        elif not profile.preferred_cities:
            score += 10  # Partial points if no city preference
        
        # Program match (30 points) - check if any preferred program matches university programs
        program_match = False
        if hasattr(university, 'programs') and university.programs:
            for preferred_program in profile.preferred_programs:
                if any(preferred_program.lower() in program.lower() 
                      for program in university.programs if program):
                    program_match = True
                    break
        
        if program_match:
            score += 30
        
        # Application fee match (10 points)
        fee_match = UniversityRecommendationService._check_fee_match(
            university.application_fee, profile.application_fee_preference
        )
        if fee_match:
            score += 10
        
        return min(score, max_score)
    
    @staticmethod
    def _check_fee_match(university_fee, preference):
        """Check if university fee matches user preference"""
        
        if not university_fee:
            university_fee = 0
        
        if preference == 'no_fee':
            return university_fee == 0
        elif preference == 'less_than_15':
            return university_fee < 15
        elif preference == 'less_than_30':
            return university_fee < 30
        elif preference == 'less_than_50':
            return university_fee < 50
        elif preference == '50_or_more':
            return university_fee >= 50
        
        return True  # Default to match if no preference
    
    @staticmethod
    def _generate_recommendation_reason(university, profile):
        """Generate a human-readable reason for the recommendation"""
        
        reasons = []
        
        # Country match
        if university.country in profile.preferred_countries:
            reasons.append(f"Located in your preferred country: {university.country}")
        
        # City match
        if profile.preferred_cities and university.city in profile.preferred_cities:
            reasons.append(f"Located in your preferred city: {university.city}")
        
        # Fee match
        fee_match = UniversityRecommendationService._check_fee_match(
            university.application_fee, profile.application_fee_preference
        )
        if fee_match:
            fee_text = UniversityRecommendationService._get_fee_text(profile.application_fee_preference)
            reasons.append(f"Application fee matches your preference: {fee_text}")
        
        # University ranking or other features
        if hasattr(university, 'ranking') and university.ranking:
            reasons.append(f"Well-ranked institution (Rank: {university.ranking})")
        
        return "; ".join(reasons) if reasons else "Matches your general preferences"
    
    @staticmethod
    def _get_fee_text(fee_preference):
        """Convert fee preference code to readable text"""
        
        fee_map = {
            'no_fee': 'No application fee',
            'less_than_15': 'Less than $15',
            'less_than_30': 'Less than $30',
            'less_than_50': 'Less than $50',
            '50_or_more': '$50 or more'
        }
        return fee_map.get(fee_preference, 'Unknown')