#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_api.settings')
django.setup()

from content_creator.models import ApplicationSettings

# Create initial settings
settings, created = ApplicationSettings.objects.get_or_create(
    defaults={
        'is_open': True,
        'creator_revenue_percentage': 35.00
    }
)

if created:
    print("ApplicationSettings created successfully!")
else:
    print("ApplicationSettings already exists.")
    
print(f"Applications open: {settings.is_open}")
print(f"Creator revenue percentage: {settings.creator_revenue_percentage}%")