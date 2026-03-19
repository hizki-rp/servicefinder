"""
One-time data normalization: maps existing free-text service_category values
to the new ServiceSubCategory FK on ProviderService.

Run: python manage.py normalize_categories
"""
from django.core.management.base import BaseCommand
from providers.models import ProviderService, ServiceSubCategory


# Map common free-text values → subcategory name (case-insensitive partial match)
CATEGORY_MAP = {
    'cleaner': 'Cleaner / Housekeeper',
    'housekeeper': 'Cleaner / Housekeeper',
    'babysitter': 'Babysitter / Nanny',
    'nanny': 'Babysitter / Nanny',
    'cook': 'Cook / Personal Chef',
    'chef': 'Cook / Personal Chef',
    'laundry': 'Laundry / Ironing',
    'ironing': 'Laundry / Ironing',
    'caregiver': 'Elderly Caregiver',
    'electrician': 'Electrician',
    'plumber': 'Plumber',
    'plumbing': 'Plumber',
    'carpenter': 'Carpenter',
    'carpentry': 'Carpenter',
    'ac repair': 'AC & Refrigerator Repair',
    'refrigerator': 'AC & Refrigerator Repair',
    'appliance': 'Appliance / TV Repair',
    'tv repair': 'Appliance / TV Repair',
    'handyman': 'Handyman',
    'mason': 'Mason / Plaster Worker',
    'plaster': 'Mason / Plaster Worker',
    'welder': 'Welder',
    'welding': 'Welder',
    'painter': 'Painter',
    'painting': 'Painter',
    'tile': 'Tile / Roof Installer',
    'roof': 'Tile / Roof Installer',
    'interior': 'Interior Finisher',
    'developer': 'App / Web Developer',
    'web dev': 'App / Web Developer',
    'graphic': 'Graphic Designer',
    'designer': 'Graphic Designer',
    'photographer': 'Photographer / Videographer',
    'videographer': 'Photographer / Videographer',
    'social media': 'Social Media Manager',
    'computer': 'Computer Trainer',
    'hairdresser': 'Hairdresser / Barber',
    'barber': 'Hairdresser / Barber',
    'makeup': 'Makeup Artist',
    'nail': 'Nail Technician',
    'skincare': 'Skincare Specialist',
    'massage': 'Massage Therapist',
    'fitness': 'Fitness Trainer',
    'trainer': 'Fitness Trainer',
    'tailor': 'Tailor',
    'fashion': 'Fashion Designer',
    'shoe repair': 'Shoe Repair',
    'bag maker': 'Bag Maker',
    'driver': 'Driver (Personal/Taxi/Truck)',
    'taxi': 'Driver (Personal/Taxi/Truck)',
    'mechanic': 'Car Mechanic',
    'car wash': 'Car Wash Worker',
    'tire': 'Tire Repair Technician',
    'delivery': 'Package / Food Delivery',
    'tutor': 'Tutor / Language Teacher',
    'teacher': 'Tutor / Language Teacher',
    'music': 'Music Teacher',
    'event': 'Event Planner / Decorator',
    'caterer': 'Caterer / DJ',
    'dj': 'Caterer / DJ',
}


class Command(BaseCommand):
    help = 'Normalizes free-text service_category to SubCategory FK'

    def handle(self, *args, **options):
        # Build lookup: subcategory name (lower) → SubCategory object
        sub_lookup = {s.name.lower(): s for s in ServiceSubCategory.objects.all()}

        services = ProviderService.objects.filter(subcategory__isnull=True)
        total = services.count()
        matched = 0
        skipped = 0

        self.stdout.write(f'Processing {total} services without subcategory...\n')

        for service in services:
            raw = (service.service_category or '').lower().strip()
            target_name = None

            # Direct lookup first
            if raw in sub_lookup:
                target_name = raw
            else:
                # Partial match via CATEGORY_MAP
                for keyword, sub_name in CATEGORY_MAP.items():
                    if keyword in raw:
                        target_name = sub_name.lower()
                        break

            if target_name and target_name in sub_lookup:
                service.subcategory = sub_lookup[target_name]
                service.save(update_fields=['subcategory'])
                matched += 1
                self.stdout.write(f'  ✓ "{service.service_category}" → {sub_lookup[target_name].name}')
            else:
                skipped += 1
                self.stdout.write(self.style.WARNING(f'  ? No match for: "{service.service_category}"'))

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Matched: {matched}, Skipped: {skipped} / {total} total.'
        ))
