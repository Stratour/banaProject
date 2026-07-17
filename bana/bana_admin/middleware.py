import ipaddress
from datetime import timedelta
from django.utils import timezone
from .models import SiteVisit

EXCLUDED_PREFIXES = ('/static/', '/media/', '/__reload__/')

THROTTLE_MINUTES = 5

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


def _get_device_type(user_agent: str) -> str:
    ua = user_agent.lower()
    if any(k in ua for k in ('ipad', 'tablet', 'kindle', 'playbook', 'silk')):
        return 'tablet'
    if any(k in ua for k in ('mobile', 'android', 'iphone', 'ipod', 'windows phone', 'blackberry', 'opera mini', 'opera mobi')):
        return 'mobile'
    return 'desktop'


def _anonymize_ip(ip: str) -> str:
    try:
        addr = ipaddress.ip_address(ip)
        if isinstance(addr, ipaddress.IPv4Address):
            parts = ip.split('.')
            return f"{parts[0]}.{parts[1]}.{parts[2]}.0"
        else:
            # IPv6 : conserver uniquement le préfixe /48
            network = ipaddress.ip_network(f"{ip}/48", strict=False)
            return str(network.network_address)
    except ValueError:
        return '0.0.0.0'


class SiteVisitMiddleware:
    """
    Enregistre la dernière visite par IP anonymisée + utilisateur dans SiteVisit.
    - Filtre les bots connus
    - Anonymise l'IP avant stockage (RGPD)
    - Détecte le type d'appareil sans stocker le User-Agent complet
    - Throttle à 5 min pour éviter une écriture DB à chaque requête
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
        device = _get_device_type(user_agent)
        cutoff = timezone.now() - timedelta(minutes=THROTTLE_MINUTES)

        try:
            if request.user.is_authenticated:
                SiteVisit.objects.filter(user=request.user).exclude(ip_address=ip).delete()
                visit, created = SiteVisit.objects.get_or_create(
                    ip_address=ip,
                    user=request.user,
                    defaults={'device_type': device},
                )
                if not created and visit.timestamp < cutoff:
                    visit.device_type = device
                    visit.save()
            else:
                visit, created = SiteVisit.objects.get_or_create(
                    ip_address=ip,
                    user=None,
                    defaults={'device_type': device},
                )
                if not created and visit.timestamp < cutoff:
                    visit.device_type = device
                    visit.save()
        except Exception:
            pass

        return response

    @staticmethod
    def _get_client_ip(request):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            # Prendre le DERNIER IP (ajouté par notre proxy nginx, non falsifiable)
            ip = x_forwarded.split(',')[-1].strip()
            try:
                ipaddress.ip_address(ip)
                return _anonymize_ip(ip)
            except ValueError:
                pass
        return _anonymize_ip(request.META.get('REMOTE_ADDR', '0.0.0.0'))
