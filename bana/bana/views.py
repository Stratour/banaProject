from django.shortcuts import render, redirect
from django.utils import translation
from bana import settings
from django.http import HttpResponseRedirect
from django.utils.translation import gettext_lazy as _

# --- Home page ---------------------------------------------------------------------------
def home(request):
    home_benefits = [
        {
            'img_src': 'bana/img/icon/Icon_clock.svg',
            'title': _('Gain de temps'),
            'highlight': _('Flexibilité'),
            'description': _('dans votre agenda')
        },
        {
            'img_src': 'bana/img/icon/Icon_currency.svg',
            'title': _('Économique'),
            'highlight': _('Économiser'),
            'description': _('sur l’essence')
        },
        {
            'img_src': 'bana/img/icon/Icon_earth.svg',
            'title': _('Écologique'),
            'highlight': _('Utiliser'),
            'description': _('des moyens de transport alternatifs')
        },
        {
            'img_src': 'bana/img/icon/Icon_hearth.svg',
            'title': _('Communauté'),
            'highlight': _('Créer du lien social'),
            'description': _('en partageant des moments')
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

# --- Conact page ---------------------------------------------------------------------------
def contact(request):
    return render(request, 'contact.html')

# --- About page ---------------------------------------------------------------------------
def about(request):
    return render(request, 'about.html')

# --- Work page ---------------------------------------------------------------------------
def work(request):
    work_steps = [
        {'img_src': 'bana/img/icon/Icon_profile.svg', 'title': '1. Créez votre profil', 'highlight': 'Rejoignez une communauté', 'description': 'de parents de l’école ou des activités de votre enfant.'},
        {'img_src': 'bana/img/icon/Icon_place.svg', 'title': '2. Indiquez vos trajets', 'highlight': 'Partagez vos demandes de trajets', 'description': 'ou répondez aux alertes, et Bana vous met en relation.'},
        {'img_src': 'bana/img/icon/Icon_message.svg', 'title': '3. Composez votre tribu', 'highlight': 'Trouvez des parents aux trajets similaires,', 'description': 'choisissez leurs profils et construisez votre tribu de confiance.'}
    ]

    work_roles = [
        {'img_src': 'bana/img/other/Bana_Parent.png', 'alt_text': 'Parent Icon', 'link_text': 'I am a parent', 'link_url': '#'},
        {'img_src': 'bana/img/other/Bana_Mentor.png', 'alt_text': 'Mentor Icon', 'link_text': 'I am a mentor', 'link_url': '#'},
        {'img_src': 'bana/img/other/Bana_Community.png', 'alt_text': 'Community Icon', 'link_text': 'I am a community member', 'link_url': '#'}
    ]

    work_profiles = [
        {
            'img_src': 'bana/img/other/Sandy.png',
            'name': 'Sandy D.',
            'short_bio': '38 ans, maman de Justin et Bastien, 5 et 7 ans',
            'full_description': 'Avant, je choisissais leurs activités en fonction de mes disponibilités. Aujourd’hui, je peux leur ouvrir la porte à un monde de possibilités : il n’y a plus de limites !'
        },
        {
            'img_src': 'bana/img/other/Thi.png',
            'name': 'Thi M.',
            'short_bio': '38 ans, maman de 2 garçons, 5 et 9 ans',
            'full_description': 'Bana me permet d’aider et de dépanner d’autres parents. J’apprécie particulièrement le concept collaboratif et communautaire de cette application.'
        },
        {
            'img_src': 'bana/img/other/Andre.png',
            'name': 'André K.',
            'short_bio': '41 ans, papa de 3 enfants, 1, 5 et 8 ans',
            'full_description': 'Comme beaucoup de parents, j’étais assez réticent à confier mes enfants à d’autres. J’ai donc contacté Bana pour discuter de la confiance et de la sécurité : j’ai été très vite rassuré !'
        }
    ]
    return render(request, 'work.html', {"work_steps": work_steps, "work_roles": work_roles, "work_profiles": work_profiles})


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
    return redirect(request.META.get('HTTP_REFERER', '/'))