"""
Seed test data for all categories and subcategories.
Creates 1 provider with 1 service for each subcategory.
Run: python manage.py seed_test_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from providers.models import (
    ServiceCategory, ServiceSubCategory, ProviderProfile, 
    ProviderService, ProviderVerification
)
import random

User = get_user_model()

# Ethiopian names for realistic test data
ETHIOPIAN_NAMES = [
    ('Abebe', 'Bekele'), ('Almaz', 'Tadesse'), ('Biruk', 'Haile'),
    ('Chaltu', 'Mekonnen'), ('Dawit', 'Tesfaye'), ('Eleni', 'Girma'),
    ('Fikadu', 'Kebede'), ('Genet', 'Alemu'), ('Habtamu', 'Desta'),
    ('Aster', 'Mulugeta'), ('Kidist', 'Assefa'), ('Lemlem', 'Wolde'),
    ('Mekdes', 'Abera'), ('Netsanet', 'Gebre'), ('Rahel', 'Yohannes'),
    ('Selam', 'Negash'), ('Tigist', 'Demissie'), ('Yared', 'Getachew'),
    ('Zewdu', 'Amare'), ('Bethlehem', 'Tekle'), ('Meseret', 'Ayele'),
    ('Tewodros', 'Mengistu'), ('Hanna', 'Worku'), ('Samson', 'Tilahun'),
    ('Marta', 'Berhanu'), ('Yonas', 'Fekadu'), ('Sara', 'Tadele'),
    ('Daniel', 'Sisay'), ('Ruth', 'Alemayehu'), ('Abel', 'Getahun'),
    ('Mahlet', 'Shiferaw'), ('Eyob', 'Mulatu'), ('Seble', 'Abate'),
    ('Henok', 'Legesse'), ('Meron', 'Tefera'), ('Kaleb', 'Admasu'),
    ('Liya', 'Wondimu'), ('Natnael', 'Gebreyesus'), ('Tsion', 'Hailu'),
    ('Yosef', 'Mesfin'), ('Eden', 'Bekele'), ('Robel', 'Tadesse'),
    ('Hiwot', 'Haile'), ('Biniam', 'Mekonnen'), ('Senait', 'Tesfaye'),
]

# Addis Ababa neighborhoods
NEIGHBORHOODS = [
    'Bole', 'Piassa', 'Merkato', 'Kazanchis', 'Megenagna',
    'CMC', '22 Mazoria', 'Gerji', 'Sarbet', 'Lideta',
    'Arada', 'Kirkos', 'Nifas Silk', 'Kolfe', 'Yeka',
    'Gulele', 'Addis Ketema', 'Akaki Kality', 'Lemi Kura', 'Summit',
]

# Phone number prefixes in Ethiopia
PHONE_PREFIXES = ['0911', '0912', '0913', '0914', '0915', '0921', '0922', '0923']

# Service descriptions templates
DESCRIPTION_TEMPLATES = {
    'default': [
        'Professional {service} with {years} years of experience in Addis Ababa. Quality work guaranteed.',
        'Experienced {service} offering reliable and affordable services. Available for both residential and commercial.',
        'Certified {service} providing top-quality service. Fast response time and competitive rates.',
        'Skilled {service} with excellent customer reviews. Serving Addis Ababa and surrounding areas.',
        'Expert {service} dedicated to customer satisfaction. Licensed and insured professional.',
    ]
}


class Command(BaseCommand):
    help = 'Seeds test data: 1 provider + 1 service per subcategory'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing test data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing test data...')
            ProviderService.objects.filter(provider__user__username__startswith='test_').delete()
            ProviderProfile.objects.filter(user__username__startswith='test_').delete()
            User.objects.filter(username__startswith='test_').delete()
            self.stdout.write(self.style.SUCCESS('✓ Cleared'))

        # First, ensure taxonomy is seeded
        self.stdout.write('Checking taxonomy...')
        categories = ServiceCategory.objects.all()
        if not categories.exists():
            self.stdout.write(self.style.WARNING('No categories found. Run: python manage.py seed_taxonomy'))
            return

        total_providers = 0
        total_services = 0
        used_names = set()

        for category in categories.order_by('order'):
            self.stdout.write(f'\n📁 {category.name}')
            
            subcategories = ServiceSubCategory.objects.filter(category=category)
            
            for subcategory in subcategories:
                # Get unique name
                first_name, last_name = self._get_unique_name(used_names)
                username = f"test_{first_name.lower()}_{last_name.lower()}_{random.randint(100, 999)}"
                
                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=f"{username}@test.com",
                    password='test123456',
                    first_name=first_name,
                    last_name=last_name,
                )
                
                # Create provider profile
                phone = f"{random.choice(PHONE_PREFIXES)}{random.randint(100000, 999999)}"
                neighborhood = random.choice(NEIGHBORHOODS)
                
                provider = ProviderProfile.objects.create(
                    user=user,
                    phone_number=phone,
                    city='Addis Ababa',
                    is_verified=True,  # Auto-verify test data
                    national_id_verified=True,
                    payment_verified=True,
                    latitude=9.0 + random.uniform(-0.1, 0.1),  # Around Addis Ababa
                    longitude=38.7 + random.uniform(-0.1, 0.1),
                )
                total_providers += 1
                
                # Create verification records (auto-approved)
                ProviderVerification.objects.create(
                    user=user,
                    verification_type='selfie',
                    status='approved',
                    reviewed_at=timezone.now(),
                )
                ProviderVerification.objects.create(
                    user=user,
                    verification_type='national_id',
                    status='approved',
                    reviewed_at=timezone.now(),
                )
                
                # Create service
                years = random.randint(2, 15)
                price = self._generate_price(subcategory.name)
                description = random.choice(DESCRIPTION_TEMPLATES['default']).format(
                    service=subcategory.name,
                    years=years
                )
                
                service = ProviderService.objects.create(
                    provider=user,
                    subcategory=subcategory,
                    service_category=subcategory.name,  # Legacy field
                    name=f"{subcategory.name} - {neighborhood}",
                    description=description,
                    price_type='hourly',
                    hourly_rate=price,
                    is_active=True,
                    latitude=provider.latitude,
                    longitude=provider.longitude,
                    city='Addis Ababa',
                )
                total_services += 1
                
                self.stdout.write(
                    f'  ✓ {first_name} {last_name} - {subcategory.name} '
                    f'({price} ETB/hr, {years}y exp)'
                )

        self.stdout.write(self.style.SUCCESS(
            f'\n🎉 Done! Created {total_providers} providers and {total_services} services.'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'All test accounts use password: test123456'
        ))

    def _get_unique_name(self, used_names):
        """Get a unique name combination."""
        while True:
            first_name, last_name = random.choice(ETHIOPIAN_NAMES)
            name_combo = f"{first_name}_{last_name}"
            if name_combo not in used_names:
                used_names.add(name_combo)
                return first_name, last_name

    def _generate_price(self, service_name):
        """Generate realistic price based on service type."""
        service_lower = service_name.lower()
        
        # High-skill services
        if any(word in service_lower for word in ['developer', 'designer', 'photographer', 'videographer']):
            return random.randint(500, 1500)
        
        # Medium-skill services
        elif any(word in service_lower for word in ['electrician', 'plumber', 'carpenter', 'mechanic', 'trainer']):
            return random.randint(200, 600)
        
        # Standard services
        elif any(word in service_lower for word in ['cleaner', 'driver', 'cook', 'tutor', 'teacher']):
            return random.randint(100, 300)
        
        # Basic services
        else:
            return random.randint(80, 250)
