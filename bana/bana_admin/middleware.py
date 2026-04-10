from .models import SiteVisit

EXCLUDED_PREFIXES = ('/static/', '/media/', '/__reload__/')

BOT_SIGNATURES = (
    'bot', 'crawler', 'spider', 'crawl', 'slurp',
    'python-requests', 'python-urllib', 'curl/', 'wget/',
    'scrapy', 'httpx', 'aiohttp', 'go-http-client',
    'facebookexternalhit', 'twitterbot', 'linkedinbot',
    'whatsapp', 'telegrambot', 'discordbot',
    'uptimerobot', 'pingdom', 'statuscake',
    'semrushbot', 'ahrefsbot', 'mj12bot', 'dotbot',
    'petalbot', 'yandexbot', 'baiduspider',
)


def _is_bot(user_agent: str) -> bool:
    ua = user_agent.lower()
    return any(sig in ua for sig in BOT_SIGNATURES)


class SiteVisitMiddleware:
    """
    Enregistre la dernière visite par IP+utilisateur dans SiteVisit.
    Filtre les bots connus. Persistant, partagé entre tous les workers.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if any(request.path.startswith(p) for p in EXCLUDED_PREFIXES):
            return response

        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if _is_bot(user_agent):
            return response

        ip = self._get_client_ip(request)

        try:
            if request.user.is_authenticated:
                # Un seul enregistrement par user — on supprime les anciennes IPs
                SiteVisit.objects.filter(user=request.user).exclude(ip_address=ip).delete()
                SiteVisit.objects.update_or_create(
                    ip_address=ip,
                    user=request.user,
                    defaults={'user_agent': user_agent[:512]},
                )
            else:
                # Anonyme : une ligne par IP
                SiteVisit.objects.update_or_create(
                    ip_address=ip,
                    user=None,
                    defaults={'user_agent': user_agent[:512]},
                )
        except Exception:
            pass

        return response

    @staticmethod
    def _get_client_ip(request):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')
