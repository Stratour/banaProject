from django.urls import path
from . import views

urlpatterns = [
    #path('', views.all_trajects, name='all_trajects'),
    path('autocomplete/', views.autocomplete_view, name='autocomplete'),
    #path('proposed_traject/<int:researchesTraject_id>', views.proposed_traject_views, name='proposed_traject'),
    
    ###### Parents #####
    path('recherches/nouvelles-recherches', views.researched_traject, name='researched_traject'),
    path('recherches/mes-recherches/', views.my_researched_trajects, name='my_researched_trajects'),
    path('recherches/mes-recherches/<uuid:groupe_uid>/', views.my_researched_groupe_detail, name='my_researched_groupe_detail'),
    path('recherches/mes-recherches/delete/<uuid:groupe_uid>/', views.delete_researched_groupe, name='delete_researched_groupe'),
    path('recherches/mes-recherches/<uuid:groupe_uid>/delete/<int:pk>', views.delete_researched_traject, name='delete_researched_traject'),
    path('recherches/matchings/', views.my_matchings_researched, name='my_matchings_researched'),
    path('recherches/matchings/<uuid:researched_groupe_uid>/<uuid:proposed_groupe_uid>/<int:matched_user_id>/', views.my_matchings_researched_detail, name='my_matchings_researched_detail'),
    
    ##### Parents / Yaya #####
    path('propositions/nouveaux-trajets/', views.proposed_traject, name='proposed_traject'),
    path('propositions/mes-trajets/', views.my_proposed_trajects, name='my_proposed_trajects'),
    path('propositions/mes-trajets/<uuid:groupe_uid>/', views.my_proposed_groupe_detail, name='my_proposed_groupe_detail'),
    path('propositions/delete/<uuid:groupe_uid>/', views.delete_proposed_groupe, name='delete_proposed_groupe'),
    path('propositions/<uuid:groupe_uid>/delete/<int:pk>', views.delete_proposed_traject, name='delete_proposed_traject'),
    path('propositions/matchings/', views.my_matchings_proposed, name='my_matchings_proposed'),
    path('propositions/matchings/<uuid:proposed_groupe_uid>/<uuid:researched_groupe_uid>/<int:parent_user_id>/', views.my_matchings_proposed_detail, name='my_matchings_proposed_detail'),

    ##### Yaya #####
    path('recherches-rayon/nouvelles-recherches/', views.simple_proposed_traject, name='simple_proposed_traject'),
    path('recherches-rayon/mes-recherches/', views.my_simple_trajects, name='my_simple_trajects'),
    path('recherches-rayon/mes-recherches/<uuid:groupe_uid>/', views.my_simple_groupe_detail, name='my_simple_groupe_detail'),
    path('recherches-rayon/mes-recherches/delete/<uuid:groupe_uid>/', views.delete_simple_groupe, name='delete_simple_groupe'),
    path('recherches-rayon/mes-recherches/<uuid:groupe_uid>/delete/<int:pk>', views.delete_simple_traject, name='delete_simple_traject'),
    path('recherches-rayon/matchings/', views.my_matchings_simple, name='my_matchings_simple'),
    path('recherches-rayon/matchings/<uuid:proposed_groupe_uid>/<uuid:researched_groupe_uid>/<int:parent_user_id>/', views.my_matchings_simple_detail, name='my_matchings_simple_detail'),


    path('réservations/', views.my_reservations, name='my_reservations'),
    path('réservations/made/<uuid:researched_groupe_uid>/<uuid:proposed_groupe_uid>/<int:matched_user_id>', views.my_reservations_made_detail, name='my_reservations_made_detail'),
    path('réservations/reçue/<uuid:proposed_groupe_uid>/', views.my_reservations_received_detail, name='my_reservations_received_detail'),

    #path('modify/<int:id>/<str:type>/', views.modify_traject, name='modify_traject'),
    #path('reserve/<int:id>/', views.reserve_traject, name='reserve_traject'),
    # Dans urls.py
    #path('reserve/researched/<int:researchedTraject_id>/', views.reserve_trajectResearched, name='reserve_trajectResearched'),
    
    
    path('manage_reservation/<int:reservation_id>/<str:action>/', views.manage_reservation, name='manage_reservation'),

    path('propose-help/<int:researched_id>/', views.propose_help, name='propose_help'),
    path('reservation/auto/<int:proposed_id>/<int:researched_id>/', views.auto_reserve, name='auto_reserve'),
    
    path('place-details/', views.place_details_view, name='place_details'),

]
