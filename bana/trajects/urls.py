from django.urls import path
from . import views

urlpatterns = [
    path('', views.all_trajects, name='all_trajects'),
    path('autocomplete/', views.autocomplete_view, name='autocomplete'),
    path('proposed_traject/<int:researchesTraject_id>', views.proposed_traject, name='proposed_traject'),
    path('proposed_traject/', views.proposed_traject, name='proposed_traject'),

    path('searched_traject/', views.searched_traject, name='searched_traject'),
    path('delete/<int:id>/<str:type>/', views.delete_traject, name='delete_traject'),
    path('modify/<int:id>/<str:type>/', views.modify_traject, name='modify_traject'),
    path('reserve/<int:id>/', views.reserve_traject, name='reserve_traject'),
    
]
