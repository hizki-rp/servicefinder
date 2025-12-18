from django.core.management.base import BaseCommand
from django.test import RequestFactory
from django.contrib.auth.models import User
from recommendations.views import questionnaire_options


class Command(BaseCommand):
    help = 'Test questionnaire options endpoint'

    def handle(self, *args, **options):
        # Create a test user
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={'email': 'test@example.com'}
        )
        
        # Create a mock request
        factory = RequestFactory()
        request = factory.get('/recommendations/questionnaire/options/')
        request.user = user
        
        # Call the view
        try:
            response = questionnaire_options(request)
            data = response.data
            
            self.stdout.write('Questionnaire Options Test Results:')
            self.stdout.write(f'Status Code: {response.status_code}')
            
            if response.status_code == 200:
                self.stdout.write(f'Countries: {len(data.get("countries", []))} available')
                if data.get("countries"):
                    self.stdout.write(f'  Sample countries: {data["countries"][:3]}')
                
                self.stdout.write(f'Cities: {len(data.get("cities", []))} available')
                if data.get("cities"):
                    self.stdout.write(f'  Sample cities: {data["cities"][:3]}')
                
                self.stdout.write(f'Programs: {len(data.get("programs", []))} available')
                if data.get("programs"):
                    self.stdout.write(f'  Sample programs: {data["programs"][:3]}')
                
                self.stdout.write(f'Intakes: {len(data.get("intakes", []))} available')
                for intake in data.get("intakes", []):
                    self.stdout.write(f'  - {intake}')
                
                self.stdout.write(f'Application Fees: {len(data.get("application_fees", []))} options')
                for fee in data.get("application_fees", []):
                    self.stdout.write(f'  - {fee.get("label", fee)} ({fee.get("value", fee)})')
                
                self.stdout.write(self.style.SUCCESS('✅ Questionnaire options loaded successfully!'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ Error: {data}'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Exception: {str(e)}'))
            import traceback
            traceback.print_exc()