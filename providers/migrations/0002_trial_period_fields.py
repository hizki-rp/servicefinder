# Generated migration for trial period fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('providers', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='providerprofile',
            name='subscription_status',
            field=models.CharField(
                choices=[('trial', 'Trial (1 Month Free)'), ('active', 'Active'), ('expired', 'Expired')],
                default='trial',
                max_length=10
            ),
        ),
        migrations.AddField(
            model_name='providerprofile',
            name='trial_start_date',
            field=models.DateTimeField(
                blank=True,
                help_text='When the 1-month free trial started',
                null=True
            ),
        ),
        migrations.AddField(
            model_name='providerprofile',
            name='trial_expiry_date',
            field=models.DateTimeField(
                blank=True,
                help_text='When the 1-month free trial expires',
                null=True
            ),
        ),
        migrations.AddField(
            model_name='providerprofile',
            name='trial_notification_sent',
            field=models.BooleanField(
                default=False,
                help_text='Whether expiry notification has been sent'
            ),
        ),
        migrations.AddIndex(
            model_name='providerprofile',
            index=models.Index(fields=['subscription_status'], name='providers_p_subscri_idx'),
        ),
        migrations.AddIndex(
            model_name='providerprofile',
            index=models.Index(fields=['trial_expiry_date'], name='providers_p_trial_e_idx'),
        ),
    ]
