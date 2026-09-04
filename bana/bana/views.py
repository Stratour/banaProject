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
            'img_src': 'bana/img/page/home/flexibilite-agenda.png',
            'title': _('Gain de temps'),
            'highlight': _('Flexibilité'),
            'description': _('Flexibilité dans votre agenda')
        },
        {
            'img_src': 'bana/img/page/home/economie-carburant.png',
            'title': _('Économique'),
            'highlight': _('Économiser'),
            'description': _('Économiser sur <br>le carburant')
        },
        {
            'img_src': 'bana/img/page/home/ecologie.png',
            'title': _('Écologique'),
            'highlight': _('Utiliser'),
            'description': _('Utiliser des moyens de transport alternatifs')
        },
        {
            'img_src': 'bana/img/page/home/communaute.png',
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
    
    work_benefits = [
        {
            'img_src': 'bana/img/page/work/carte-identite.png',
            'title': _("Carte d'identité vérifiée"),
            'highlight': _(''),
            'description': _('Vérification via Stripe Identity pour les parents et les Yaya')
        },
        {
            'img_src': 'bana/img/page/work/casier-judiciaire.png',
            'title': _('Extrait de casier judiciaire'),
            'highlight': _(''),
            'description': _('Certificat de bonne vie et mœurs modèle 596.2 pour tous les membres')
        },
        {
            'img_src': 'bana/img/page/work/rencontre.png',
            'title': _('Rencontre préalable'),
            'highlight': _(''),
            'description': _("Rencontre en personne avec le parent, l'enfant et le Yaya avant le 1er trajet")
        },
        {
            'img_src': 'bana/img/page/work/avis.png',
            'title': _("Système d'avis réciproque"),
            'highlight': _(''),
            'description': _("Parents et Yaya sont notés pour un système d'avis équitable")
        }
    ]

    work_detail_steps = [
        {
            'number': '1',
            'title': 'Créez votre profil gratuitement',
            'description': "Encodez vos informations, ajoutez votre photo et indiquez vos trajets.",
        },
        {
            'number': '2',
            'title': 'Découvrez les profils compatibles',
            'description': "Bana identifie automatiquement les parents et les Yaya qui font déjà le même chemin.",
        },
        {
            'number': '3',
            'title': 'Rencontrez-vous avant le premier trajet',
            'description': "Une rencontre préalable permet de vérifier la compatibilité et de créer la confiance.",
        },
    ]

    work_journey_steps = [
        {
            'icon_src': 'bana/img/page/work/prise-en-charge-3.svg',
            'title': 'Prise en charge',
            'short_description': "Le Yaya récupère l'enfant auprès d'un adulte responsable et prévient le parent du départ",
            'description': "Le Yaya récupère l'enfant à la maison ou auprès d'un adulte (parent, enseignant, éducateur…). Le parent reçoit un <strong>message confirmant la prise en charge</strong> et le départ de l'enfant.",
        },
        {
            'icon_src': 'bana/img/page/work/accompagnement-securise-1.svg',
            'title': 'Accompagnement sécurisé',
            'short_description': "L'enfant voyage accompagné jusqu'à destination, quel que soit le mode de transport",
            'description': "Le Yaya accompagne l'enfant du départ jusqu'à la destination. Quel que soit le moyen de transport utilisé, <strong>le Yaya assure la sécurité de l'enfant pendant tout le trajet</strong>.",
        },
        {
            'icon_src': 'bana/img/page/work/arrivee-et-confirmation-1.svg',
            'title': 'Arrivée et confirmation',
            'short_description': "L'enfant est confié à un adulte à l'arrivée et le parent reçoit une confirmation",
            'description': "L'enfant est confié à un adulte responsable à l'arrivée selon les directives du parent. Le parent reçoit un <strong>message confirmant l'arrivée de l'enfant</strong>.",
        },
        
        #{
        #    'icon_src': 'bana/img/page/work/defraiement-2.svg',
        #    'title': 'Défraiement',
        #    'short_description': "Le parent verse directement au Yaya le défraiement convenu pour le trajet.",
        #    'description': "Le parent verse directement au Yaya une <strong>compensation financière pour le trajet</strong>, convenue librement entre eux selon la distance et la fréquence (réglée journalièrement ou hebdomadairement).",
        #},

    ]

    work_profiles = [
        {
            'name': 'Jean-Philippe',
            'short_bio': 'Papa solo de 2 enfants',
            'city': 'Nivelles',
            'full_description': "Mes enfants ont rapidement créé un lien affectif avec leurs accompagnatrices respectives et ont pu poursuivre leur activité tout au long de l'année. Une réussite totale. Je ne peux que recommander ce service.",
        },
        {
            'name': 'Stéphanie',
            'short_bio': 'Maman de 2 enfants',
            'city': 'Baulers',
            'full_description': "Super expérience avec Bana pour conduire ma fille de l'école à son cours de danse à l'académie ! Toujours à l'heure et un petit mot pour vous rassurer quand votre enfant est bien déposé ! À recommander !",
        },
        {
            'name': 'Bernard',
            'short_bio': 'Papa de 3 enfants',
            'city': 'Sombreffe',
            'full_description': "Service parfait avec des valeurs au top. Je recommande !",
        },
        {
            'name': 'Thi Minh',
            'short_bio': 'Maman de 2 enfants',
            'city': 'Overijse',
            'full_description': "Super service fiable. La personne de contact était très douce et a pris le temps de nous expliquer le fonctionnement.",
        },
        {
            'name': 'Patrick',
            'short_bio': 'Papa solo de 3 enfants',
            'city': 'Namur',
            'full_description': "Concept qui simplifie la vie des parents qui sont toujours en train de courir pour aller déposer et récupérer leurs enfants à l'école et leurs différentes activités. Merci Bana",
        },
        {
            'name': 'Valérie',
            'short_bio': 'Maman solo de 1 enfant',
            'city': 'Wavre',
            'full_description': "J'étais un peu perdue et grâce à Bana ma vie a été plus calme, moins stressante et plus reposante !! Merci pour tout",
        },
        {
            'name': 'Stéphane',
            'short_bio': 'Papa de 2 enfants',
            'city': 'Ixelles',
            'full_description': "Service vraiment utile au quotidien pour les parents qui travaillent !",
        },
        {
            'name': 'Sandy',
            'short_bio': 'Maman solo de 2 enfants',
            'city': 'Villers-La-Ville',
            'full_description': "J'ai eu la possibilité de profiter du service d'accompagnement de Bana. J'ai pu constater le sérieux des accompagnateurs. J'ai enfin trouvé une solution pour que mes enfants soient conduits en toute sécurité à leur activité. Merci Bana",
        },
        {
            'name': 'Ludovic',
            'short_bio': 'Papa de 2 enfants',
            'city': 'Tervuren',
            'full_description': "Super expérience avec Bana, j'ai très vite trouvé une solution au problème de déplacements de mes enfants",
        },
        {
            'name': 'Hélène',
            'short_bio': 'Maman de 1 enfant',
            'city': 'Anderlecht',
            'full_description': "Bana a rendu notre quotidien plus serein. Grâce à un service bien organisé et sécurisé, nous avons pu mieux concilier vie privée et vie professionnelle.",
        },
        {
            'name': 'Alexandre',
            'short_bio': 'Papa de 1 enfant',
            'city': 'Ham-Sur-Heure-Nalinnes',
            'full_description': "Merci pour ce service de qualité, j'ai la possibilité d'avoir plus de temps pour moi et mon enfant se fait de nouveaux amis, tout le monde est content !! Je recommande Bana à tous",
        },
        {
            'name': 'Cynthia',
            'short_bio': 'Maman solo de 2 enfants',
            'city': 'Charleroi',
            'full_description': "Service de qualité !",
        },
        {
            'name': 'Réginald',
            'short_bio': 'Papa de 1 enfant',
            'city': 'Watermael-Boitsfort',
            'full_description': "Les trajets de l'école au club de judo ensuite du club à la maison ne sont plus du tout un souci. Grâce à la communauté Bana j'ai trouvé la solution pour supprimer le stress des déplacements les jours où le travail prend trop de place !",
        },
        {
            'name': 'Isabel',
            'short_bio': 'Maman de 3 enfants',
            'city': 'Nivelles',
            'full_description': "Les accompagnatrices sont fiables, très gentilles et s'occupent soigneusement des enfants.",
        },
        {
            'name': 'Cédrick',
            'short_bio': 'Papa solo de 2 enfants',
            'city': 'Genval',
            'full_description': "Bana me donne plus de flexibilité dans mon quotidien, en libérant mon temps et en facilitant la vie de ma famille pour certains de nos besoins de déplacement spécifiques. C'est un réel plaisir !",
        },
    ]
    return render(request, 'work.html', {
        "work_benefits": work_benefits,
        "work_detail_steps": work_detail_steps,
        "work_journey_steps": work_journey_steps,
        "work_profiles": work_profiles,
    })

# --- Yaya page ---------------------------------------------------------------------------
def yaya(request):
    yaya_benefits = [
        {
            'img_src': 'bana/img/page/yaya/flexibilite.png',
            'title': _('Flexible'),
            'description': _('Engagement uniquement selon votre disponibilité')
        },
        {
            'img_src': 'bana/img/page/yaya/defraiement-1.png',
            'title': _('Défraiement'),
            'description': _('Recevez jusqu’à 176€/mois pour vos trajets quotidiens')
        },
        {
            'img_src': 'bana/img/page/yaya/sans-voiture-obligatoire.png',
            'title': _('Sans voiture obligatoire'),
            'description': _('Tous les moyens de transport sont utilisés')
        },
        {
            'img_src': 'bana/img/page/yaya/communautaire.png',
            'title': _('Communautaire'),
            'description': _('Créer du lien social dans votre quartier')
        }
    ]

    work_profiles = [
        {
            'name': 'Océane',
            'age': '20 ans',
            'short_bio': 'Étudiante en Puériculture',
            'city': 'Nivelles',
            'full_description': "J'avais déjà l'habitude de prendre le bus tous les jours pour rentrer chez moi après les cours. Avec Bana, je peux rendre ce trajet utile en accompagnant un enfant. C'est une expérience enrichissante, aussi bien humainement que dans le cadre de mes études.",
        },
        {
            'name': 'Timothé',
            'age': '23 ans',
            'short_bio': 'Étudiant en Kinésithérapie',
            'city': 'Louvain-La-Neuve',
            'full_description': "Je cherchais un job étudiant qui ait du sens et qui soit flexible. Accompagner un enfant quelques fois par semaine s'intègre parfaitement dans mon emploi du temps et j'ai le sentiment d'être vraiment utile.",
        },
        {
            'name': 'Meriem',
            'age': '34 ans',
            'short_bio': 'Enseignante',
            'city': 'Sint-Pieters-Leeuw',
            'full_description': "J'accompagne déjà des enfants toute la journée dans mon métier. Être Yaya est une façon de prolonger cet engagement en dehors de l'école et d'aider concrètement des familles de ma communauté.",
        },
        {
            'name': 'Guillaume',
            'age': '39 ans',
            'short_bio': 'Papa de 1 enfant',
            'city': 'La Louvière',
            'full_description': "Je dépose déjà mon fils à l'école tous les matins. Accompagner un deuxième enfant ne me prend que quelques minutes et cela rend un vrai service à une autre famille.",
        },
        {
            'name': 'Sofia',
            'age': '22 ans',
            'short_bio': 'Étudiante en Droit',
            'city': 'Ixelles',
            'full_description': "Entre les cours, les stages et les examens, j'avais besoin d'un job étudiant flexible. Avec Bana, je choisis les trajets qui correspondent à mon emploi du temps et je reçois un défraiement pour mon aide auprès des familles.",
        },
        {
            'name': 'Gaspard',
            'age': '19 ans',
            'short_bio': 'Étudiant en Éducation physique',
            'city': 'Woluwé-Saint-Pierre',
            'full_description': "Pour moi c'est mieux qu'un job étudiant parce que je les accompagne juste à vélo en allant coacher les U10 et je suis payé pour ce trajet plusieurs fois par semaine.",
        },
        {
            'name': 'Thi Minh',
            'age': '41 ans',
            'short_bio': 'Maman de 2 enfants',
            'city': 'Overijse',
            'full_description': "Bana me permet d'aider et de dépanner d'autres parents. J'apprécie particulièrement le concept collaboratif et communautaire de cette application.",
        },
        {
            'name': 'Lucie',
            'age': '15 ans',
            'short_bio': 'Étudiante en secondaire',
            'city': 'Nivelles',
            'full_description': "Être Yaya m'a permis de gagner en responsabilités. Les parents me font confiance et j'aime savoir que je peux accompagner des enfants à pied après les cours.",
        },
        {
            'name': 'Mehdi',
            'age': '24 ans',
            'short_bio': 'Étudiant en Ingénierie',
            'city': 'Mons',
            'full_description': "Je me déplace uniquement en bus et à pied. Bana m'a montré qu'on pouvait accompagner des enfants sans avoir de voiture. C'est une belle découverte.",
        },
        {
            'name': 'Françoise',
            'age': '67 ans',
            'short_bio': 'Jeune retraitée',
            'city': 'Waterloo',
            'full_description': "Depuis ma retraite, j'avais envie de rester active et de me sentir utile. Accompagner des enfants à pied quelques fois par semaine me permet de garder un rythme et de rester en forme.",
        },
        {
            'name': 'Yassine',
            'age': '18 ans',
            'short_bio': 'Étudiant en Communication',
            'city': 'Namur',
            'full_description': "Le défraiement est plutôt cool. Et ce qui me motive aussi c'est de savoir que j'aide une famille sans changer mes habitudes. Je fais simplement le trajet que je faisais déjà.",
        },
        {
            'name': 'Caroline',
            'age': '54 ans',
            'short_bio': 'Maman de 3 enfants',
            'city': 'Charleroi',
            'full_description': "Mes enfants sont maintenant plus grands, mais je me souviens combien j'étais inquiète lorsqu'ils devaient se déplacer seuls étant petits. En devenant Yaya, je peux aujourd'hui rassurer d'autres parents et leur donner un petit coup de pouce dans leur journée.",
        },
        {
            'name': 'Théodore',
            'age': '17 ans',
            'short_bio': "Étudiant en Technique d'animation",
            'city': 'Nalinnes',
            'full_description': "Moi j'adore partager mes trajets avec Liam. C'est devenu comme un petit frère. Ma maman est fière de moi en plus !",
        },
        {
            'name': 'Sarah',
            'age': '23 ans',
            'short_bio': 'Étudiante en Médecine',
            'city': 'Uccle',
            'full_description': "Je cherchais un moyen de gagner un peu d'argent à côté de mes études sans devoir sacrifier le peu de temps libre que j'ai. Avec Bana, je peux être utile, garder une certaine flexibilité et être défrayée pour des petits trajets au quotidien. En plus, les petits sont adorables !",
        },
        {
            'name': 'Matteo',
            'age': '46 ans',
            'short_bio': 'Papa solo de 3 enfants',
            'city': 'Laeken',
            'full_description': "Gérer les trajets des enfants seul, une semaine sur deux, est un vrai challenge avec le travail. Sur Bana, j'ai trouvé un autre parent avec qui partager les trajets. Ça me simplifie tellement la vie.",
        },
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
            'img_src': 'bana/img/page/tarifs/inscription.png',
            'title': _('Inscription gratuite'),
            'description': _("Parents et Yaya <br> s'inscrivent gratuitement"),
        },
        {
            'img_src': 'bana/img/page/tarifs/abonnement-payant.png',
            'title': _('Abonnement payant'),
            'description': _("Nécessaire pour découvrir <br> les matchings"),
        },
        {
            'img_src': 'bana/img/page/tarifs/defraiement-1.png',
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
        {'emoji': '🚗', 'icon': 'bana/img/page/about/trafic.png',      'text': 'Moins de trafic sur la route'},
        {'emoji': '🧒', 'icon': 'bana/img/page/about/autonomie.png',      'text': "Autonomie progressive des enfants"},
        {'emoji': '🧠', 'icon': 'bana/img/page/about/mental.png',         'text': 'Moins de charge mentale'},
        {'emoji': '🤝', 'icon': 'bana/img/page/about/communautaire.png',  'text': "Plus d'entraide communautaire"},
        {'emoji': '🌱', 'icon': 'bana/img/page/about/environnement.png',  'text': 'Impact environnemental concret'},
        {'emoji': '🔒', 'icon': 'bana/img/page/about/securite.png',       'text': 'Plus de sécurité autour des écoles'},
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
            'img_src': 'bana/img/page/about/nyota-profil-bana.jpg',
            'img_src_webp': 'bana/img/page/about/nyota-profil-bana.webp',
            'name': 'Nyota',
            'role': 'Fondatrice',
            'description': 'Entrepreneuriat social et mobilité, Nyota porte la vision communautaire de Bana.',
            'linkedin': 'https://www.linkedin.com/in/nyotadelecourt/',
            'instagram': '',
        },
        {
            'img_src': 'bana/img/page/about/luca-profil-bana.jpg',
            'img_src_webp': 'bana/img/page/about/luca-profil-bana.webp',
            'name': 'Luca',
            'role': 'Développeur IT',
            'description': 'Architecture et développement de la plateforme, du backend aux interfaces.',
            'linkedin': 'https://www.linkedin.com/in/luca-camilleri-487474332',
            'instagram': '',
        },
        {
            'img_src': 'bana/img/page/about/raph-profil-bana.jpg',
            'img_src_webp': 'bana/img/page/about/raph-profil-bana.webp',
            'name': 'Raphaël',
            'role': 'Développeur IT',
            'description': 'Innovation digitale et intégration des fonctionnalités clés de la plateforme.',
            'linkedin': 'https://www.linkedin.com/in/raphaeljonard/',
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
                "src": "/static/bana/img/icon/web-app-manifest-192x192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "/static/bana/img/icon/web-app-manifest-512x512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable"
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
        "Disallow: /trajects/",
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