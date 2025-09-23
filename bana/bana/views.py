from django.shortcuts import render, redirect
from django.utils import translation
from bana import settings

# --- Home page ---------------------------------------------------------------------------
def home(request):
    home_benefits = [
        {'img_src': 'bana/img/icon/Icon_clock.svg', 'title': 'Gain de temps', 'highlight': 'Flexibilité', 'description': 'dans votre agenda'},
        {'img_src': 'bana/img/icon/Icon_currency.svg', 'title': 'Économique', 'highlight': 'Économiser', 'description': 'sur l’essence'},
        {'img_src': 'bana/img/icon/Icon_earth.svg', 'title': 'Écologique', 'highlight': 'Utiliser', 'description': 'des moyens de transport alternatifs'},
        {'img_src': 'bana/img/icon/Icon_hearth.svg', 'title': 'Communauté', 'highlight': 'Créer du lien social', 'description': 'en partageant des moments'}
    ]

    home_roles = [
        {'img_src': 'bana/img/other/Bana_Parent.png', 'alt_text': 'Parent Icon', 'link_text': 'I am a parent', 'link_url': '#'},
        {'img_src': 'bana/img/other/Bana_Mentor.png', 'alt_text': 'Mentor Icon', 'link_text': 'I am a mentor', 'link_url': '#'},
        {'img_src': 'bana/img/other/Bana_Community.png', 'alt_text': 'Community Icon', 'link_text': 'I am a community member', 'link_url': '#'}
    ]
    return render(request, 'home.html', {"home_benefits": home_benefits, "home_roles": home_roles})

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

def switch_language(request, lang_code):
    if lang_code in dict(settings.LANGUAGES).keys():
        request.session['django_language'] = lang_code
    return redirect(request.META.get('HTTP_REFERER', '/'))