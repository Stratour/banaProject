# Generated by Django 5.1.4 on 2025-01-13 12:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trajects', '0003_proposedtraject_number_of_place_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='proposedtraject',
            name='number_of_place',
            field=models.SmallIntegerField(),
        ),
        migrations.AlterField(
            model_name='researchedtraject',
            name='number_of_place',
            field=models.SmallIntegerField(),
        ),
    ]
