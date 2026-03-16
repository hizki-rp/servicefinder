from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('providers', '0011_add_kyc_images'),
    ]

    operations = [
        migrations.CreateModel(
            name='ServiceCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('icon', models.CharField(default='briefcase', max_length=50)),
                ('order', models.IntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Service Category',
                'verbose_name_plural': 'Service Categories',
                'ordering': ['order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='ServiceSubCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('icon', models.CharField(default='tool', max_length=50)),
                ('category', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='subcategories',
                    to='providers.servicecategory',
                )),
            ],
            options={
                'verbose_name': 'Service Sub-Category',
                'verbose_name_plural': 'Service Sub-Categories',
                'ordering': ['category__order', 'name'],
                'unique_together': {('category', 'name')},
            },
        ),
        migrations.AddField(
            model_name='providerservice',
            name='subcategory',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='services',
                to='providers.servicesubcategory',
                help_text='Two-tier taxonomy sub-category',
            ),
        ),
    ]
