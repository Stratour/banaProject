from django.db import migrations

def fill_proposed_researched(apps, schema_editor):
    Reservation = apps.get_model('trajects', 'Reservation')
    ProposedTraject = apps.get_model('trajects', 'ProposedTraject')
    ResearchedTraject = apps.get_model('trajects', 'ResearchedTraject')
    Traject = apps.get_model('trajects', 'Traject')

    for res in Reservation.objects.all():
        traject = res.traject

        # Cherche un ProposedTraject correspondant à ce Traject
        try:
            proposed = ProposedTraject.objects.get(traject=traject)
            res.proposed_traject = proposed
        except ProposedTraject.DoesNotExist:
            pass

        # Cherche un ResearchedTraject correspondant à ce Traject
        try:
            researched = ResearchedTraject.objects.get(traject=traject)
            res.researched_traject = researched
        except ResearchedTraject.DoesNotExist:
            pass

        res.save()

class Migration(migrations.Migration):

    dependencies = [
        ('trajects', '0004_alter_reservation_traject'),  # remplace par la migration précédente
    ]

    operations = [
        migrations.RunPython(fill_proposed_researched),
    ]
