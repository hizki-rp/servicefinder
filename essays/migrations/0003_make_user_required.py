# Generated migration for making user field required on Essay model

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def assign_orphan_essays(apps, schema_editor):
    """
    Assign essays without users to the first admin user, or delete them.
    This ensures the migration doesn't fail when making user required.
    """
    Essay = apps.get_model('essays', 'Essay')
    User = apps.get_model('auth', 'User')
    
    # Get orphan essays (essays without a user)
    orphan_essays = Essay.objects.filter(user__isnull=True)
    
    if orphan_essays.exists():
        # Try to find an admin user to assign them to
        admin_user = User.objects.filter(is_staff=True).first()
        
        if admin_user:
            # Assign orphan essays to admin
            orphan_essays.update(user=admin_user)
        else:
            # If no admin user, delete orphan essays
            orphan_essays.delete()


def reverse_migration(apps, schema_editor):
    """No-op for reverse migration"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('essays', '0002_essay_is_template_alter_essay_user'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # First, handle any essays without users
        migrations.RunPython(assign_orphan_essays, reverse_migration),
        
        # Then make the user field required
        migrations.AlterField(
            model_name='essay',
            name='user',
            field=models.ForeignKey(
                help_text='Owner of the essay',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='essays',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        
        # Change default for is_template to False
        migrations.AlterField(
            model_name='essay',
            name='is_template',
            field=models.BooleanField(default=False, help_text='Whether this is a template'),
        ),
        
        # Change ordering to show most recently edited first
        migrations.AlterModelOptions(
            name='essay',
            options={'ordering': ['-updated_at'], 'verbose_name': 'Essay', 'verbose_name_plural': 'Essays'},
        ),
    ]

