# Generated by Django 5.1.4 on 2025-03-13 12:37

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trajects', '0004_reservation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reservation',
            name='traject',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='trajects.proposedtraject'),
        ),
    ]
