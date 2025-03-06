# Generated by Django 5.1.4 on 2025-01-20 16:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trajects', '0009_proposedtraject_language_researchedtraject_language'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='proposedtraject',
            name='language',
        ),
        migrations.AlterField(
            model_name='proposedtraject',
            name='number_of_places',
            field=models.CharField(choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7')], max_length=1),
        ),
        migrations.RemoveField(
            model_name='researchedtraject',
            name='language',
        ),
        migrations.AddField(
            model_name='proposedtraject',
            name='language',
            field=models.ManyToManyField(blank=True, null=True, related_name='proposed_trajects', to='trajects.languages'),
        ),
        migrations.AddField(
            model_name='researchedtraject',
            name='language',
            field=models.ManyToManyField(blank=True, null=True, related_name='researched_trajects', to='trajects.languages'),
        ),
    ]
