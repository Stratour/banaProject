# Generated by Django 5.1.4 on 2025-01-20 16:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trajects', '0010_remove_proposedtraject_language_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='proposedtraject',
            name='language',
            field=models.ManyToManyField(blank=True, related_name='proposed_trajects', to='trajects.languages'),
        ),
        migrations.AlterField(
            model_name='traject',
            name='end_country',
            field=models.CharField(blank=True, default='Belgium', max_length=100),
        ),
    ]
