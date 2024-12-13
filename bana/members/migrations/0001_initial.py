# Generated by Django 5.1.3 on 2024-12-05 18:55

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Type',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('memb_type_name', models.CharField(max_length=50)),
                ('memb_type_desc', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Members',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('memb_date_joined', models.DateTimeField(auto_now_add=True)),
                ('memb_birth_date', models.DateField()),
                ('memb_gender', models.CharField(choices=[('M', 'Homme'), ('F', 'Femme'), ('X', 'Non Genré')], max_length=1)),
                ('memb_num_street', models.SmallIntegerField()),
                ('memb_box', models.CharField(max_length=50)),
                ('memb_street', models.CharField(max_length=50)),
                ('memb_zp', models.SmallIntegerField()),
                ('memb_locality', models.CharField(max_length=50)),
                ('memb_country', models.CharField(default='Belgique', max_length=50)),
                ('memb_car', models.BooleanField(default=False)),
                ('memb_user_fk', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='votre username')),
            ],
        ),
    ]
