# Generated migration — custom User + TravelPlan with adults/children

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False)),
                ('full_name', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('country', models.CharField(blank=True, max_length=2)),
                ('is_active', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now)),
                ('groups', models.ManyToManyField(
                    blank=True,
                    related_name='api_user_set',
                    to='auth.group',
                    verbose_name='groups',
                )),
                ('user_permissions', models.ManyToManyField(
                    blank=True,
                    related_name='api_user_set',
                    to='auth.permission',
                    verbose_name='user permissions',
                )),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TravelPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('budget_type', models.CharField(choices=[('luxury', 'Luxury'), ('economy', 'Economy'), ('cheap', 'Cheap')], max_length=20)),
                ('activities', models.JSONField(blank=True, default=list)),
                ('city', models.CharField(max_length=150)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('guests', models.PositiveIntegerField()),
                ('adults', models.PositiveIntegerField(default=1)),
                ('children', models.PositiveIntegerField(default=0)),
                ('itinerary_data', models.JSONField(blank=True, default=dict)),
                ('user', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='travel_plans',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
        ),
    ]
