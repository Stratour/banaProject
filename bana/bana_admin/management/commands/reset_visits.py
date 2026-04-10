from django.core.management.base import BaseCommand
from bana_admin.models import SiteVisit


class Command(BaseCommand):
    help = "Supprime tous les enregistrements de visites (SiteVisit)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirme la suppression sans prompt interactif.',
        )

    def handle(self, *args, **options):
        count = SiteVisit.objects.count()

        if count == 0:
            self.stdout.write(self.style.WARNING("Aucune visite à supprimer."))
            return

        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(f"{count} enregistrement(s) seront supprimés.")
            )
            confirm = input("Confirmer ? (oui/non) : ").strip().lower()
            if confirm not in ("oui", "o"):
                self.stdout.write("Annulé.")
                return

        SiteVisit.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"{count} visite(s) supprimée(s)."))
