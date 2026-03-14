"""
Django management command to seed test providers for all 12 categories.
Usage: python manage.py seed_test_providers
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from providers.models import ProviderProfile, ProviderService
from decimal import Decimal
import random


class Command(BaseCommand):
    help = 'Seeds the database with test providers for all 12 categories'

    # 12 categories matching frontend
    CATEGORIES = [
        'Plumber', 'Electrician', 'Cleaner', 'Handyman',
        'Painter', 'Carpenter', 'Gardener', 'Moving',
        'Pet Care', 'Tutor', 'Chef', 'More'
    ]

    # Sample provider data
    PROVIDER_NAMES = [
        ('Ahmed', 'Kebede'), ('Sara', 'Mohammed'), ('John', 'Desta'),
        ('Fatima', 'Ali'), ('Michael', 'Tesfaye'), ('Hanna', 'Bekele'),
        ('David', 'Yohannes'), ('Marta', 'Girma'), ('Samuel', 'Haile'),
        ('Rahel', 'Tadesse'), ('Daniel', 'Mulugeta'), ('Selam', 'Abebe'),
        ('Yonas', 'Getachew'), ('Bethlehem', 'Assefa'), ('Dawit', 'Lemma'),
        ('Tigist', 'Negash'), ('Elias', 'Worku'), ('Meseret', 'Alemu'),
        ('Biniam', 'Tekle'), ('Selamawit', 'Mekonnen'), ('Getnet', 'Tadele'),
        ('Almaz', 'Gebre'), ('Tesfaye', 'Berhanu'), ('Alem', 'Desta'),
        ('Mulugeta', 'Abera'), ('Tsion', 'Fekadu'), ('Yared', 'Mengistu'),
        ('Hiwot', 'Tilahun'), ('Abebe', 'Wolde'), ('Senait', 'Amare'),
        ('Kidus', 'Teshome'), ('Meron', 'Ayele'), ('Bereket', 'Sisay'),
        ('Eyerusalem', 'Demissie'), ('Henok', 'Gebreyesus'), ('Liya', 'Tadesse')
    ]

    # Addis Ababa coordinates (center: 9.03, 38.76)
    # Generate coordinates within ~5km radius
    BASE_LAT = Decimal('9.030000')
    BASE_LNG = Decimal('38.760000')

    def add_arguments(self, parser):
        parser.add_argument(
            '--providers-per-category',
            type=int,
            default=3,
            help='Number of providers to create per category (default: 3)'
        )

    def handle(self, *args, **options):
        providers_per_category = options['providers_per_category']

        # Disconnect the UserDashboard signal to avoid errors on fresh DBs
        # where universities tables may not exist yet
        try:
            from universities.models import create_user_dashboard
            from django.db.models.signals import post_save
            from django.contrib.auth.models import User as AuthUser
            post_save.disconnect(create_user_dashboard, sender=AuthUser)
            self.stdout.write(self.style.WARNING('⚠️  Disconnected UserDashboard signal for seeding'))
        except Exception:
            pass

        self.stdout.write(self.style.SUCCESS(
            f'\n🌱 Seeding {providers_per_category} providers for each of {len(self.CATEGORIES)} categories...\n'
        ))

        total_created = 0
        provider_index = 0

        for category in self.CATEGORIES:
            self.stdout.write(f'\n📦 Creating providers for: {category}')
            
            for i in range(providers_per_category):
                if provider_index >= len(self.PROVIDER_NAMES):
                    provider_index = 0  # Wrap around if we run out of names
                
                first_name, last_name = self.PROVIDER_NAMES[provider_index]
                username = f"{first_name.lower()}{last_name.lower()}{provider_index}"
                
                # Create or get user
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'email': f'{username}@servicefinder.et'
                    }
                )
                
                if created:
                    user.set_password('test123456')
                    user.save()
                
                # Create or get provider profile
                profile, profile_created = ProviderProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'phone_number': f'+2519{random.randint(10000000, 99999999)}',
                        'city': 'Addis Ababa',
                        'country': 'Ethiopia',
                        'latitude': self._random_coordinate(self.BASE_LAT, 0.05),
                        'longitude': self._random_coordinate(self.BASE_LNG, 0.05),
                        'national_id_verified': True,
                        'payment_verified': True,
                        'is_verified': True,
                        'rating': round(random.uniform(4.0, 5.0), 1),
                        'total_reviews': random.randint(10, 150)
                    }
                )
                
                # Ensure profile is verified
                if not profile.is_verified:
                    profile.national_id_verified = True
                    profile.payment_verified = True
                    profile.is_verified = True
                    profile.rating = round(random.uniform(4.0, 5.0), 1)
                    profile.total_reviews = random.randint(10, 150)
                    profile.save()
                
                # Create service
                service_name = self._generate_service_name(category, first_name)
                service_description = self._generate_description(category)
                
                service, service_created = ProviderService.objects.get_or_create(
                    provider=user,
                    service_category=category,
                    defaults={
                        'name': service_name,
                        'description': service_description,
                        'price_type': random.choice(['hourly', 'fixed']),
                        'hourly_rate': Decimal(random.randint(200, 800)),
                        'base_price': Decimal(random.randint(500, 2000)),
                        'latitude': self._random_coordinate(self.BASE_LAT, 0.05),
                        'longitude': self._random_coordinate(self.BASE_LNG, 0.05),
                        'city': 'Addis Ababa',
                        'country': 'Ethiopia',
                        'is_active': True,
                        'verification_status': 'approved'
                    }
                )
                
                # Ensure service is approved
                if service.verification_status != 'approved':
                    service.verification_status = 'approved'
                    service.is_active = True
                    service.save()
                
                if service_created:
                    total_created += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Created: {first_name} {last_name} - {service_name}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠ Already exists: {first_name} {last_name}')
                    )
                
                provider_index += 1

        self.stdout.write(self.style.SUCCESS(
            f'\n\n🎉 Successfully seeded {total_created} new providers!'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'📊 Total providers in database: {ProviderService.objects.filter(is_active=True, verification_status="approved").count()}'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'✅ All providers are verified and ready to be discovered!\n'
        ))

    def _random_coordinate(self, base, variance):
        """Generate random coordinate within variance range"""
        offset = Decimal(str(random.uniform(-variance, variance)))
        return base + offset

    def _generate_service_name(self, category, first_name):
        """Generate service name based on category"""
        templates = {
            'Plumber': f"{first_name}'s Professional Plumbing",
            'Electrician': f"{first_name}'s Electrical Services",
            'Cleaner': f"{first_name}'s Cleaning Solutions",
            'Handyman': f"{first_name}'s Handyman Services",
            'Painter': f"{first_name}'s Painting & Decoration",
            'Carpenter': f"{first_name}'s Carpentry Works",
            'Gardener': f"{first_name}'s Garden Care",
            'Moving': f"{first_name}'s Moving & Transport",
            'Pet Care': f"{first_name}'s Pet Care Services",
            'Tutor': f"{first_name}'s Tutoring Services",
            'Chef': f"{first_name}'s Catering & Chef Services",
            'More': f"{first_name}'s General Services"
        }
        return templates.get(category, f"{first_name}'s {category} Services")

    def _generate_description(self, category):
        """Generate description based on category"""
        descriptions = {
            'Plumber': 'Professional plumbing services for residential and commercial properties. Expert in pipe repairs, installations, and emergency services. Available 24/7.',
            'Electrician': 'Licensed electrician providing safe and reliable electrical services. Specializing in installations, repairs, and maintenance. Quick response time.',
            'Cleaner': 'Professional cleaning services for homes and offices. Deep cleaning, regular maintenance, and specialized cleaning solutions. Eco-friendly products.',
            'Handyman': 'Skilled handyman for all your home repair needs. From minor fixes to major renovations. Reliable and affordable service.',
            'Painter': 'Expert painting and decoration services. Interior and exterior painting, wallpaper installation, and color consultation. Quality guaranteed.',
            'Carpenter': 'Professional carpentry services for custom furniture, repairs, and installations. Attention to detail and quality craftsmanship.',
            'Gardener': 'Complete garden care and landscaping services. Lawn maintenance, plant care, and garden design. Transform your outdoor space.',
            'Moving': 'Reliable moving and transport services. Careful handling of your belongings. Local and long-distance moves. Affordable rates.',
            'Pet Care': 'Professional pet care services including grooming, walking, and sitting. Experienced with all breeds. Your pets are in safe hands.',
            'Tutor': 'Experienced tutor offering personalized lessons. All subjects and levels. Flexible scheduling and proven results.',
            'Chef': 'Professional chef and catering services. Custom menus for events and daily meal prep. Fresh ingredients and authentic flavors.',
            'More': 'Versatile service provider offering various professional services. Contact for custom requirements and special projects.'
        }
        return descriptions.get(category, f'Professional {category.lower()} services in Addis Ababa.')
