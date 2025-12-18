from django.core.management.base import BaseCommand
from universities.models import University
from django.db.models import Q, Min, Max, Count
from django.db import models


class Command(BaseCommand):
    help = 'Check university data for recommendations'

    def handle(self, *args, **options):
        total_universities = University.objects.count()
        self.stdout.write(f'Total universities: {total_universities}')
        
        # Check countries
        countries = University.objects.exclude(
            Q(country__isnull=True) | Q(country__exact='')
        ).values_list('country', flat=True).distinct()
        self.stdout.write(f'Countries available: {len(countries)}')
        for country in sorted(countries)[:10]:  # Show first 10
            count = University.objects.filter(country=country).count()
            self.stdout.write(f'  - {country}: {count} universities')
        if len(countries) > 10:
            self.stdout.write(f'  ... and {len(countries) - 10} more countries')
        
        # Check cities
        cities = University.objects.exclude(
            Q(city__isnull=True) | Q(city__exact='')
        ).values_list('city', flat=True).distinct()
        self.stdout.write(f'\nCities available: {len(cities)}')
        
        # Check programs
        programs_set = set()
        universities_with_programs = University.objects.exclude(
            Q(programs__isnull=True) | Q(programs__exact=[])
        ).values_list('programs', flat=True)
        
        for program_list in universities_with_programs:
            if program_list and isinstance(program_list, list):
                for program in program_list:
                    if program and program.strip():
                        programs_set.add(program.strip())
        
        self.stdout.write(f'Programs available: {len(programs_set)}')
        for program in sorted(list(programs_set))[:10]:  # Show first 10
            self.stdout.write(f'  - {program}')
        if len(programs_set) > 10:
            self.stdout.write(f'  ... and {len(programs_set) - 10} more programs')
        
        # Check application fees
        fee_stats = University.objects.exclude(
            application_fee__isnull=True
        ).aggregate(
            min_fee=Min('application_fee'),
            max_fee=Max('application_fee'),
            count=Count('application_fee')
        )
        
        self.stdout.write(f'\nApplication fees:')
        self.stdout.write(f'  Universities with fee data: {fee_stats["count"]}')
        if fee_stats['min_fee'] is not None:
            self.stdout.write(f'  Fee range: ${fee_stats["min_fee"]} - ${fee_stats["max_fee"]}')
        
        # Check data quality
        self.stdout.write(f'\nData Quality Check:')
        no_country = University.objects.filter(Q(country__isnull=True) | Q(country__exact='')).count()
        no_city = University.objects.filter(Q(city__isnull=True) | Q(city__exact='')).count()
        no_programs = University.objects.filter(Q(programs__isnull=True) | Q(programs__exact=[])).count()
        
        self.stdout.write(f'  Universities missing country: {no_country}')
        self.stdout.write(f'  Universities missing city: {no_city}')
        self.stdout.write(f'  Universities missing programs: {no_programs}')
        
        if no_country > 0 or no_city > 0 or no_programs > 0:
            self.stdout.write(self.style.WARNING('\nRecommendation: Update university data to improve recommendation quality'))
        else:
            self.stdout.write(self.style.SUCCESS('\nAll universities have complete data for recommendations!'))