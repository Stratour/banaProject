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
    path("__reload__/", include("django_browser_reload.urls")),
    path('admin/', admin.site.urls),
    
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
    path('about/', views.about, name='about'),
    path('work/', views.work, name='work'),
    path('parent/', views.parent, name='parent'),
    path('welcome/', account_views.welcome, name="welcome"),

    # Admin Interfaces
    path('bana_admin/', include('bana_admin.urls')),
    
    # Bug Tracker
    path('bug_tracker/', include('bug_tracker.urls')),
    
    # Authentification
    path('accounts/', include('allauth.urls')),
    path('accounts/', include('accounts.urls')),

    # Applications
    path('trajects/', include('trajects.urls')),
    path('chat/', include('chat.urls')),
    path('', include('stripe_sub.urls')),
    
    # Définir si on veut le préfixe pour la langue par défaut
    prefix_default_language=True  # True = /fr/, False = pas de préfixe pour la langue par défaut
)

# Servir les fichiers médias en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)