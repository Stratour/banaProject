# Generated by Django 5.1.4 on 2025-03-10 14:30

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trajects', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='proposedtraject',
            name='date',
            field=models.DateField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='researchedtraject',
            name='date',
            field=models.DateField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
