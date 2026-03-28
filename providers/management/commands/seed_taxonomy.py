"""
Seed the two-tier service taxonomy.
Run: python manage.py seed_taxonomy
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from providers.models import ServiceCategory, ServiceSubCategory

TAXONOMY = [
    {
        'name': 'Home Services',
        'icon': 'home',
        'order': 1,
        'subs': [
            ('Cleaner / Housekeeper', 'spray-can'),
            ('Babysitter / Nanny', 'baby'),
            ('Cook / Personal Chef', 'chef-hat'),
            ('Laundry / Ironing', 'shirt'),
            ('Elderly Caregiver', 'heart-handshake'),
        ],
    },
    {
        'name': 'Repair & Maintenance',
        'icon': 'wrench',
        'order': 2,
        'subs': [
            ('Electrician', 'zap'),
            ('Plumber', 'droplets'),
            ('Carpenter', 'hammer'),
            ('AC & Refrigerator Repair', 'wind'),
            ('Appliance / TV Repair', 'tv'),
            ('Handyman', 'tool'),
        ],
    },
    {
        'name': 'Construction & Industrial',
        'icon': 'hard-hat',
        'order': 3,
        'subs': [
            ('Mason / Plaster Worker', 'brick-wall'),
            ('Welder', 'flame'),
            ('Painter', 'paint-roller'),
            ('Tile / Roof Installer', 'layers'),
            ('Interior Finisher', 'layout'),
        ],
    },
    {
        'name': 'Tech & Digital',
        'icon': 'monitor',
        'order': 4,
        'subs': [
            ('App / Web Developer', 'code'),
            ('Graphic Designer', 'pen-tool'),
            ('Photographer / Videographer', 'camera'),
            ('Social Media Manager', 'share-2'),
            ('Computer Trainer', 'laptop'),
        ],
    },
    {
        'name': 'Beauty & Personal Care',
        'icon': 'sparkles',
        'order': 5,
        'subs': [
            ('Hairdresser / Barber', 'scissors'),
            ('Makeup Artist', 'palette'),
            ('Nail Technician', 'hand'),
            ('Skincare Specialist', 'sun'),
            ('Massage Therapist', 'activity'),
            ('Fitness Trainer', 'dumbbell'),
        ],
    },
    {
        'name': 'Clothing & Fashion',
        'icon': 'shirt',
        'order': 6,
        'subs': [
            ('Tailor', 'scissors'),
            ('Fashion Designer', 'star'),
            ('Shoe Repair', 'footprints'),
            ('Bag Maker', 'shopping-bag'),
            ('Clothes Ironer', 'wind'),
        ],
    },
    {
        'name': 'Transport & Delivery',
        'icon': 'truck',
        'order': 7,
        'subs': [
            ('Driver (Personal/Taxi/Truck)', 'car'),
            ('Car Mechanic', 'settings'),
            ('Car Wash Worker', 'droplets'),
            ('Tire Repair Technician', 'circle'),
            ('Package / Food Delivery', 'package'),
        ],
    },
    {
        'name': 'Education & Events',
        'icon': 'graduation-cap',
        'order': 8,
        'subs': [
            ('Tutor / Language Teacher', 'book-open'),
            ('Music Teacher', 'music'),
            ('Event Planner / Decorator', 'calendar'),
            ('Caterer / DJ', 'utensils'),
            ('Fitness Trainer / Coach', 'dumbbell'),
        ],
    },
]


class Command(BaseCommand):
    help = 'Seeds the two-tier service taxonomy (idempotent)'

    def handle(self, *args, **options):
        total_cats = 0
        total_subs = 0

        for cat_data in TAXONOMY:
            cat, created = ServiceCategory.objects.update_or_create(
                name=cat_data['name'],
                defaults={
                    'slug': slugify(cat_data['name']),
                    'icon': cat_data['icon'],
                    'order': cat_data['order'],
                }
            )
            if created:
                total_cats += 1
            self.stdout.write(f'  {"✓ Created" if created else "↻ Updated"} category: {cat.name}')

            for sub_name, sub_icon in cat_data['subs']:
                slug = f"{slugify(cat_data['name'])}-{slugify(sub_name)}"[:100]

                sub, sub_created = ServiceSubCategory.objects.update_or_create(
                    category=cat,
                    name=sub_name,
                    defaults={'slug': slug, 'icon': sub_icon}
                )
                if sub_created:
                    total_subs += 1
                    self.stdout.write(f'    + {sub_name}')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! {total_cats} new categories, {total_subs} new sub-categories.'
        ))
