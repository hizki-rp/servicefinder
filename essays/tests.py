from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from .models import Essay


class EssayTemplatePreventionTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_user_essay_never_template_on_create(self):
        """Test that user essays are never marked as templates when created"""
        data = {
            'title': 'My Test Essay',
            'description': 'Test description',
            'content': {'text': 'Test content'}
        }
        
        response = self.client.post('/essays/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        essay = Essay.objects.get(id=response.data['id'])
        self.assertFalse(essay.is_template)
        self.assertEqual(essay.user, self.user)

    def test_user_essay_never_template_on_update(self):
        """Test that user essays remain non-templates when updated"""
        essay = Essay.objects.create(
            title='Original Title',
            user=self.user,
            is_template=False
        )
        
        data = {
            'title': 'Updated Title',
            'description': 'Updated description',
            'content': {'text': 'Updated content'}
        }
        
        response = self.client.put(f'/essays/{essay.id}/update/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        essay.refresh_from_db()
        self.assertFalse(essay.is_template)

    def test_model_save_prevents_template(self):
        """Test that model save method prevents user essays from being templates"""
        essay = Essay(
            title='Test Essay',
            user=self.user,
            is_template=True  # Try to force it to be a template
        )
        essay.save()
        
        # Should be automatically set to False
        self.assertFalse(essay.is_template)

    def test_templates_not_in_user_list(self):
        """Test that template essays don't appear in user's essay list"""
        # Create a user essay
        user_essay = Essay.objects.create(
            title='User Essay',
            user=self.user,
            is_template=False
        )
        
        # Create a template essay (simulating seeded data)
        template_user = User.objects.create_user(username='rakibul')
        template_essay = Essay.objects.create(
            title='Template Essay',
            user=template_user,
            is_template=True
        )
        
        response = self.client.get('/essays/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only see the user essay, not the template
        essay_ids = [essay['id'] for essay in response.data]
        self.assertIn(user_essay.id, essay_ids)
        self.assertNotIn(template_essay.id, essay_ids)
        self.assertEqual(len(response.data), 1)