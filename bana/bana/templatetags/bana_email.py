"""Balises de gabarit réservées aux emails HTML.

Un email est lu hors du site : toute URL y est absolue ou morte. Les images le
sont aussi — Gmail et Outlook ne téléchargent pas un `/static/...` relatif, ils
n'ont aucun hôte auquel le rattacher.

`request` n'est pas une source fiable ici : `trajects/utils/mail.py` rend ses
gabarits à partir de modèles, sans requête. D'où `SITE_BASE_URL`, déjà utilisé
par `absolute_url` pour les liens d'action des emails de trajet.
"""

from django import template
from django.conf import settings
from django.templatetags.static import static

# Source unique des URLs absolues d'email : `absolute_url` force déjà le
# préfixe de langue (/fr/) et connaît le piège LANGUAGE_CODE='fr-fr' vs
# LANGUAGES=['fr']. La redéfinir ici ferait diverger les liens des emails de
# compte de ceux des emails de trajet.
from trajects.utils.display import absolute_url

register = template.Library()


@register.simple_tag
def email_static(path):
    """URL absolue d'un fichier statique (logo, icônes, PDF légaux)."""
    return f"{settings.SITE_BASE_URL.rstrip('/')}{static(path)}"


@register.simple_tag
def email_url(url_name, *args, **kwargs):
    """URL absolue et préfixée /fr/ d'une vue, utilisable dans un email."""
    return absolute_url(url_name, *args, **kwargs)
