"""Helpers d'affichage partagés entre les vues et les emails.

Ces fonctions vivaient dans `views.py`, mais `utils/mail.py` ne peut pas les y
importer : `views.py` importe déjà `utils.mail`, l'import serait circulaire. Ce
module est donc le point bas commun — il ne doit importer ni les vues ni les
modèles de l'app.
"""

from django.conf import settings
from django.urls import reverse
from django.utils import translation
from django.utils.translation import get_supported_language_variant, gettext_lazy as _


def display_name_and_initials(person):
    """Nom affichable ("Prénom N.") + initiales, en privilégiant l'identité
    vérifiée par Stripe Identity quand elle existe."""
    if not person:
        return "", "?"
    profile = getattr(person, "profile", None)
    if profile and profile.ci_is_verified and profile.verified_first_name and profile.verified_last_name:
        first, last = profile.verified_first_name, profile.verified_last_name
    else:
        first, last = person.first_name, person.last_name
    # L'initiale n'est ajoutée que si le nom existe : sans cette garde, un
    # membre qui n'a renseigné que son prénom s'affichait « Marie . », point
    # orphelin compris. Le nom de famille est facultatif à l'inscription, le cas
    # est donc courant.
    first = (first or "").strip()
    last = (last or "").strip()
    display = f"{first} {last[:1]}." if first and last else first
    initials = f"{(first or '?')[:1]}{last[:1]}".upper()
    return display, initials


def display_name(person, fallback=""):
    """Nom affichable seul, avec repli quand l'identité n'est pas renseignée.

    Jamais l'adresse email en repli : elle apparaîtrait dans le corps ou l'objet
    d'un mail, alors qu'elle ne doit se découvrir qu'au moment de répondre.
    """
    display, initials = display_name_and_initials(person)
    if initials == "?" or not display.strip(" ."):
        return fallback
    return display


def first_name_only(person, fallback=""):
    """Prénom seul, pour s'adresser à quelqu'un.

    « Bonjour Luca L., » sonne comme un courrier administratif : on interpelle
    le destinataire par son prénom. `display_name` reste la forme à utiliser
    pour désigner un TIERS (« Sophie L. a confirmé »), où l'initiale du nom aide
    à distinguer deux personnes du même prénom.

    Même priorité que partout ailleurs : identité vérifiée par Stripe Identity
    d'abord, prénom du compte ensuite, et jamais l'adresse email en repli.
    """
    if not person:
        return fallback
    profile = getattr(person, "profile", None)
    if profile and profile.ci_is_verified and profile.verified_first_name:
        first = profile.verified_first_name
    else:
        first = person.first_name
    return (first or "").strip() or fallback


def child_labels(researched_traject):
    """Pastilles enfant du calendrier, au même format que child_badge.html."""
    if not researched_traject:
        return []
    return [
        {
            "label": f"{c.chld_name} {(c.chld_surname or '')[:1]}.".strip(),
            "age": c.age,
        }
        for c in researched_traject.children.all()
    ]


def traject_parts(traject, is_simple=False, radius_km=None):
    """Adresses d'un trajet, décomposées et prêtes à afficher.

    `Traject.__str__` concatène toujours « départ → arrivée », ce qui laisse une
    flèche orpheline sur les offres dans un rayon (`is_simple=True`) : elles
    n'ont pas de destination, seulement un point de départ et un rayon. Les
    emails ne peuvent pas se contenter de `str(traject)`.
    """
    depart = (traject.start_adress or "").strip()
    arrivee = (traject.end_adress or "").strip()
    if is_simple or not arrivee:
        label = depart
    else:
        label = f"{depart} → {arrivee}"
    return {
        "trajet_info": label,
        "depart_adresse": depart,
        "arrivee_adresse": "" if is_simple else arrivee,
        "is_simple": bool(is_simple),
        "search_radius_km": radius_km if is_simple else None,
    }


def cancellation_label(canceled_by, side):
    """Libellé d'une réservation annulée.

    `side` vaut "made" (je suis le demandeur) ou "received" (on me sollicite) :
    un refus du conducteur et une annulation du parent valent tous deux
    status='canceled', seul `canceled_by` les distingue.

    Source unique du libellé : `_status_badge` (views.py) y branche ses couleurs
    et les emails d'annulation s'en servent tels quels. Les deux ne doivent pas
    diverger.
    """
    if canceled_by == 'auto':
        return _("Annulée - date déjà couverte") if side == 'made' \
            else _("Annulée - le parent a confirmé ailleurs")
    if canceled_by == 'yaya':
        return _("Refusée") if side == 'made' else _("Refusée par vous")
    if canceled_by == 'parent':
        return _("Annulée par vous") if side == 'made' else _("Annulée par le parent")
    # canceled_by vide : réservations annulées avant l'ajout du champ.
    return _("Annulée")


def format_time(value, fallback=""):
    """Heure au format HH:MM, chaîne vide quand l'heure manque.

    `ProposedTraject.departure_time` et `arrival_time` sont nullables —
    l'appelant doit avoir tenté son repli vers la recherche avant d'arriver ici.
    Le repli est vide plutôt qu'un tiret pour que les gabarits puissent masquer
    la ligne entière : « Horaires : — → — » ne vaut pas mieux que rien.
    """
    return value.strftime("%H:%M") if value else fallback


def absolute_url(url_name, *args, **kwargs):
    """URL absolue utilisable dans un email.

    `utils/mail.py` reçoit des modèles, jamais de `request` : pas de
    `build_absolute_uri` possible, et `django.contrib.sites` n'est pas installé
    (le SITE_ID de settings.py est un résidu). D'où le réglage `SITE_BASE_URL`.

    La langue est forcée parce que les routes `trajects` sont sous
    `i18n_patterns(prefix_default_language=True)` : sans ça, `reverse()`
    utiliserait la langue active au moment de l'envoi — celle de l'émetteur, pas
    du destinataire, qui enverrait un lien /nl/ à un francophone.

    `get_supported_language_variant` est indispensable : LANGUAGE_CODE vaut
    'fr-fr' alors que LANGUAGES ne déclare que 'fr', et le préfixe servi est
    donc /fr/. Forcer 'fr-fr' tel quel produirait des liens /fr-fr/ morts.
    """
    try:
        lang = get_supported_language_variant(settings.LANGUAGE_CODE)
    except LookupError:
        lang = settings.LANGUAGE_CODE
    with translation.override(lang):
        path = reverse(url_name, args=args, kwargs=kwargs)
    return f"{settings.SITE_BASE_URL.rstrip('/')}{path}"
