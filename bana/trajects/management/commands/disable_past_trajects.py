from django.core.management.base import BaseCommand
from django.utils import timezone
from trajects.models import ProposedTraject, ResearchedTraject

class Command(BaseCommand):
    help = "Désactive les trajets dont la date est passée"

    def handle(self, *args, **kwargs):
        today = timezone.now().date()

        proposed = ProposedTraject.objects.filter(date__lt=today, is_active=True)
        researched = ResearchedTraject.objects.filter(date__lt=today, is_active=True)

        p_count = proposed.update(is_active=False)
        r_count = researched.update(is_active=False)

        self.stdout.write(self.style.SUCCESS(f"{p_count} trajets proposés désactivés"))
        self.stdout.write(self.style.SUCCESS(f"{r_count} trajets recherchés désactivés"))
