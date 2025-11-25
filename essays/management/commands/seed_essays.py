from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from essays.models import Essay
from datetime import datetime


class Command(BaseCommand):
    help = 'Seed initial essays data'

    def handle(self, *args, **options):
        # Get or create users for the essays
        users_data = [
            {'username': 'rakibul', 'email': 'rakibul@example.com', 'first_name': 'Rakibul', 'last_name': 'Islam'},
            {'username': 'miki', 'email': 'miki@example.com', 'first_name': 'Miki', 'last_name': 'Dench'},
            {'username': 'randall', 'email': 'randall@example.com', 'first_name': 'Randall', 'last_name': 'Koffi'},
            {'username': 'seun', 'email': 'seun@example.com', 'first_name': 'Seun', 'last_name': 'Abdul'},
            {'username': 'zeynep', 'email': 'zeynep@example.com', 'first_name': 'Zeynep', 'last_name': 'Akkoyun'},
        ]

        users = []
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                }
            )
            users.append(user)
            if created:
                user.set_password('password123')  # Set a default password
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created user: {user.username}'))

        # Sample essays data
        essays_data = [
            {
                'title': 'Essay 1',
                'description': 'Essay 1 Description',
                'user': users[0],
                'content': {
                    'json': {
                        'type': 'doc',
                        'content': [
                            {
                                'type': 'paragraph',
                                'content': [
                                    {
                                        'type': 'text',
                                        'text': 'This is Essay 1 content. It contains important information about scholarship applications.'
                                    }
                                ]
                            }
                        ]
                    },
                    'html': '<p>This is Essay 1 content. It contains important information about scholarship applications.</p>',
                    'text': 'This is Essay 1 content. It contains important information about scholarship applications.'
                }
            },
            {
                'title': 'Essay 2',
                'description': 'Essay 2 Description',
                'user': users[1],
                'content': {
                    'json': {
                        'type': 'doc',
                        'content': [
                            {
                                'type': 'paragraph',
                                'content': [
                                    {
                                        'type': 'text',
                                        'text': 'This is Essay 2 content. It discusses various scholarship opportunities and application strategies.'
                                    }
                                ]
                            }
                        ]
                    },
                    'html': '<p>This is Essay 2 content. It discusses various scholarship opportunities and application strategies.</p>',
                    'text': 'This is Essay 2 content. It discusses various scholarship opportunities and application strategies.'
                }
            },
            {
                'title': 'Essay 3',
                'description': 'Essay 3 Description',
                'user': users[2],
                'content': {
                    'json': {
                        'type': 'doc',
                        'content': [
                            {
                                'type': 'paragraph',
                                'content': [
                                    {
                                        'type': 'text',
                                        'text': 'This is Essay 3 content. It focuses on personal statements and motivation letters.'
                                    }
                                ]
                            }
                        ]
                    },
                    'html': '<p>This is Essay 3 content. It focuses on personal statements and motivation letters.</p>',
                    'text': 'This is Essay 3 content. It focuses on personal statements and motivation letters.'
                }
            },
            {
                'title': 'Essay 4',
                'description': 'Essay 4 Description',
                'user': users[3],
                'content': {
                    'json': {
                        'type': 'doc',
                        'content': [
                            {
                                'type': 'paragraph',
                                'content': [
                                    {
                                        'type': 'text',
                                        'text': 'This is Essay 4 content. It covers tips for writing effective scholarship essays.'
                                    }
                                ]
                            }
                        ]
                    },
                    'html': '<p>This is Essay 4 content. It covers tips for writing effective scholarship essays.</p>',
                    'text': 'This is Essay 4 content. It covers tips for writing effective scholarship essays.'
                }
            },
            {
                'title': 'Essay 5',
                'description': 'Essay 5 Description',
                'user': users[4],
                'content': {
                    'json': {
                        'type': 'doc',
                        'content': [
                            {
                                'type': 'paragraph',
                                'content': [
                                    {
                                        'type': 'text',
                                        'text': 'This is Essay 5 content. It provides guidance on scholarship application processes.'
                                    }
                                ]
                            }
                        ]
                    },
                    'html': '<p>This is Essay 5 content. It provides guidance on scholarship application processes.</p>',
                    'text': 'This is Essay 5 content. It provides guidance on scholarship application processes.'
                }
            },
        ]

        # Create essays as shared templates (user is optional)
        created_count = 0
        for essay_data in essays_data:
            essay, created = Essay.objects.get_or_create(
                title=essay_data['title'],
                defaults={
                    'description': essay_data['description'],
                    'content': essay_data['content'],
                    'user': essay_data.get('user'),  # Optional user
                    'is_template': True,  # Mark as shared template
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created essay template: {essay.title}'))
            else:
                # Update existing essay to be a template
                essay.is_template = True
                essay.save()
                self.stdout.write(self.style.WARNING(f'Essay already exists, updated as template: {essay.title}'))

        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created {created_count} essays.'))

