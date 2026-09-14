import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import Ecole

DEFAULT_PATH = Path(settings.BASE_DIR).parent / "docs" / (
    "fwb-age-fichier-signaletique-des-etablissements-d-enseignement-de-la-federation-.json"
)


class Command(BaseCommand):
    help = (
        "Importe/actualise la liste des écoles FWB depuis l'export JSON ODWB "
        "(dataset 'fwb-age-fichier-signaletique-des-etablissements-d-enseignement-de-la-federation-'). "
        "À relancer chaque rentrée scolaire avec un export à jour téléchargé sur odwb.be."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "json_path",
            nargs="?",
            default=str(DEFAULT_PATH),
            help="Chemin vers le fichier JSON exporté depuis odwb.be (par défaut: docs/fwb-age-....json)",
        )

    def handle(self, *args, **options):
        path = Path(options["json_path"])
        if not path.exists():
            raise CommandError(f"Fichier introuvable : {path}")

        with path.open(encoding="utf-8") as f:
            rows = json.load(f)

        # Le fichier contient une ligne par (établissement, implantation, type d'enseignement) :
        # on déduplique sur (établissement, implantation), une seule adresse physique par école.
        by_key = {}
        for row in rows:
            fase_etab = row.get("ndeg_fase_de_l_etablissement")
            fase_impl = row.get("ndeg_fase_de_l_implantation")
            if fase_etab is None or fase_impl is None:
                continue
            by_key[(int(fase_etab), int(fase_impl))] = row

        created = updated = 0
        seen_ids = []

        with transaction.atomic():
            for (fase_etab, fase_impl), row in by_key.items():
                obj, was_created = Ecole.objects.update_or_create(
                    fase_etablissement=fase_etab,
                    fase_implantation=fase_impl,
                    defaults={
                        "numero_bce": row.get("numero_bce_de_l_etablissement") or "",
                        "nom": row.get("nom_d_etablissement") or "",
                        "niveau": row.get("niveau") or "",
                        "reseau": row.get("reseau") or "",
                        "adresse": row.get("adresse_de_l_implantation") or "",
                        "code_postal": row.get("code_postal_de_l_implantation") or "",
                        "commune": row.get("commune_de_l_implantation") or "",
                    },
                )
                seen_ids.append(obj.pk)
                created += int(was_created)
                updated += int(not was_created)

            deleted, _ = Ecole.objects.exclude(pk__in=seen_ids).delete()

        self.stdout.write(self.style.SUCCESS(
            f"{created} écoles créées, {updated} mises à jour, {deleted} supprimées (absentes du nouvel export)."
        ))
