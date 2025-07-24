from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from . import views
from .views import CustomPasswordChangeView

app_name='accounts'

urlpatterns = [
    path('logout/', views.logout_user, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/public/', views.profile_public, name='profile_public'),
    path('profile/info/', views.profile_info, name='profile_info'),

    path('profile/enfant/', views.profile_children, name='profile_children'),
    path('profile/security/', views.profile_security, name='profile_security'),
    path('profile/security/password/', CustomPasswordChangeView.as_view(), name='account_change_password'),
    path('profile/security/deactivate/', views.deactivate_account, name='deactivate_account'),
    
    path('email/display/', views.email_display, name='email_display'),
    path('email/edit/', views.email_edit, name='email_edit'), 
    
    path('profil_child/', views.profile_children_view, name='profile_child'),
    path('add_child/', views.add_child_view, name='add_child'),
]
