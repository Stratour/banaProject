from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

from . import views
from accounts import views as account_views

urlpatterns = [ 
    path("__reload__/", include("django_browser_reload.urls")),
    path('admin/', admin.site.urls),

    # pages globales
    path('', views.home, name='home'),
    path('contact/', views.contact, name='contact'),
    path('about/', views.about, name='about'),
    path('work/', views.work, name='work'),
    path('parent/', views.parent, name='parent'),
    path('welcome/', account_views.welcome, name="welcome"),

    # changement de langue
    path('<str:lang_code>/', views.switch_language, name='switch_language'),

    # Admin Interfaces
    path('bana_admin/', include('bana_admin.urls')),
    # Bug Tracker
    path('bug_tracker/', include('bug_tracker.urls')),
    # Authentification
    path('accounts/', include('allauth.urls')),
    path('accounts/', include('accounts.urls')),

    path('trajects/', include('trajects.urls')),
    path('chat/', include('chat.urls')),
    path('', include('stripe_sub.urls')),
] 

# Servir les fichiers médias en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


