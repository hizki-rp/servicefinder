from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from recommendations.models import UserRecommendationProfile
from recommendations.services import UniversityRecommendationService


class Command(BaseCommand):
    help = 'Test university recommendation system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username to test recommendations for',
            default='testuser'
        )

    def handle(self, *args, **options):
        username = options['username']
        
        # Get or create test user
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(f'Created test user: {username}')
        else:
            self.stdout.write(f'Using existing user: {username}')
        
        # Create or update recommendation profile
        profile, created = UserRecommendationProfile.objects.get_or_create(
            user=user,
            defaults={
                'preferred_countries': ['United States', 'Canada', 'United Kingdom'],
                'preferred_cities': ['New York', 'Toronto', 'London'],
                'preferred_programs': ['Computer Science', 'Engineering', 'Business'],
                'preferred_intake': 'Fall (September)',
                'application_fee_preference': 'less_than_50'
            }
        )
        
        if created:
            self.stdout.write('Created recommendation profile')
        else:
            self.stdout.write('Using existing recommendation profile')
        
        # Generate recommendations
        self.stdout.write('Generating recommendations...')
        recommendations = UniversityRecommendationService.generate_recommendations(user)
        
        self.stdout.write(f'Generated {len(recommendations)} recommendations:')
        for rec in recommendations:
            self.stdout.write(f'  - {rec.university.name} (Score: {rec.match_score})')
            self.stdout.write(f'    Reason: {rec.recommendation_reason}')
        
        self.stdout.write('Test completed successfully!')