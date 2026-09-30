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
            'highlight': True,
            'badge': _('Seule formule disponible'),
            'available': True,
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
            'highlight': False,
            'badge': _('Bientôt disponible'),
            'available': False,
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
            'badge': _('Bientôt disponible'),
            'available': False,
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

# --- FAQ page ---------------------------------------------------------------------------
def faq(request):
    faq_categories = [
        {
            'slug': 'bana-mobi',
            'label': _('Bana Mobi'),
            'questions': [
                {
                    'question': _("Qu'est-ce que Bana Mobi ?"),
                    'answer': _("<p>Bana Mobi est une plateforme qui facilite les trajets des enfants entre la maison, l'école et les activités extrascolaires grâce à un réseau de personnes de confiance appelées les Yaya.</p>"),
                    'featured': True,
                },
                {
                    'question': _('Comment fonctionne Bana ?'),
                    'answer': _("<p>Bana met en relation des parents qui recherchent une solution pour les trajets de leurs enfants avec des Yaya qui effectuent des trajets similaires aux mêmes horaires.</p>\n<p>Bana facilite la mise en relation. Les parents et les Yaya organisent ensuite ensemble les modalités de leurs trajets.</p>"),
                    'featured': True,
                },
                {
                    'question': _('Qui sont les Yaya ?'),
                    'answer': _("<p>Les Yaya sont des personnes de confiance au profil vérifié qui accompagnent les enfants sur leurs trajets du quotidien.</p>\n<p>Il peut s'agir d'étudiants, de parents, de coachs sportifs, d'animateurs, d'infirmières ou d'autres membres de la communauté.</p>"),
                    'featured': True,
                },
                {
                    'question': _("Quels types de trajets peut-on organiser avec Bana ?"),
                    'answer': _("<p>Bana permet d'organiser les trajets entre la maison, l'école, la garderie et les activités extrascolaires.</p>\n<p>Les trajets peuvent être réguliers ou ponctuels, selon les besoins de la famille et les disponibilités des Yaya.</p>"),
                },
                {
                    'question': _('Quels moyens de transport peuvent être utilisés ?'),
                    'answer': _("<p>Les trajets peuvent être effectués :</p>\n<ul><li>à pied</li><li>à vélo</li><li>en transports en commun</li><li>en covoiturage</li></ul>\n<p>L'utilisation d'une trottinette électrique pour accompagner un enfant est interdite.</p>"),
                },
                {
                    'question': _('Bana est-il un service de taxi ou de chauffeur privé ?'),
                    'answer': _("<p>Non. Bana est une plateforme de mobilité partagée.</p>\n<p>Les Yaya ne sont pas des chauffeurs professionnels : ils accompagnent les enfants dans le cadre de trajets qu'ils effectuent ou peuvent intégrer à leurs déplacements.</p>"),
                },
                {
                    'question': _('Dans quelles régions Bana est-il disponible ?'),
                    'answer': _("<p>Bana se développe progressivement en fonction des familles et des Yaya inscrits dans chaque zone.</p>\n<p>La disponibilité dépend donc du nombre de trajets encodés et de la présence de membres compatibles à proximité.</p>"),
                },
            ],
        },
        {
            'slug': 'inscription-matching',
            'label': _('Inscription & matching'),
            'questions': [
                {
                    'question': _("L'inscription sur Bana est-elle gratuite ?"),
                    'answer': _("<p>Oui. Parents et Yaya peuvent s'inscrire gratuitement, créer leur profil et encoder leurs trajets.</p>\n<p>Vous ne passez à l'abonnement que lorsqu'un matching est disponible et que vous souhaitez entrer en contact avec un membre de la communauté.</p>"),
                    'featured': True,
                },
                {
                    'question': _("Combien de temps faut-il pour s'inscrire ?"),
                    'answer': _("<p>La création du compte ne prend que quelques minutes.</p>\n<p>Vous pouvez ensuite compléter votre profil et encoder les trajets que vous recherchez ou proposez.</p>"),
                },
                {
                    'question': _('Comment fonctionne le système de matching ?'),
                    'answer': _("<p>Bana recherche les trajets compatibles entre les besoins encodés par les parents et les trajets proposés par les Yaya.</p>\n<p>Le matching tient notamment compte des lieux, des horaires et des caractéristiques du trajet.</p>"),
                    'featured': True,
                },
                {
                    'question': _("Que se passe-t-il si aucun matching n'est disponible ?"),
                    'answer': _("<p>Vous pouvez conserver gratuitement votre profil et vos trajets sur la plateforme.</p>\n<p>Si un nouveau Yaya ou une nouvelle famille encode ultérieurement un trajet compatible, un matching pourra alors apparaître.</p>"),
                },
                {
                    'question': _("Dois-je payer même si aucun matching n'existe ?"),
                    'answer': _("<p>Non.</p>\n<p>L'inscription et l'encodage des trajets restent gratuits. Vous passez à l'abonnement uniquement lorsqu'un matching existe et que vous souhaitez entrer en contact avec le membre concerné.</p>"),
                },
                {
                    'question': _('Comment entrer en contact avec un matching ?'),
                    'answer': _("<p>Une fois votre abonnement activé, vous avez accès à l'adresse email de vos matchings afin de pouvoir échanger et organiser les trajets.</p>\n<p>Vous pouvez ensuite partager vos coordonnées téléphoniques pour communiquer plus facilement.</p>"),
                },
                {
                    'question': _('Puis-je choisir le Yaya qui accompagnera mon enfant ?'),
                    'answer': _("<p>Oui.</p>\n<p>Le parent choisit toujours la personne avec laquelle il souhaite entrer en contact et à laquelle il souhaite confier son enfant parmi les profils compatibles proposés sur Bana.</p>"),
                },
                {
                    'question': _('Un matching signifie-t-il que le trajet est automatiquement accepté ?'),
                    'answer': _("<p>Non.</p>\n<p>Un matching signifie simplement que les trajets semblent compatibles. Le parent et le Yaya doivent ensuite échanger pour vérifier leurs disponibilités, leurs attentes et les modalités du trajet.</p>"),
                },
            ],
        },
        {
            'slug': 'trajets-organisation',
            'label': _('Trajets & organisation'),
            'questions': [
                {
                    'question': _('Comment se déroule le premier contact avec un Yaya ?'),
                    'answer': _("<p>Avant le premier trajet, une rencontre entre le parent, l'enfant et le Yaya est fortement recommandée afin de faire connaissance et de préparer le trajet en toute confiance.</p>\n<p>Bana recommande également d'effectuer le premier trajet en présence du parent afin de présenter le parcours au Yaya et de permettre à l'enfant de se familiariser progressivement avec cette nouvelle organisation.</p>"),
                    'featured': True,
                },
                {
                    'question': _('Comment se passe un trajet ?'),
                    'answer': _("<p>Le Yaya récupère l'enfant auprès d'un adulte responsable, l'accompagne jusqu'à destination puis le confie à l'adulte désigné par le parent.</p>\n<p>L'enfant est accompagné pendant toute la durée du trajet.</p>"),
                },
                {
                    'question': _('Comment suis-je informé pendant le trajet ?'),
                    'answer': _("<p>Le parent reçoit un message lorsque le Yaya prend l'enfant en charge et un second message lorsque l'enfant arrive à destination.</p>"),
                },
                {
                    'question': _('À qui le Yaya peut-il confier mon enfant à l\'arrivée ?'),
                    'answer': _("<p>L'enfant doit être remis à l'adulte désigné par le parent selon les consignes convenues avant le trajet.</p>\n<p>Il peut s'agir par exemple d'un parent, d'un enseignant, d'un éducateur, d'un coach ou d'un autre adulte autorisé.</p>"),
                },
                {
                    'question': _('Les trajets peuvent-ils être ponctuels ?'),
                    'answer': _("<p>Oui.</p>\n<p>Selon les disponibilités des Yaya, un trajet peut être organisé de manière ponctuelle ou récurrente.</p>"),
                },
                {
                    'question': _('Les trajets doivent-ils toujours se faire en voiture ?'),
                    'answer': _("<p>Non.</p>\n<p>Bana encourage une mobilité multimodale. Selon le trajet et l'âge de l'enfant, l'accompagnement peut se faire à pied, à vélo, en transports en commun ou en covoiturage.</p>"),
                },
                {
                    'question': _('Peut-on combiner plusieurs moyens de transport sur un même trajet ?'),
                    'answer': _("<p>Oui.</p>\n<p>Un trajet peut par exemple combiner la marche et les transports en commun si cette solution est adaptée au parcours et à l'enfant.</p>"),
                },
                {
                    'question': _("Combien d'enfants un Yaya peut-il accompagner ?"),
                    'answer': _("<p>Un Yaya peut accompagner maximum 4 enfants à la fois.</p>\n<p>Cette limite vise à garantir une attention suffisante à chaque enfant et des conditions de trajet adaptées.</p>"),
                },
                {
                    'question': _("Que se passe-t-il en cas d'annulation ou d'imprévu ?"),
                    'answer': _("<p>Le parent et le Yaya doivent se prévenir mutuellement dès que possible.</p>\n<p>Les modalités d'annulation et d'organisation sont convenues directement entre eux dans le respect des engagements pris.</p>"),
                },
                {
                    'question': _('Puis-je demander au même Yaya d\'accompagner régulièrement mon enfant ?'),
                    'answer': _("<p>Oui, si le Yaya est disponible et que l'organisation convient aux deux parties.</p>\n<p>Une relation régulière peut d'ailleurs favoriser la confiance et créer des repères rassurants pour l'enfant.</p>"),
                },
            ],
        },
        {
            'slug': 'confiance-securite-assurance',
            'label': _('Confiance, sécurité & assurance'),
            'questions': [
                {
                    'question': _('Comment Bana vérifie-t-il les Yaya ?'),
                    'answer': _("<p>Les Yaya doivent faire vérifier leur identité et fournir un extrait de casier judiciaire modèle 596-2, destiné aux activités impliquant des mineurs.</p>\n<p>Ces vérifications constituent un prérequis pour rejoindre la communauté en tant que Yaya vérifié.</p>"),
                    'featured': True,
                },
                {
                    'question': _('Comment puis-je savoir si je peux faire confiance à un Yaya ?'),
                    'answer': _("<p>La confiance repose sur plusieurs éléments :</p>\n<ul><li>la vérification du profil</li><li>les évaluations laissées par la communauté</li><li>les échanges avec le Yaya</li><li>la rencontre organisée avant le premier trajet</li></ul>\n<p>Le parent reste toujours décisionnaire quant au choix de la personne qui accompagnera son enfant.</p>"),
                },
                {
                    'question': _('La rencontre avant le premier trajet est-elle importante ?'),
                    'answer': _("<p>Oui.</p>\n<p>Elle permet au parent, à l'enfant et au Yaya de faire connaissance, de vérifier que chacun se sent à l'aise et de clarifier l'organisation du trajet.</p>"),
                },
                {
                    'question': _("Comment fonctionne le système d'avis et d'évaluations ?"),
                    'answer': _("<p>Après les trajets, parents et Yaya peuvent partager leur expérience.</p>\n<p>Les évaluations permettent notamment de valoriser la ponctualité, la fiabilité, la communication et le respect des engagements.</p>\n<p>Elles aident ainsi les membres à choisir leurs futurs matchings en s'appuyant sur l'expérience de la communauté.</p>"),
                },
                {
                    'question': _('Pourquoi les parents sont-ils également évalués ?'),
                    'answer': _("<p>Chez Bana, la confiance fonctionne dans les deux sens.</p>\n<p>Les Yaya peuvent eux aussi évaluer les parents, notamment sur la ponctualité, la communication et le respect des engagements.</p>\n<p>Ce système réciproque contribue à créer une communauté équilibrée, transparente et respectueuse pour tous.</p>"),
                },
                {
                    'question': _('Les Yaya sont-ils assurés pendant les trajets ?'),
                    'answer': _("<p>Oui. Une assurance est prévue pour les Yaya pendant les accompagnements organisés via Bana, selon les conditions applicables au service.</p>"),
                },
                {
                    'question': _('Mon enfant est-il assuré pendant le trajet ?'),
                    'answer': _("<p>Bana prévoit également des solutions d'assurance pour les enfants selon la formule ou les options choisies.</p>\n<p>Les conditions exactes sont précisées lors de l'inscription et dans les informations contractuelles.</p>"),
                },
                {
                    'question': _("Que se passe-t-il en cas d'incident pendant un trajet ?"),
                    'answer': _("<p>Le Yaya doit assurer en priorité la sécurité de l'enfant et prévenir immédiatement le parent.</p>\n<p>En cas de situation nécessitant une aide urgente, les services d'urgence doivent être contactés sans délai.</p>"),
                },
                {
                    'question': _("Bana garantit-il qu'aucun incident ne peut survenir ?"),
                    'answer': _("<p>Aucun service ne peut garantir un risque zéro.</p>\n<p>Bana met néanmoins en place plusieurs mesures pour renforcer la sécurité : vérification des profils, rencontre préalable, évaluations, consignes de trajet et règles de bonne conduite.</p>"),
                },
                {
                    'question': _('Existe-t-il une charte de bonne conduite ?'),
                    'answer': _("<p>Oui.</p>\n<p>Les membres de la communauté s'engagent à respecter des principes essentiels comme la sécurité des enfants, la ponctualité, la fiabilité, la communication claire et le respect mutuel.</p>"),
                },
            ],
        },
        {
            'slug': 'tarifs-defraiements',
            'label': _('Tarifs & défraiements'),
            'questions': [
                {
                    'question': _('Quand dois-je payer un abonnement ?'),
                    'answer': _("<p>L'inscription et l'encodage des trajets sont gratuits.</p>\n<p>Vous payez uniquement lorsqu'un matching est disponible et que vous souhaitez accéder aux coordonnées du membre afin d'entrer en contact avec lui.</p>"),
                    'featured': True,
                },
                {
                    'question': _("Que comprend l'abonnement Bana ?"),
                    'answer': _("<p>L'abonnement permet notamment d'accéder aux matchings disponibles et aux coordonnées nécessaires pour entrer en contact avec les membres compatibles.</p>"),
                },
                {
                    'question': _("Le prix des trajets est-il compris dans l'abonnement ?"),
                    'answer': _("<p>Non.</p>\n<p>L'abonnement concerne l'accès à la plateforme et aux matchings. Les trajets font ensuite l'objet d'un défraiement distinct, versé directement par le parent au Yaya.</p>"),
                },
                {
                    'question': _('Le prix des trajets est-il fixé par Bana ?'),
                    'answer': _("<p>Non.</p>\n<p>Le défraiement est librement convenu entre le parent et le Yaya avant le début des trajets.</p>\n<p>Bana propose uniquement des montants indicatifs afin de préserver un équilibre entre l'accessibilité pour les familles et la reconnaissance du temps et de la responsabilité assumée par les Yaya.</p>"),
                },
                {
                    'question': _('Quel défraiement Bana recommande-t-il ?'),
                    'answer': _("<p>À titre indicatif :</p>\n<ul><li>moins de 10 minutes : environ 3 € par enfant</li><li>de 10 à 20 minutes : 4 à 5 € par enfant</li><li>de 20 à 30 minutes : 5 à 7 € par enfant</li></ul>\n<p>Le montant définitif reste librement convenu entre le parent et le Yaya.</p>"),
                    'featured': True,
                },
                {
                    'question': _('Pourquoi le défraiement est-il calculé par enfant ?'),
                    'answer': _("<p>Chaque enfant accompagné représente une responsabilité et nécessite l'attention du Yaya.</p>\n<p>Le montant indicatif est donc exprimé par enfant et par trajet.</p>"),
                },
                {
                    'question': _('Que couvre le défraiement ?'),
                    'answer': _("<p>Le défraiement reconnaît :</p>\n<ul><li>le temps consacré à l'accompagnement</li><li>la responsabilité liée à la prise en charge de l'enfant</li><li>les éventuels frais liés au déplacement</li></ul>"),
                },
                {
                    'question': _('Le défraiement dépend-il du moyen de transport ?'),
                    'answer': _("<p>Non.</p>\n<p>Le principe de défraiement reste le même que le trajet soit effectué à pied, à vélo, en transports en commun ou en covoiturage.</p>"),
                },
                {
                    'question': _('Bana intervient-il dans le paiement des trajets ?'),
                    'answer': _("<p>Non.</p>\n<p>Le défraiement est versé directement par le parent au Yaya selon les modalités convenues entre eux.</p>\n<p>Bana n'intervient ni dans la fixation du montant définitif ni dans son paiement.</p>"),
                },
                {
                    'question': _('À quelle fréquence dois-je payer le Yaya ?'),
                    'answer': _("<p>La fréquence du paiement est convenue directement entre le parent et le Yaya.</p>\n<p>Il peut par exemple être effectué après chaque trajet ou de manière hebdomadaire.</p>"),
                },
                {
                    'question': _('Dois-je payer si un trajet est annulé ?'),
                    'answer': _("<p>Les modalités sont à convenir entre le parent et le Yaya avant de commencer les trajets.</p>\n<p>Pour les trajets réguliers, Bana recommande de clarifier dès le départ les règles applicables en cas d'annulation afin d'éviter tout malentendu.</p>"),
                },
            ],
        },
        {
            'slug': 'devenir-yaya',
            'label': _('Devenir Yaya'),
            'questions': [
                {
                    'question': _('Qui peut devenir Yaya ?'),
                    'answer': _("<p>Toute personne responsable et fiable âgée d'au moins 15 ans peut proposer ses trajets sur Bana, sous réserve de satisfaire aux conditions de vérification de la plateforme.</p>\n<p>Il n'est pas nécessaire d'être étudiant ni de posséder une voiture.</p>"),
                    'featured': True,
                },
                {
                    'question': _("Quel est le statut d'un Yaya ?"),
                    'answer': _("<p>Un Yaya effectue les trajets sous le statut de bénévole.</p>\n<p>Il ne s'agit ni d'un emploi, ni d'un job étudiant, ni d'un flexi-job, ni d'une activité indépendante.</p>"),
                },
                {
                    'question': _('Dois-je avoir une voiture pour devenir Yaya ?'),
                    'answer': _("<p>Non.</p>\n<p>Vous pouvez devenir Yaya si vous vous déplacez à pied, à vélo, en transports en commun ou en voiture.</p>"),
                },
                {
                    'question': _('Quel défraiement puis-je recevoir en tant que Yaya ?'),
                    'answer': _("<p>Chaque trajet peut donner lieu à un défraiement convenu directement avec le parent.</p>\n<p>Le montant dépend notamment de la durée du trajet et du nombre d'enfants accompagnés, dans le respect des plafonds légaux applicables au volontariat.</p>"),
                },
                {
                    'question': _('Comment sont calculés les défraiements ?'),
                    'answer': _("<p>À titre indicatif :</p>\n<ul><li>moins de 10 minutes : environ 3 € par enfant</li><li>de 10 à 20 minutes : 4 à 5 € par enfant</li><li>de 20 à 30 minutes : 5 à 7 € par enfant</li></ul>\n<p>Le montant est toujours convenu avec le parent avant le début des trajets.</p>"),
                },
                {
                    'question': _('Dois-je m\'engager sur des trajets réguliers ?'),
                    'answer': _("<p>Non.</p>\n<p>Être Yaya reste flexible. Vous choisissez les trajets que vous souhaitez proposer et n'acceptez que ceux qui correspondent à vos déplacements habituels et à vos disponibilités.</p>"),
                },
                {
                    'question': _('Puis-je être Yaya uniquement de temps en temps ?'),
                    'answer': _("<p>Oui.</p>\n<p>Vous pouvez proposer des trajets réguliers ou ponctuels selon votre emploi du temps.</p>"),
                },
                {
                    'question': _("Dois-je avoir de l'expérience avec les enfants ?"),
                    'answer': _("<p>Il n'est pas nécessaire d'avoir une expérience professionnelle dans le secteur de l'enfance.</p>\n<p>En revanche, le Yaya doit être responsable, attentif, fiable et à l'aise avec l'accompagnement des enfants.</p>"),
                },
                {
                    'question': _('Quelles vérifications dois-je effectuer pour devenir Yaya ?'),
                    'answer': _("<p>Vous devez notamment faire vérifier votre identité et fournir un extrait de casier judiciaire modèle 596-2.</p>\n<p>D'autres informations peuvent également être demandées afin de compléter votre profil.</p>"),
                },
                {
                    'question': _('Puis-je choisir les familles avec lesquelles je souhaite effectuer des trajets ?'),
                    'answer': _("<p>Oui.</p>\n<p>Comme les parents, les Yaya restent libres d'accepter ou non un matching.</p>\n<p>La mise en relation doit convenir aux deux parties.</p>"),
                },
                {
                    'question': _('Pourquoi les parents peuvent-ils m\'évaluer ?'),
                    'answer': _("<p>Les évaluations permettent aux futurs parents de mieux connaître l'expérience des autres membres avec vous.</p>\n<p>La ponctualité, la communication, la fiabilité et le respect des engagements contribuent progressivement à construire votre réputation sur Bana.</p>"),
                },
                {
                    'question': _('Puis-je également évaluer les parents ?'),
                    'answer': _("<p>Oui.</p>\n<p>Le système d'évaluation est réciproque afin que les Yaya puissent eux aussi partager leur expérience et choisir leurs futurs matchings en connaissance de cause.</p>"),
                },
                {
                    'question': _('Pourquoi devenir Yaya ?'),
                    'answer': _("<p>Parce qu'un déplacement du quotidien peut aussi devenir un geste d'entraide.</p>\n<p>En accompagnant un enfant, vous soutenez une famille de votre quartier, contribuez à sécuriser ses déplacements et participez à une mobilité plus locale, intergénérationnelle et partagée.</p>"),
                },
            ],
        },
        {
            'slug': 'a-propos',
            'label': _('À propos de Bana'),
            'questions': [
                {
                    'question': _('Que signifie le nom "Bana" ?'),
                    'answer': _("<p>« Bana » est un mot en lingala qui signifie « enfants ».</p>\n<p>Nous avons choisi ce nom parce qu'il est court, facile à retenir et qu'il représente le cœur de notre activité : les enfants.</p>"),
                },
                {
                    'question': _('Pourquoi Bana a-t-il été créé ?'),
                    'answer': _("<p>Bana a été créé pour faciliter la vie des familles, alléger la charge mentale et logistique des parents et permettre aux enfants de participer plus sereinement à leurs activités scolaires et extrascolaires.</p>"),
                },
                {
                    'question': _('Quelle est la mission de Bana ?'),
                    'answer': _("<p>Bana souhaite développer une nouvelle culture de la mobilité scolaire : plus partagée, plus douce, plus responsable et plus solidaire.</p>\n<p>La plateforme contribue également à aider les enfants à développer progressivement leur autonomie dans leurs déplacements.</p>"),
                },
                {
                    'question': _('Quel est l\'impact social de Bana ?'),
                    'answer': _("<p>Bana encourage l'entraide locale et intergénérationnelle et crée du lien entre les familles et les personnes de confiance de leur quartier.</p>\n<p>La plateforme aide également les parents à mieux concilier leur vie familiale, professionnelle et les activités de leurs enfants.</p>"),
                },
                {
                    'question': _('Quel est l\'impact environnemental de Bana ?'),
                    'answer': _("<p>En encourageant la marche, le vélo, les transports en commun et le covoiturage, Bana favorise une mobilité plus durable et contribue à réduire la dépendance à la voiture individuelle pour les trajets des enfants.</p>"),
                },
            ],
        },
    ]
    for category in faq_categories:
        category['has_featured'] = any(q.get('featured') for q in category['questions'])
    return render(request, 'faq.html', {'faq_categories': faq_categories})

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
        # Routes sous i18n_patterns (prefix_default_language=True) : servies sous /fr/, /en/, /nl/,
        # jamais à la racine -> wildcard /*/ pour matcher le préfixe de langue quel qu'il soit.
        "Disallow: /*/accounts/login/",
        "Disallow: /*/accounts/signup/",
        "Disallow: /*/accounts/password/",
        "Disallow: /*/accounts/email/",
        "Disallow: /*/accounts/confirm-email/",
        "Disallow: /*/accounts/social/",
        "Disallow: /*/accounts/reauthenticate/",
        "Disallow: /*/accounts/3rdparty/",
        "Disallow: /*/bana_admin/",
        "Disallow: /*/bug_tracker/",
        "Disallow: /*/trajets/",
        "Disallow: /*/chat/",
        "Disallow: /*/profil/",
        # Routes hors i18n_patterns : servies telles quelles, sans préfixe de langue.
        "Disallow: /admin/",
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