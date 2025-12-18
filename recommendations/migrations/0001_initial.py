# Generated manually for recommendations app

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('universities', '0001_initial'),  # Adjust this based on your universities app migration
    ]

    operations = [
        migrations.CreateModel(
            name='UserRecommendationProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('preferred_countries', models.JSONField(default=list, help_text='List of preferred country codes')),
                ('preferred_cities', models.JSONField(default=list, help_text='List of preferred cities')),
                ('preferred_programs', models.JSONField(default=list, help_text='List of preferred program/course names')),
                ('preferred_intake', models.CharField(blank=True, help_text='Preferred intake period', max_length=50)),
                ('application_fee_preference', models.CharField(blank=True, choices=[('no_fee', 'No Fee'), ('less_than_15', 'Less than $15'), ('less_than_30', 'Less than $30'), ('less_than_50', 'Less than $50'), ('50_or_more', '$50 or more')], help_text='Application fee preference', max_length=20)),
                ('completed_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='recommendation_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Recommendation Profile',
                'verbose_name_plural': 'User Recommendation Profiles',
            },
        ),
        migrations.CreateModel(
            name='RecommendationQuestionnaireResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('responses', models.JSONField(default=dict, help_text='Complete questionnaire responses')),
                ('completed', models.BooleanField(default=False)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='questionnaire_response', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Questionnaire Response',
                'verbose_name_plural': 'Questionnaire Responses',
            },
        ),
        migrations.CreateModel(
            name='RecommendedUniversity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('match_score', models.FloatField(default=0.0, help_text='Match score (0-100)')),
                ('recommendation_reason', models.TextField(blank=True, help_text='Why this university was recommended')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True, help_text='Whether this recommendation is still active')),
                ('university', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='universities.university')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recommended_universities', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Recommended University',
                'verbose_name_plural': 'Recommended Universities',
                'ordering': ['-match_score', '-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='recommendeduniversity',
            constraint=models.UniqueConstraint(fields=('user', 'university'), name='unique_user_university_recommendation'),
        ),
    ]