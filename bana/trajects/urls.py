from django.urls import path
from . import views

urlpatterns = [
    path('', views.all_trajects, name='all_trajects'),
    path('search_trajects/', views.search_trajects, name='search_trajects'),
    #path('save_traject/', views.save_traject, name='save_traject'),
    path('proposed_traject/', views.proposed_traject, name='proposed_traject'),
    path('searched_traject/', views.searched_traject, name='searched_traject'),
    
]
