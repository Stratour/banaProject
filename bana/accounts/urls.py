from django.urls import path
from . import views
from .views import CustomPasswordChangeView, CustomPasswordSetView

app_name='accounts'

urlpatterns = [
    path('logout/', views.logout_user, name='logout'),
    path('profil/mes-informations/', views.profile_view, name='profile'),
    path('profil/mes-informations/edit/', views.profile_edit, name='profile_edit'),
    path('profil/mes-enfants/', views.profile_children_view, name='profile_child'),
    path('profil/mes-enfants/ajouter-enfant/', views.add_child_view, name='add_child'),
    path('profil/mes-enfants/supprimer-enfant/<int:child_id>/', views.delete_child_view, name='delete_child'),
    path('profil/mes-adresses/', views.profile_addresses, name='profile_addresses'),
    path('profil/mes-adresses/ajouter-adresses/', views.create_address, name='create_address'),
    path('profil/mes-adresses/<uuid:uid>/supprimer-adresse/', views.delete_address, name='delete_address'),

    path('profil/utilisateur/<int:user_id>/', views.profile_user, name='profile_user'),
    path('profil/<int:user_id>/delete_review/', views.delete_review, name='delete_review'),
    
    ### HTMX ###
    path('profil/public/', views.profile_public, name='profile_public'),
    path('profil/info/', views.profile_info, name='profile_info'),
    path('profil/ecoles/recherche/', views.ecole_search, name='ecole_search'),
    
    path('profil/securité&connexion/', views.profile_security, name='profile_security'),
    path('profil/securité&connexion/password/', CustomPasswordChangeView.as_view(), name='account_change_password'),
    path('profil/securité&connexion/password/set/', CustomPasswordSetView.as_view(), name='account_set_password'),
    path('profil/securité&connexion/deactivate/', views.deactivate_account, name='deactivate_account'),

    path('email/edit/', views.email_edit, name='email_edit'),
    path('email/change/confirm/<str:key>/', views.email_change_confirm, name='email_change_confirm'),
]
