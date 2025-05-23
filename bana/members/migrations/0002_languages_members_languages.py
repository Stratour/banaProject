# Generated by Django 5.1.4 on 2025-03-28 10:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Languages',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.AddField(
            model_name='members',
            name='languages',
            field=models.ManyToManyField(blank=True, related_name='members', to='members.languages'),
        ),
    ]
