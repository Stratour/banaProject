from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def clear_site_visits(apps, schema_editor):
    """Les anciennes lignes (IP anonymisée, device) n'ont plus de sens avec le
    nouveau modèle 'dernière activité par membre connecté' : on repart de zéro
    plutôt que de tenter de les faire correspondre au nouveau schéma."""
    SiteVisit = apps.get_model('bana_admin', 'SiteVisit')
    SiteVisit.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('bana_admin', '0008_sitevisit_device_type'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(clear_site_visits, migrations.RunPython.noop),
        migrations.AlterUniqueTogether(
            name='sitevisit',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='sitevisit',
            name='ip_address',
        ),
        migrations.RemoveField(
            model_name='sitevisit',
            name='device_type',
        ),
        migrations.RemoveField(
            model_name='sitevisit',
            name='timestamp',
        ),
        migrations.AddField(
            model_name='sitevisit',
            name='last_seen',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='sitevisit',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='site_visit', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterModelOptions(
            name='sitevisit',
            options={'ordering': ['-last_seen']},
        ),
    ]
