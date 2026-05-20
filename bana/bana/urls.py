from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from stripe_sub.views import stripe_webhook
from . import views
from accounts import views as account_views

# URLs sans préfixe de langue (utilitaires)
urlpatterns = [
    path('admin/', admin.site.urls),

    # PWA
    path('manifest.json', views.manifest, name='manifest'),
    path('sw.js', views.service_worker, name='service_worker'),
    path('offline/', views.offline, name='offline'),

    # 🚨 Webhook Stripe déclaré en dehors de i18n_patterns
    path("webhook/stripe/", stripe_webhook, name="stripe_webhook"),

    # Vue pour changer de langue
    path('switch-language/<str:language>/', views.switch_language, name='switch_language'),

    # URL Django pour changement de langue (optionnel, en plus)
    path('i18n/', include('django.conf.urls.i18n')),
]

# URLs avec préfixes de langue (/fr/, /en/, etc.)
urlpatterns += i18n_patterns(
    # Pages globales
    path('', views.home, name='home'),
    path('contact/', views.contact, name='contact'),
    path('mission/', views.about, name='about'),
    path('comment-ca-marche/', views.work, name='work'),
    path('parent/', views.parent, name='parent'),
    path('devenir-yaya/', views.yaya, name='yaya'),
    path('tarifs/', views.tarifs, name='tarifs'),

    # Admin Interfaces
    path('bana_admin/', include('bana_admin.urls')),
    
    # Bug Tracker
    path('bug_tracker/', include('bug_tracker.urls')),
    
    # Authentification
    path('accounts/', include('allauth.urls')),
    path('', include('accounts.urls')),

    # Applications
    path('trajets/', include('trajects.urls')),
    path('chat/', include('chat.urls')),
    path('profil/', include('stripe_sub.urls')),
    
    # Définir si on veut le préfixe pour la langue par défaut
    prefix_default_language=True  # True = /fr/, False = pas de préfixe pour la langue par défaut
)

# Servir les fichiers médias en développement
if settings.DEBUG:
    urlpatterns += [path("__reload__/", include("django_browser_reload.urls"))]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)