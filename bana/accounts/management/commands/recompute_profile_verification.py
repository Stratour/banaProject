from django.core.management.base import BaseCommand
from accounts.models import Profile


class Command(BaseCommand):
    help = "Recalcule prfl_is_verified pour tous les profils (profil complet + CI vérifiée + BVM vérifié)"

    def handle(self, *args, **kwargs):
        changed = 0
        for profile in Profile.objects.all():
            before = profile.prfl_is_verified
            profile.update_profile_verified()
            if profile.prfl_is_verified != before:
                changed += 1

        self.stdout.write(self.style.SUCCESS(f"{changed} profils mis à jour"))
