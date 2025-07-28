from django.urls import path
from . import views

urlpatterns = [
    # links :
    path('', views.profile, name='profile'),
    # connexion:
    path('login_user/', views.login_user, name='login'),
    path('logout_user/', views.logout_user, name='logout'),
    path('register_user/', views.register_user, name='register'),
    path('profile/<int:user_id>/', views.profile_user, name='profile_user'),
    path('profile/<int:user_id>/delete_review/', views.delete_review, name='delete_review'),
]
