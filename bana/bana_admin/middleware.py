from django.core.cache import cache
from django.utils import timezone

class SiteVisitMiddleware:
    """
    - Compte les visites anonymes (par jour, semaine, mois)
    - Met à jour la dernière visite des utilisateurs connectés
    - Compte le nombre de visites utilisateurs sur /profile
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        now = timezone.now()

        if not request.user.is_authenticated:
            # Visiteur anonyme
            day_key = f"anonymous_visits:{now.date()}"
            week_key = f"anonymous_visits_week:{now.isocalendar().week}"
            month_key = f"anonymous_visits_month:{now.year}-{now.month}"

            for key in [day_key, week_key, month_key]:
                cache.set(key, cache.get(key, 0) + 1)
        else:
            # Utilisateur connecté
            # Mise à jour de la dernière visite en cache
            cache.set(f"user_last_seen:{request.user.id}", now, timeout=60 * 60 * 24 * 7)  # 7j

            if request.path.startswith("/accounts/profile"):
                cache.set("user_profile_visits", cache.get("user_profile_visits", 0) + 1)

        return response
