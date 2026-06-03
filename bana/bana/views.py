import os
from django.shortcuts import render, redirect
from django.utils import translation
from django.utils.http import url_has_allowed_host_and_scheme
from bana import settings
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.utils.translation import gettext_lazy as _

# --- Home page ---------------------------------------------------------------------------
def home(request):
    home_benefits = [
        {
            'img_src': 'bana/img/page/home/flexibilite-agenda.svg',
            'title': _('Gain de temps'),
            'highlight': _('Flexibilité'),
            'description': _('Flexibilité dans votre agenda')
        },
        {
            'img_src': 'bana/img/page/home/economie-carburant.svg',
            'title': _('Économique'),
            'highlight': _('Économiser'),
            'description': _('Économiser sur <br>le carburant')
        },
        {
            'img_src': 'bana/img/page/home/ecologie.svg',
            'title': _('Écologique'),
            'highlight': _('Utiliser'),
            'description': _('Utiliser des moyens de transport alternatifs')
        },
        {
            'img_src': 'bana/img/page/home/communaute.svg',
            'title': _('Communauté'),
            'highlight': _('Créer du lien social'),
            'description': _('Créer du lien social <br> dans votre quartier')
        }
    ]

    home_roles = [
        {
            'img_src': 'bana/img/other/Bana_Parent.png',
            'alt_text': _('Parent Icon'),
            'link_text': _('Je suis un parent'),
            'link_url': '#'
        },
        {
            'img_src': 'bana/img/other/Bana_Mentor.png',
            'alt_text': _('Mentor Icon'),
            'link_text': _('Je suis un mentor'),
            'link_url': '#'
        },
        {
            'img_src': 'bana/img/other/Bana_Community.png',
            'alt_text': _('Community Icon'),
            'link_text': _('Je fais partie de la communauté'),
            'link_url': '#'
        }
    ]

    return render(
        request,
        'home.html',
        {"home_benefits": home_benefits, "home_roles": home_roles}
    )

# --- Comment ça marche page ---------------------------------------------------------------------------
def work(request):
    work_steps = [
        {'img_src': 'bana/img/icon/Icon_profile.svg', 'title': '1. Créez votre compte', 'description': "Parents et Yaya s'inscrivent gratuitement en 3 min"},
        {'img_src': 'bana/img/icon/Icon_place.svg',   'title': '2. Ajoutez vos trajets', 'description': 'Renseignez vos trajets habituels et vos modes de transport'},
        {'img_src': 'bana/img/icon/Icon_search_active.svg',  'title': '3. Découvrez vos matchings', 'description': "Passez à l'abonnement pour contacter votre Yaya"},
        {'img_src': 'bana/img/icon/Icon_meet.svg',    'title': '4. Organisez la rencontre', 'description': "Une rencontre est prévue entre parent, enfant et Yaya avant le 1er trajet"},
    ]

    work_detail_steps = [
        {
            'number': '1',
            'title': 'Créez votre compte gratuitement',
            'description': "Parents et Yaya s'inscrivent gratuitement sur la plateforme en 3 min et complètent leur profil avec leur photo.",
            'highlight': None,
        },
        {
            'number': '2',
            'title': 'Ajoutez vos trajets',
            'description': "Indiquez les <strong>trajets que vous recherchez ou que vous proposez</strong> et choisissez vos modes de transport :",
            'highlight': "À pied, en vélo, avec un transport en commun ou en covoiturage.",
        },
        {
            'number': '3',
            'title': 'Découvrez vos matchings',
            'description': "Lorsque des trajets compatibles sont trouvés, <strong>les profils des Yayas correspondants apparaissent dans vos résultats</strong>.",
            'highlight': "Pour les contacter et organiser le premier trajet, passez à l'abonnement.",
            'cta': {'text': 'Voir les tarifs', 'url': '#'},
        },
        {
            'number': '4',
            'title': 'Rencontrez-vous avant le premier trajet',
            'description': "Une rencontre entre le parent, l'enfant et le Yaya est <strong>organisée avant tout premier trajet</strong> — pour vérifier le parcours et instaurer la confiance.",
            'highlight': "Cette rencontre est <strong>obligatoire</strong>.",
        },
    ]

    work_journey_steps = [
        {
            'icon_src': 'bana/img/page/work/prise-en-charge-3.svg',
            'title': 'Prise en charge',
            'short_description': "Le Yaya récupère l'enfant auprès d'un adulte responsable et prévient le parent du départ.",
            'description': "Le Yaya récupère l'enfant à la maison ou auprès d'un adulte (parent, enseignant, éducateur…). Le parent reçoit un <strong>message confirmant la prise en charge</strong> et le départ de l'enfant.",
        },
        {
            'icon_src': 'bana/img/page/work/accompagnement-securise-1.svg',
            'title': 'Accompagnement sécurisé',
            'short_description': "L'enfant voyage en sécurité jusqu'à destination, quel que soit le mode de transport.",
            'description': "Le Yaya accompagne l'enfant du départ jusqu'à la destination. Quel que soit le moyen de transport utilisé, <strong>le Yaya assure la sécurité de l'enfant pendant tout le trajet</strong>.",
        },
        {
            'icon_src': 'bana/img/page/work/arrivee-et-confirmation-1.svg',
            'title': 'Arrivée et confirmation',
            'short_description': "L'enfant est confié à un adulte à l'arrivée — le parent reçoit une confirmation.",
            'description': "L'enfant est confié à un adulte responsable à l'arrivée selon les directives du parent. Le parent reçoit un <strong>message confirmant l'arrivée de l'enfant</strong>.",
        },
        {
            'icon_src': 'bana/img/page/work/defraiement-2.svg',
            'title': 'Défraiement',
            'short_description': "Le parent verse directement au Yaya le défraiement convenu pour le trajet.",
            'description': "Le parent verse directement au Yaya une <strong>compensation financière pour le trajet</strong>, convenue librement entre eux selon la distance et la fréquence (réglée journalièrement ou hebdomadairement).",
        },
    ]

    work_profiles = [
        {
            'img_src': 'bana/img/other/Sandy.png',
            'name': 'Sandy D.',
            'age': '38 ans',
            'short_bio': 'Maman de Justin et Bastien, 5 et 7 ans',
            'full_description': "Avant, je choisissais leurs activités en fonction de mes disponibilités. Aujourd'hui, je peux leur ouvrir la porte à un monde de possibilités : il n'y a plus de limites !",
        },
        {
            'img_src': 'bana/img/other/Thi.png',
            'name': 'Thi M.',
            'age': '38 ans',
            'short_bio': 'Maman de 2 garçons, 5 et 9 ans',
            'full_description': "Bana me permet d'aider et de dépanner d'autres parents. J'apprécie particulièrement le concept collaboratif et communautaire de cette application.",
        },
        {
            'img_src': 'bana/img/other/Andre.png',
            'name': 'André K.',
            'age': '41 ans',
            'short_bio': 'Papa de 3 enfants, 1, 5 et 8 ans',
            'full_description': "Comme beaucoup de parents, j'étais assez réticent à confier mes enfants à d'autres. J'ai donc contacté Bana pour discuter de la confiance et de la sécurité : j'ai été très vite rassuré !",
        },
        {
            'img_src': 'bana/img/other/Alex.png',
            'name': 'Alex M.',
            'age': '33 ans',
            'short_bio': 'Papa de Maé, 6 ans',
            'full_description': "En tant qu'éducateur spécialisé, j'ai des horaires coupés qui me laissent peu de flexibilité. Avec cette application, j'ai trouvé une solution pour ma fille à moindre coût. Tout le monde y gagne, moi le premier !",
        },
        {
            'img_src': 'bana/img/other/Shilo.png',
            'name': 'Shilo B.',
            'age': '10 ans',
            'short_bio': "Élève de 5ᵉ primaire",
            'full_description': "Ce que j'adore avec Bana, c'est l'idée que je peux passer plus de temps avec mes amis car on va ensemble aux activités, c'est trop cool !",
        },
        {
            'img_src': 'bana/img/other/Ludo.png',
            'name': 'Ludo B.',
            'age': '42 ans',
            'short_bio': 'Papa de 2 garçons, 18 et 10 ans',
            'full_description': "J'y ai rencontré des parents très sérieux et flexibles. Nous partageons beaucoup de choses avec des amis qui vont au-delà des trajets de nos enfants.",
        },
    ]
    return render(request, 'work.html', {
        "work_steps": work_steps,
        "work_detail_steps": work_detail_steps,
        "work_journey_steps": work_journey_steps,
        "work_profiles": work_profiles,
    })

# --- Yaya page ---------------------------------------------------------------------------
def yaya(request):
    yaya_benefits = [
        {
            'img_src': 'bana/img/page/yaya/flexibilite.svg',
            'title': _('Flexible'),
            'description': _('Engagement uniquement selon votre disponibilité')
        },
        {
            'img_src': 'bana/img/page/yaya/defraiement-2b.svg',
            'title': _('Défraiement'),
            'description': _('Recevez jusqu’à 176€/mois pour vos trajets quotidiens')
        },
        {
            'img_src': 'bana/img/page/yaya/sans-voiture-obligatoire.svg',
            'title': _('Sans voiture obligatoire'),
            'description': _('Tous les moyens de transport sont utilisés')
        },
        {
            'img_src': 'bana/img/page/yaya/communautaire.svg',
            'title': _('Communautaire'),
            'description': _('Créer du lien social dans votre quartier')
        }
    ]

    work_profiles = [
        {
            'img_src': 'bana/img/other/Sandy.png',
            'name': 'Sandy D.',
            'age': '38 ans',
            'short_bio': 'Maman de Justin et Bastien, 5 et 7 ans',
            'full_description': 'Avant, je choisissais leurs activités en fonction de mes disponibilités. Aujourd’hui, je peux leur ouvrir la porte à un monde de possibilités : il n’y a plus de limites !'
        },
        {
            'img_src': 'bana/img/other/Thi.png',
            'name': 'Thi M.',
            'age': '38 ans',
            'short_bio': 'Maman de 2 garçons, 5 et 9 ans',
            'full_description': 'Bana me permet d’aider et de dépanner d’autres parents. J’apprécie particulièrement le concept collaboratif et communautaire de cette application.'
        },
        {
            'img_src': 'bana/img/other/Andre.png',
            'name': 'André K.',
            'age': '41 ans',
            'short_bio': 'Papa de 3 enfants, 1, 5 et 8 ans',
            'full_description': 'Comme beaucoup de parents, j’étais assez réticent à confier mes enfants à d’autres. J’ai donc contacté Bana pour discuter de la confiance et de la sécurité : j’ai été très vite rassuré !'
        },
         {
            'img_src': 'bana/img/other/Alex.png',
            'name': 'Alex M.',
            'age': '33 ans',
            'short_bio': 'Papa de Maé, 6 ans',
            'full_description': 'En tant qu’éducateur spécialisé, j’ai des horaires coupés qui me laissent peu de flexibilité. Avec cette application, j’ai trouvé une solution pour ma fille à moindre coût. Tout le monde y gagne, moi le premier !'
        },
        {
            'img_src': 'bana/img/other/Shilo.png',
            'name': 'Shilo B.',
            'age': '10 ans',
            'short_bio': 'élève de 5ᵉ primaire',
            'full_description': 'Ce que j’adore avec Bana, c’est l’idée que je peux passer plus de temps avec mes amis car on va ensemble aux activités, c’est trop cool !'
        },
        {
            'img_src': 'bana/img/other/Ludo.png',
            'name': 'Ludo B.',
            'age': '42 ans',
            'short_bio': 'papa de 2 garçons, 18 et 10 ans',
            'full_description': 'J’y ai rencontré des parents très sérieux et flexibles. Nous partageons beaucoup de choses avec des amis qui vont au-delà des trajets de nos enfants.'
        }
    ]

    return render(request,'yaya.html', {"work_profiles": work_profiles, "yaya_benefits": yaya_benefits})

# --- Tarifs page ---------------------------------------------------------------------------
def tarifs(request):
    parent_packs = [
        {
            'name': 'Formule Essentiel',
            'tagline': 'Simplifier les trajets du quotidien',
            'price': '99',
            'included': '1 enfant inclus',
            'extra_child': '+30€/an par enfant supplémentaire',
            'highlight': False,
            'features': [
                "Profils vérifiés (carte d'identité + extrait de casier judiciaire)",
                "Accès matching",
                "Notifications nouveaux matchings",
                "Réservation des trajets",
            ],
        },
        {
            'name': 'Formule Confort',
            'tagline': 'Réduire la charge mentale',
            'price': '149',
            'included': '1 enfant inclus',
            'extra_child': '+40€/an par enfant supplémentaire',
            'highlight': True,
            'features': [
                "Pack Essentiel inclus +",
                "Calendrier",
                "Rappels automatiques",
                "Historique des trajets",
                "Notifications intelligentes",
                "Accessoire sécurité routière",
            ],
        },
        {
            'name': 'Formule Premium',
            'tagline': "Faciliter l'organisation familiale",
            'price': '199',
            'included': '1 enfant inclus',
            'extra_child': '+50€/an par enfant supplémentaire',
            'highlight': False,
            'features': [
                "Pack Confort inclus +",
                "Badge identification enfant personnalisé",
                "Calendrier familial partagé",
                "Accès multi-utilisateurs",
                "Assurance enfant incluse",
            ],
        },
    ]
    defraiement_table = [
        {'duration': 'Moins de 10 minutes', 'amount': '3€'},
        {'duration': '10 à 20 minutes', 'amount': '4€ à 5€'},
        {'duration': '20 à 30 minutes', 'amount': '5€ à 7€'},
    ]
    tarifs_highlights = [
        {
            'img_src': 'bana/img/page/tarifs/inscription-gratuite.svg',
            'title': _('Inscription gratuite'),
            'description': _("Parents et Yaya <br> s'inscrivent gratuitement"),
        },
        {
            'img_src': 'bana/img/page/tarifs/abonnement-payant.svg',
            'title': _('Abonnement payant'),
            'description': _("Nécessaire pour découvrir <br> les matchings"),
        },
        {
            'img_src': 'bana/img/page/tarifs/defraiement-1.svg',
            'title': _('Trajets défrayés'),
            'description': _("Petite compensation <br> pour chaque trajet effectué"),
        },
    ]
    return render(request, 'tarifs.html', {
        'parent_packs': parent_packs,
        'defraiement_table': defraiement_table,
        'tarifs_highlights': tarifs_highlights,
    })

# --- Notre mission page ---------------------------------------------------------------------------
def about(request):
    impacts = [
        {'emoji': '🚗', 'icon': 'bana/img/page/about/trafic_1.svg',      'text': 'Moins de trafic sur la route'},
        {'emoji': '🧒', 'icon': 'bana/img/page/about/autonomie.svg',      'text': "Autonomie progressive des enfants"},
        {'emoji': '🧠', 'icon': 'bana/img/page/about/mental.svg',         'text': 'Moins de charge mentale'},
        {'emoji': '🤝', 'icon': 'bana/img/page/about/communautaire.svg',  'text': "Plus d'entraide communautaire"},
        {'emoji': '🌱', 'icon': 'bana/img/page/about/environnement.svg',  'text': 'Impact environnemental concret'},
        {'emoji': '🔒', 'icon': 'bana/img/page/about/securite.svg',       'text': 'Plus de sécurité autour des écoles'},
    ]
    odd_badges = [
        {'number': '03', 'name': 'Bonne santé et bien-être'},
        {'number': '04', 'name': 'Éducation de qualité'},
        {'number': '05', 'name': 'Égalité entre les sexes'},
        {'number': '08', 'name': 'Travail décent et croissance économique'},
        {'number': '10', 'name': 'Inégalités réduites'},
        {'number': '11', 'name': 'Villes et communautés durables'},
        {'number': '12', 'name': 'Consommation et production responsables'},
        {'number': '13', 'name': 'Action climatique'},
        {'number': '17', 'name': 'Partenariats pour les objectifs'},
    ]
    stats = [
        {'value': '250+', 'label': 'Trajets effectués'},
        {'value': '5', 'label': 'Villes actives'},
        {'value': '3', 'label': 'Prix reçus'},
    ]
    partners = [
        {
            'logo': 'bana/img/logo/logo_materne.png',
            'name': 'Materne',
            'url': 'https://www.materne.be/pages/pocket',
            'type': 'Mécénat matériel',
            'description': 'Lots de compotes distribués lors de nos événements communautaires.',
        },
        {
            'logo': 'bana/img/logo/logo_alvityl.png',
            'name': 'Alvityl',
            'url': 'https://alvityl.be/',
            'type': 'Mécénat matériel',
            'description': 'Lots de vitamines offerts aux membres de la communauté Bana.',
        },
        {
            'logo': 'bana/img/logo/logo_coverseal.png',
            'name': 'Coverseal',
            'url': 'https://coverseal.com/',
            'type': 'Mécénat de compétences',
            'description': 'Expertise technique et accompagnement au service de Bana.',
        },
        {
            'logo': 'bana/img/logo/logo_digit_up.svg',
            'name': 'Digit Up Agency',
            'url': 'https://www.digit-up.be/',
            'type': 'Partenaire digital',
            'description': 'Développement web et accompagnement digital de la plateforme.',
        },
        {
            'logo': 'bana/img/logo/logo_startit@kbc.png',
            'name': 'Start it @KBC',
            'url': 'https://startit-x.com/en/accelerate/start-it-kbc',
            'type': 'Accélérateur',
            'description': "Programme d'accélération startup pour développer l'impact de Bana.",
        },
        {
            'logo': 'bana/img/logo/logo_capinnove.png',
            'name': 'Cap Innove',
            'url': 'https://capinnove.be/',
            'type': 'Incubateur',
            'description': "Incubation et accompagnement à l'innovation sociale et entrepreneuriale.",
        },
    ]
    team_members = [
        {
            'img_src': 'bana/img/page/about/Nyota.png',
            'name': 'Nyota Delecourt',
            'role': 'Fondatrice',
            'description': 'Entrepreneuriat social et mobilité, Nyota porte la vision communautaire de Bana.',
            'linkedin': '#',
            'instagram': '',
        },
        {
            'img_src': 'bana/img/page/about/Luca.png',
            'name': 'Luca C.',
            'role': 'Développeur IT',
            'description': 'Architecture et développement de la plateforme, du backend aux interfaces.',
            'linkedin': '#',
            'instagram': '',
        },
        {
            'img_src': 'bana/img/page/about/Raph.png',
            'name': 'Raphaël J.',
            'role': 'Développeur IT',
            'description': 'Innovation digitale et intégration des fonctionnalités clés de la plateforme.',
            'linkedin': '#',
            'instagram': '',
        },
    ]
    return render(request, 'about.html', {
        'impacts': impacts,
        'odd_badges': odd_badges,
        'stats': stats,
        'partners': partners,
        'team_members': team_members,
    })




# --- Parent page ---------------------------------------------------------------------------
def parent(request):
    features_search = [
        {"icon": "Icon_clock.svg", "title": "Time saving", "highlight": "Flexibility", "text": "in your calendar"},
        {"icon": "Icon_currency.svg", "title": "Economic", "highlight": "money", "text": "on gasoline"},
        {"icon": "Icon_earth.svg", "title": "Ecological", "highlight": "alternative", "text": "transport"},
        {"icon": "Icon_hearth.svg", "title": "Community", "highlight": "Social connection", "text": "& sharing moments"},
    ]

    features_share = [
        {"icon": "Icon_flexibility.svg", "title": "Flexibility", "highlight": "You choose", "text": "the rides you share"},
        {"icon": "Icon_experience.svg", "title": "Experience", "highlight": "development", "text": "Support children's"},
        {"icon": "Icon_support.svg", "title": "Most importantly", "highlight": "in your community", "text": "Support other parents"},
        {"icon": "Icon_trust.svg", "title": "Trust", "highlight": "Provide safe", "text": ", reliable rides with trusted parents."},
    ]
    return render(request, 'parent.html', {"features_search": features_search, "features_share": features_share})

# --- Conact page ---------------------------------------------------------------------------
def contact(request):
    return render(request, 'contact.html')

# --- PWA ---------------------------------------------------------------------------
def manifest(request):
    data = {
        "name": "Bana.mobi",
        "short_name": "Bana",
        "description": "Plateforme de mobilité partagée pour les trajets des enfants",
        "start_url": "/fr/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#007F73",
        "lang": "fr",
        "orientation": "portrait-primary",
        "icons": [
            {
                "src": "/static/bana/img/icon/icon-192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any"
            },
            {
                "src": "/static/bana/img/icon/icon-512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any"
            },
            {
                "src": "/static/bana/img/icon/icon-192-maskable.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "maskable"
            },
            {
                "src": "/static/bana/img/icon/icon-512-maskable.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "maskable"
            }
        ],
        "id": "/fr/",
        "categories": ["social", "travel", "kids"]
    }
    return JsonResponse(data, content_type="application/manifest+json")


def service_worker(request):
    sw_path = os.path.join(os.path.dirname(__file__), 'static', 'bana', 'js', 'sw.js')
    with open(sw_path, 'r') as f:
        content = f.read()
    response = HttpResponse(content, content_type="application/javascript")
    response['Service-Worker-Allowed'] = '/'
    response['Cache-Control'] = 'no-cache'
    return response


def offline(request):
    return render(request, 'offline.html')


# --- SEO ---------------------------------------------------------------------------
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /accounts/login/",
        "Disallow: /accounts/signup/",
        "Disallow: /accounts/password/",
        "Disallow: /accounts/email/",
        "Disallow: /accounts/confirm-email/",
        "Disallow: /accounts/social/",
        "Disallow: /accounts/reauthenticate/",
        "Disallow: /accounts/3rdparty/",
        "Disallow: /admin/",
        "Disallow: /bana_admin/",
        "Disallow: /bug_tracker/",
        "Disallow: /trajets/",
        "Disallow: /chat/",
        "Disallow: /profil/",
        "Disallow: /webhook/",
        "Disallow: /switch-language/",
        "Disallow: /i18n/",
        "Allow: /",
        "",
        "Sitemap: https://www.bana.mobi/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


# --- Language switch ---------------------------------------------------------------------------
def switch_language(request, language):
    """
    Vue pour changer de langue et rediriger vers la même page
    dans la nouvelle langue
    """
    # Vérifier que la langue est supportée
    if language in [lang[0] for lang in settings.LANGUAGES]:
        # Activer la nouvelle langue
        translation.activate(language)
        
        # Sauvegarder dans la session
        request.session['django_language'] = language
        
        # Obtenir l'URL de référence et extraire le chemin
        referer = request.META.get('HTTP_REFERER', '/')
        
        # Extraire le chemin de l'URL complète
        if 'http' in referer:
            # Séparer l'URL pour obtenir juste le chemin
            path_parts = referer.split('/', 3)  # ['http:', '', 'domain:port', 'path']
            current_path = '/' + (path_parts[3] if len(path_parts) > 3 else '')
        else:
            current_path = referer
        
        # Enlever le préfixe de langue actuel s'il existe
        for lang_code, _ in settings.LANGUAGES:
            if current_path.startswith(f'/{lang_code}/'):
                current_path = current_path[3:]  # Enlever /xx/
                break
            elif current_path == f'/{lang_code}':
                current_path = '/'  # Si on est juste sur /xx, aller à la racine
                break
        
        # S'assurer que le chemin commence par /
        if not current_path.startswith('/'):
            current_path = '/' + current_path
        
        # Construire la nouvelle URL avec le préfixe de langue
        if current_path == '/':
            new_url = f'/{language}/'
        else:
            new_url = f'/{language}{current_path}'
        
        return HttpResponseRedirect(new_url)
    
    # Si la langue n'est pas supportée, rediriger sans changement
    fallback = request.META.get('HTTP_REFERER', '/')
    if not url_has_allowed_host_and_scheme(fallback, allowed_hosts={request.get_host()}):
        fallback = '/'
    return redirect(fallback)