from django.urls import path
from . import views

urlpatterns = [
    #path('', views.all_trajects, name='all_trajects'),
    path('autocomplete/', views.autocomplete_view, name='autocomplete'),
    #path('proposed_traject/<int:researchesTraject_id>', views.proposed_traject_views, name='proposed_traject'),
    path('proposed_traject/', views.proposed_traject, name='proposed_traject'),
    path('proposed/simple/', views.simple_proposed_traject, name='simple_proposed_traject'),
    path('researched_traject/', views.researched_traject, name='researched_traject'),

    path('proposed/mine/', views.my_proposed_trajects, name='my_proposed_trajects'),
    path('researched/mine/', views.my_researched_trajects, name='my_researched_trajects'),

    path('proposed/delete/<int:pk>', views.delete_proposed_traject, name='delete_proposed_traject'),
    path('researched/delete/<int:pk>', views.delete_researched_traject, name='delete_researched_traject'),

    path('matchings/parent/', views.my_matchings_researched, name='my_matchings_researched'),
    path('matchings/yaya/', views.my_matchings_proposed, name='my_matchings_proposed'),
    
    path('my_reserve/', views.my_reservations, name='my_reservations'),

    #path('modify/<int:id>/<str:type>/', views.modify_traject, name='modify_traject'),
    #path('reserve/<int:id>/', views.reserve_traject, name='reserve_traject'),
    # Dans urls.py
    #path('reserve/researched/<int:researchedTraject_id>/', views.reserve_trajectResearched, name='reserve_trajectResearched'),
    path('manage_reservation/<int:reservation_id>/<str:action>/', views.manage_reservation, name='manage_reservation'),
    
    #path('proposed/all/', views.all_proposed_trajects, name='all_proposed_trajects'),
    #path('researched/all/', views.all_researched_trajects, name='all_researched_trajects'),

    path('reservation/auto/<int:proposed_id>/<int:researched_id>/', views.auto_reserve, name='auto_reserve'),
]
