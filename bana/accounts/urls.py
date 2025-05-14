from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from . import views
from .views import CustomPasswordChangeView

app_name='accounts'

urlpatterns = [
    path('logout/', views.logout_user, name='logout'),
    path('profile/', views.profile_user, name='profile'),
    path('profile/overview/', views.profile_overview, name='profile_overview'),
    path('profile/update_user/', views.update_user, name='update_user'),
    path('password/change/', CustomPasswordChangeView.as_view(), name="account_change_password"),

]
