import logging
from datetime import timedelta
from django.utils import timezone
from .models import SiteVisit

logger = logging.getLogger(__name__)

EXCLUDED_PREFIXES = ('/static/', '/media/', '/__reload__/')

THROTTLE_MINUTES = 5


class SiteVisitMiddleware:
    """
    Met à jour la dernière activité connue d'un membre connecté (SiteVisit.last_seen).
    Sert uniquement au KPI "membres actifs" de l'admin — le trafic anonyme/global
    est suivi via un outil externe (Google Analytics, Plausible…), pas ici.
    - Ne suit que les utilisateurs authentifiés (aucune écriture pour les visiteurs anonymes).
    - Throttle à 5 min pour éviter une écriture DB à chaque requête.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated and not any(request.path.startswith(p) for p in EXCLUDED_PREFIXES):
            try:
                visit, created = SiteVisit.objects.get_or_create(user=request.user)
                if not created:
                    cutoff = timezone.now() - timedelta(minutes=THROTTLE_MINUTES)
                    if visit.last_seen < cutoff:
                        visit.save(update_fields=['last_seen'])
            except Exception:
                logger.exception("Échec de la mise à jour de SiteVisit pour %s", request.user)

        return response
