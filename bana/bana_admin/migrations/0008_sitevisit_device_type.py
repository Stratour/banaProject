from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bana_admin', '0007_sitevisit_user_agent'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sitevisit',
            name='user_agent',
        ),
        migrations.AddField(
            model_name='sitevisit',
            name='device_type',
            field=models.CharField(
                choices=[
                    ('mobile', 'Mobile'),
                    ('tablet', 'Tablette'),
                    ('desktop', 'Desktop'),
                    ('unknown', 'Inconnu'),
                ],
                default='unknown',
                max_length=10,
            ),
        ),
    ]
