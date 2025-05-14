==================================

1. Installer la bibliothèque AllAuth :

$ pip install django-allauth # Django allauth simple

$ pip install django-allauth[socialaccount] # Django allauth avec réseaux sociaux

===============================================================

2. Dans INSTALLED_APPS, mettre le nom de l'application avant 'allauth' :

INSTALLED_APPS = [
    ...
    'accounts', # Nom de l'application

    'allauth',
    'allauth.account',
    'allauth.socialaccount', # Pour la connexion via les réseaux sociaux
    'allauth.socialaccount.providers.google', # Pour la connexion via Google (changer Google par le réseau adéquat)
     ...
]

MIDDLEWARE = (
    # Add the account middleware:
    "allauth.account.middleware.AccountMiddleware",
)

Plus d'infos : https://docs.allauth.org/en/latest/installation/quickstart.html

===============================================================

3. Dans le fichier urls.py du projet principal ajouter les chemins de l'app :

    path('accounts/', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),

===============================================================

4. Ajouter dans la barre de navigation (navbar) :

    {% if user.is_authenticated %}
    <li><a href="{% url 'accounts:profile' %}"><i class="bi bi-person-circle navicon"></i>Profil</a></li>
      <li><a href="{% url 'accounts:logout' %}"><i class="bi bi-box-arrow-in-left navicon"></i>Déconnexion</a></li>
    {% else %}
      <li><a href="{% url 'account_login' %}"><i class="bi bi-person-fill navicon"></i> Connexion</a></li>
      <li><a href="{% url 'account_signup' %}"><i class="bi bi-pencil-square navicon"></i> Inscription</a></li>
    {% endif %}

===============================================================

5. Vérifiez le chemin vers votre base.html :

Dans '/accounts/templates/allauth/layouts/base.html' mettre la redirection de votre 'base.html' du projet principal

===============================================================

6. Pour l'affichage de profile.html :

Ajouter la bibliothèque HTMX : pip install django-htmx

INSTALLED_APPS = [
    ...,
    "django_htmx",
    ...,
]

MIDDLEWARE = [
    ...,
    "django_htmx.middleware.HtmxMiddleware",
    ...,
]

Dans le fichier 'base.html' du projet principal ajouter : <script src="https://unpkg.com/htmx.org@2.0.3/dist/htmx.js" integrity="sha384-BBDmZzVt6vjz5YbQqZPtFZW82o8QotoM7RUp5xOxV3nSJ8u2pSdtzFAbGKzTlKtg" crossorigin="anonymous"></script>

========================================

7. Configuration des fichiers CSS /!\ si le projet est un template Bootstrap :

Ajouter "@import 'chemin-du-fichier ./_accounts.scss';" dans le fichier '/static/main.scss' du projet principal

=======================================

8. Plus d'option dans le setting.py :

