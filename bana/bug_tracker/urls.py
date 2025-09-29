# urls.py
from django.urls import path
from . import views

app_name = 'bug_tracker'

print('================ bug_tracker_urls.py :: ')
urlpatterns = [
    #path('', views.bug_tracker, name='bug_tracker'),
    # Vues principales
    path('', views.bug_list, name='bug_list'),
    path('dashboard/', views.bug_stats, name='dashboard'),
    path('bug_stats/', views.bug_stats, name='bug_stats'),
    path('create/', views.bug_create, name='bug_create'),
    path('<int:pk>/', views.bug_detail, name='bug_detail'),
    path('<int:pk>/edit/', views.bug_edit, name='bug_edit'),
    
    # Actions HTMX
    path('<int:pk>/status/', views.bug_status_update, name='bug_status_update'),
    path('<int:pk>/assign/', views.bug_assign, name='bug_assign'),
    path('<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('<int:pk>/upload/', views.upload_attachment, name='upload_attachment'),
]


## 🎯 URLs et Navigation
# Dashboard : `/` - Vue d'ensemble avec statistiques
# Liste des bugs : `/bugs/` - Liste paginée avec filtres
# Nouveau bug : `/create/` - Formulaire de création
# Détail bug : `/<id>/` - Vue détaillée avec commentaires
# Admin : `/admin/` - Interface d'administration Django

