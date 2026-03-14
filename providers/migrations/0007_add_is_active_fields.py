# Generated migration for adding is_active fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('providers', '0003_otp_and_user_profile'),
    ]

    operations = [
        migrations.AddField(
            model_name='providerprofile',
            name='is_active',
            field=models.BooleanField(default=True, help_text='Provider account is active (not suspended)'),
        ),
        migrations.AddField(
            model_name='providerprofile',
            name='suspended_at',
            field=models.DateTimeField(blank=True, null=True, help_text='When the provider was suspended'),
        ),
        migrations.AddField(
            model_name='providerprofile',
            name='suspension_reason',
            field=models.TextField(blank=True, help_text='Reason for suspension'),
        ),
        migrations.AddField(
            model_name='providerservice',
            name='is_active',
            field=models.BooleanField(default=True, help_text='Service is active and visible'),
        ),
        migrations.AddField(
            model_name='providerservice',
            name='hidden_at',
            field=models.DateTimeField(blank=True, null=True, help_text='When the service was hidden by admin'),
        ),
        migrations.AddField(
            model_name='providerservice',
            name='hidden_reason',
            field=models.TextField(blank=True, help_text='Reason for hiding service'),
        ),
    ]
