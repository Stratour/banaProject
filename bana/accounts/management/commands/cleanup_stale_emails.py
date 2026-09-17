from django.core.management.base import BaseCommand
from django.db.models import F

from allauth.account.models import EmailAddress


class Command(BaseCommand):
    help = (
        "Supprime les EmailAddress résiduelles laissées par un ancien changement d'adresse. "
        "allauth authentifie sur n'importe quelle EmailAddress correspondante, sans regarder "
        "primary ni verified : une ancienne adresse laissée en base permet toujours de se "
        "connecter. Affiche ce qui serait supprimé ; utiliser --apply pour supprimer."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Supprime réellement. Sans ce drapeau, la commande se contente de lister.",
        )
        parser.add_argument(
            "--include-pending",
            action="store_true",
            help=(
                "Supprime aussi les adresses non vérifiées, c'est-à-dire les demandes de "
                "changement encore en attente de confirmation. À éviter si un utilisateur "
                "est en train d'en confirmer une."
            ),
        )

    def handle(self, *args, **options):
        apply = options["apply"]
        include_pending = options["include_pending"]

        # Résiduelles = l'adresse ne correspond plus à celle du compte.
        stale = EmailAddress.objects.exclude(email=F("user__email")).select_related("user")
        if not include_pending:
            stale = stale.filter(verified=True)

        rows = list(stale.order_by("user__email", "email"))

        if not rows:
            self.stdout.write(self.style.SUCCESS("Aucune adresse résiduelle."))
            if not include_pending:
                pending = EmailAddress.objects.exclude(email=F("user__email")).filter(verified=False).count()
                if pending:
                    self.stdout.write(
                        f"({pending} demande(s) de changement en attente, conservée(s) — "
                        f"utiliser --include-pending pour les inclure.)"
                    )
            return

        self.stdout.write(f"{len(rows)} adresse(s) résiduelle(s) :\n")
        for e in rows:
            self.stdout.write(
                f"  {e.email:42} verified={str(e.verified):5} primary={str(e.primary):5}"
                f"  → compte {e.user.email}"
            )

        if not apply:
            self.stdout.write(
                self.style.WARNING(
                    "\nRien n'a été supprimé. Relancer avec --apply pour confirmer."
                )
            )
            return

        deleted, _ = EmailAddress.objects.filter(pk__in=[e.pk for e in rows]).delete()
        self.stdout.write(self.style.SUCCESS(f"\n{deleted} adresse(s) supprimée(s)."))
