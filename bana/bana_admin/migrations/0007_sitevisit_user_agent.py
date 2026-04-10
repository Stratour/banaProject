from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bana_admin', '0006_remove_activeuser_user_delete_dailystats_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitevisit',
            name='user_agent',
            field=models.CharField(blank=True, default='', max_length=512),
        ),
    ]
