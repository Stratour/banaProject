from django.http import HttpResponsePermanentRedirect

APEX_HOST = 'bana.mobi'
CANONICAL_HOST = 'www.bana.mobi'


class WWWRedirectMiddleware:
    """
    Redirige en 301 bana.mobi -> www.bana.mobi (version canonique, cf. layouts/base.html).
    Ne touche pas aux autres hosts (localhost, 127.0.0.1, IP serveur) pour ne pas casser
    le dev local ni les health checks sur l'IP nue.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.get_host().split(':')[0] == APEX_HOST:
            redirect_url = f"{request.scheme}://{CANONICAL_HOST}{request.get_full_path()}"
            return HttpResponsePermanentRedirect(redirect_url)
        return self.get_response(request)
