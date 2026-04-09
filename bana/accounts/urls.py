from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from . import views
from .views import CustomPasswordChangeView

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
    
    path('profil/security/', views.profile_security, name='profile_security'),
    path('profil/security/password/', CustomPasswordChangeView.as_view(), name='account_change_password'),
    path('profil/security/deactivate/', views.deactivate_account, name='deactivate_account'),
    
    path('email/display/', views.email_display, name='email_display'),
    path('email/edit/', views.email_edit, name='email_edit'), 
    path('email/change/confirm/<str:key>/', views.email_change_confirm, name='email_change_confirm'),
    path('email/confirm-redirect/', views.redirect_after_email_confirmation, name='email_confirm_redirect'),

    

]
