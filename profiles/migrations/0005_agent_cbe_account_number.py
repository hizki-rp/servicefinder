# Generated migration for adding CBE account number to Agent model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0004_agent'),
    ]

    operations = [
        migrations.AddField(
            model_name='agent',
            name='cbe_account_number',
            field=models.CharField(blank=True, help_text='CBE bank account number for receiving referral payments', max_length=20, null=True),
        ),
    ]

